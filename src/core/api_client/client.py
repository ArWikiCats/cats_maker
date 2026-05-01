"""

Examples::

client = WikiLoginClient(
    lang="en",
    family="wikipedia",
    username="MyBot",
    password="s3cr3t",
)
# Simple read
data = client.client_request({"action": "query", "titles": "Python"})

# Write — POST with auto CSRF + retry handling
data = client.client_request(
    {
        "action": "edit",
        "title": "Sandbox",
        "text": "hello",
        "summary": "test",
    },
    method="post",
)
"""

from __future__ import annotations

import copy
import http.cookiejar
import logging
import time
from pathlib import Path
from typing import Any, Optional, Union

import mwclient
import mwclient.errors
import requests

from ...config import settings
from . import config
from .cookies import _delete_cookie_file, get_cookie_path
from .exceptions import CSRFError, LoginError, MaxlagError, WikiClientError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# RequestsHandler — طبقة النقل وإعادة المحاولة
# ---------------------------------------------------------------------------


class RequestsHandler:
    """
    تمتلك requests.Session وتُشغّل كل طلب HTTP عبر حلقة إعادة محاولة موحّدة تتعامل مع:

    - CSRF / bad token        → تحديث التوكن، حقنه من جديد، إعادة المحاولة
    - maxlag                  → انتظار تدريجي أسّي، إعادة المحاولة
    - assertnameduserfailed   → تفويض خطّاف إعادة تسجيل الدخول، إعادة المحاولة مرة واحدة
    """

    # ------------------------------------------------------------------
    # عقد يجب أن تُوفّره الكلاسات الفرعية
    # ------------------------------------------------------------------

    @property
    def _session(self) -> requests.Session:
        raise NotImplementedError

    def _refresh_csrf_token(self) -> str:
        raise NotImplementedError

    def _on_assertnameduserfailed(self) -> None:
        raise NotImplementedError

    # ------------------------------------------------------------------
    # تنفيذ الطلب الأساسي — النقطة الوحيدة التي تلمس الشبكة
    # ------------------------------------------------------------------

    def _execute_request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        files: Optional[Any] = None,
    ) -> requests.Response:
        return self._session.request(
            method,
            url,
            params=params,
            data=data,
            files=files,
        )

    # ------------------------------------------------------------------
    # حلقة إعادة المحاولة
    # ------------------------------------------------------------------

    def _request_with_retry(
        self,
        method: str,
        url: str,
        *,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        files: Optional[Any] = None,
        assertnameduser_retries: int = 1,
    ) -> dict:
        """
        نفّذ الطلب وأعد المحاولة تلقائياً عند أخطاء API العابرة.

        يعمل على نسخ من params/data حتى لا تتلوّث المعاملات الأصلية للمُستدعي.

        Raises:
            CSRFError:          بعد استنفاد محاولات التوكن.
            MaxlagError:        بعد استنفاد محاولات maxlag.
            WikiClientError:    عند assertnameduserfailed أو أخطاء API أخرى.
            requests.HTTPError: عند استجابات غير 2xx.
        """
        # نسخ دفاعي — لا نُلوّث قواميس المُستدعي عبر المحاولات
        working_params = dict(params) if params else {}
        working_data = dict(data) if data else {}

        attempt = 0
        named_user_attempts = 0

        while attempt < config.MAX_RETRIES:
            response = self._execute_request(
                method,
                url,
                params=working_params or None,
                data=working_data or None,
                files=files,
            )
            response.raise_for_status()

            # الاستجابات غير JSON تمرّ مباشرةً
            if "application/json" not in response.headers.get("Content-Type", ""):
                return {}

            try:
                body: dict = response.json()
            except ValueError:
                return {}

            error = body.get("error", {})
            if not error:
                return body  # ← المسار السعيد

            error_code: str = error.get("code", "")
            error_info: str = error.get("info", "")

            # ── CSRF ──────────────────────────────────────────────────────
            if self._is_csrf_error(error_code, error_info):
                attempt += 1
                if attempt >= config.MAX_RETRIES:
                    raise CSRFError(
                        f"CSRF token remained invalid after {config.MAX_RETRIES} "
                        f"attempts. Last error: {error_info or error_code}"
                    )
                working_data, working_params = self._handle_csrf(
                    error_code, error_info, attempt, working_data, working_params
                )
                continue

            # ── maxlag ────────────────────────────────────────────────────
            if error_code == "maxlag":
                attempt += 1
                if attempt >= config.MAX_RETRIES:
                    raise MaxlagError(
                        f"Server maxlag not resolved after {config.MAX_RETRIES} attempts."
                    )
                self._handle_maxlag(response, attempt)
                continue

            # ── assertnameduserfailed ─────────────────────────────────────
            if error_code == "assertnameduserfailed":
                if named_user_attempts >= assertnameduser_retries:
                    raise WikiClientError(
                        "assertnameduserfailed persists after re-login"
                    )
                named_user_attempts += 1
                logger.warning(
                    "assertnameduserfailed — attempting recovery (try %d/%d)",
                    named_user_attempts,
                    assertnameduser_retries,
                )
                self._on_assertnameduserfailed()
                attempt = 0  # نُعيد ميزانية CSRF/maxlag من الصفر بعد إعادة الدخول
                continue

            # ── أي خطأ آخر — نرفعه للمُستدعي ────────────────────────────
            raise WikiClientError(f"API error {error_code}: {error_info}")

        raise MaxlagError(
            f"Exceeded {config.MAX_RETRIES} retries without a successful response."
        )

    # ------------------------------------------------------------------
    # مساعدات CSRF
    # ------------------------------------------------------------------

    @staticmethod
    def _is_csrf_error(code: str, info: str) -> bool:
        return code in ("badtoken", "notoken") or info == "Invalid CSRF token."

    def _handle_csrf(
        self,
        error_code: str,
        error_info: str,
        attempt: int,
        data: dict,
        params: dict,
    ) -> tuple[dict, dict]:
        """حدّث التوكن واحقنه في القاموس الصحيح. يُعيد (data, params) جديدتين."""
        logger.debug(
            "CSRF error (%s) — refreshing token (attempt %d/%d)",
            error_code or error_info,
            attempt,
            config.MAX_RETRIES,
        )
        try:
            new_token = self._refresh_csrf_token()
        except Exception as exc:
            raise CSRFError(f"Failed to refresh CSRF token: {exc}") from exc

        return self._inject_token(new_token, data, params)

    @staticmethod
    def _inject_token(token: str, data: dict, params: dict) -> tuple[dict, dict]:
        """أعِد نسختين مُحدَّثتين من (data, params) مع التوكن الجديد."""
        for bucket_name, bucket in (("data", data), ("params", params)):
            if "token" in bucket:
                bucket = dict(bucket)
                bucket["token"] = token
                logger.debug("Injected new CSRF token into %s", bucket_name)
                if bucket_name == "data":
                    return bucket, params
                return data, bucket
        return data, params

    # ------------------------------------------------------------------
    # مساعد maxlag
    # ------------------------------------------------------------------

    def _handle_maxlag(self, response: requests.Response, attempt: int) -> None:
        """نم للمدة التي طلبها السيرفر أو استخدم الانتظار الأسّي."""
        retry_after = response.headers.get(config.MAXLAG_HEADER)
        try:
            delay = float(retry_after) if retry_after is not None else None
        except ValueError:
            delay = None

        if delay is None:
            delay = config.BACKOFF_BASE * (2 ** attempt)

        logger.debug(
            "maxlag — sleeping %.1f s (attempt %d/%d)",
            delay,
            attempt,
            config.MAX_RETRIES,
        )
        time.sleep(delay)


# ---------------------------------------------------------------------------
# CookiesClient — إدارة الكوكيز
# ---------------------------------------------------------------------------


class CookiesClient:
    """مساعدات ساكنة لتحميل وحفظ LWP cookie jars."""

    @staticmethod
    def save_cookies(cj: http.cookiejar.LWPCookieJar) -> None:
        """احفظ الكوكيز على القرص فوراً."""
        try:
            cj.save(ignore_discard=True, ignore_expires=True)
            logger.debug("Cookies saved to _cookie_path")
        except Exception:
            logger.exception("Failed to save cookies")

    @staticmethod
    def _make_cookiejar(cookie_path: Path) -> http.cookiejar.LWPCookieJar:
        cj = http.cookiejar.LWPCookieJar(cookie_path)
        if cookie_path.exists():
            try:
                cj.load(ignore_discard=True, ignore_expires=True)
            except Exception as exc:
                logger.error("Error loading cookies: %s", exc)
        return cj


# ---------------------------------------------------------------------------
# WikiLoginClient — طبقة الأعمال
# ---------------------------------------------------------------------------


class WikiLoginClient(CookiesClient, RequestsHandler):
    """
    غلاف رفيع حول mwclient.Site يوفّر:

    - استمرارية الجلسة عبر تشغيلات متعددة باستخدام Mozilla cookie jar.
    - تخطّي تسجيل الدخول عند وجود كوكيز صالحة.
    - إعادة المحاولة تلقائياً عند أخطاء CSRF ومشاكل maxlag.
    - الاسترداد التلقائي عند انتهاء الجلسة (assertnameduserfailed).
    - حقن bot=1 و assertuser في طلبات الكتابة.

    RequestsHandler تتولى طبقة النقل/إعادة المحاولة؛
    هذه الكلاس تختص بالمصادقة وإثراء المعاملات والتصفّح المتواصل.
    """

    _WRITE_ACTIONS: frozenset[str] = frozenset(
        {
            "edit", "create", "upload", "delete", "move",
            "wbeditentity", "wbsetclaim", "wbcreateclaim",
            "wbsetreference", "wbremovereferences", "wbsetaliases",
            "wbsetdescription", "wbsetlabel", "wbsetsitelink",
            "wbmergeitems", "wbcreateredirect",
        }
    )

    def __init__(
        self,
        lang: str,
        family: str,
        username: str,
        password: str,
        cookies_dir: str = settings.paths.cookies_dir,
    ) -> None:
        """
        هيّئ الكلاينت، حمّل الكوكيز المحفوظة، وتحقق من المصادقة.

        Args:
            lang:        رمز اللغة، مثل "en"، "ar".
            family:      عائلة الموقع، مثل "wikipedia"، "wikidata".
            username:    اسم حساب البوت أو المستخدم.
            password:    كلمة المرور أو bot password.
            cookies_dir: مجلد ملفات الكوكيز. الافتراضي: settings.paths.cookies_dir.
        """
        self.lang = lang
        self.family = family
        self.username = username
        self._password = password  # خاص — لا يُسجَّل أبداً

        self._cookie_path: Path = get_cookie_path(cookies_dir, family, lang, username)

        logger.debug("Creating mwclient.Site for %s.%s", lang, family)
        self.api_url = f"https://{self.lang}.{self.family}.org/w/api.php"

        try:
            self._site = mwclient.Site(f"{self.lang}.{self.family}.org")
        except mwclient.errors.InvalidSiteIdError:
            raise WikiClientError(f"Invalid site ID: {self.lang}.{self.family}")

        # ربط الكوكيز المحفوظة بالجلسة
        self.cj = self._make_cookiejar(self._cookie_path)
        self._site.connection.cookies = self.cj

        # التحقق من المصادقة — RequestsHandler يتولى الطبقة التحتية
        self._ensure_logged_in()

    # ------------------------------------------------------------------
    # تنفيذ عقد RequestsHandler
    # ------------------------------------------------------------------

    @property
    def _session(self) -> requests.Session:
        """جلسة mwclient الداخلية."""
        return self._site.connection

    def _refresh_csrf_token(self) -> str:
        """اطلب توكن CSRF جديداً من السيرفر."""
        return self._site.get_token("csrf", force=True)

    def _on_assertnameduserfailed(self) -> None:
        """
        انتهت الجلسة في منتصف التشغيل:
        احذف الكوكيز القديمة وأعد تسجيل الدخول.
        """
        logger.warning(
            "assertnameduserfailed for %s on %s.%s — clearing cookies and re-logging in",
            self.username, self.lang, self.family,
        )
        _delete_cookie_file(self._cookie_path, reason="assertnameduserfailed")
        self._do_login()

    # ------------------------------------------------------------------
    # الواجهة العامة
    # ------------------------------------------------------------------

    @property
    def site(self) -> mwclient.Site:
        """mwclient.Site الأساسي — استخدمه للوصول رفيع المستوى."""
        return self._site

    def login(self) -> None:
        """
        أجبر على تسجيل دخول جديد بغض النظر عن حالة الكوكيز.

        استدعِ هذا إذا علمت أن الجلسة انتهت وتريد إعادة المصادقة
        دون إنشاء WikiLoginClient جديد.
        """
        if not self._site.logged_in:
            logger.info(
                "Forcing re-login for %s on %s.%s",
                self.username, self.lang, self.family,
            )
            self._do_login()

    def client_request(
        self,
        params: dict,
        method: str = "post",
        files: Optional[Any] = None,
    ) -> dict:
        """
        أرسل طلب GET أو POST إلى wiki API وأعِد JSON المُحلَّل.

        معالجة CSRF وmaxlag وassertnameduserfailed تتم تلقائياً
        عبر RequestsHandler دون أي تدخل من المُستدعي.

        Args:
            params: معاملات MediaWiki API. format يُضبط على "json" افتراضياً.
            method: "get" أو "post" (غير حساس للحالة). الملفات تُجبر POST.
            files:  {field_name: file-like} للرفع متعدد الأجزاء.

        Returns:
            قاموس JSON للاستجابة.

        Raises:
            ValueError:         عند method غير صالح.
            CSRFError:          بعد استنفاد محاولات التوكن.
            MaxlagError:        بعد استنفاد محاولات maxlag.
            WikiClientError:    عند أخطاء API الأخرى.
            requests.HTTPError: عند استجابات غير 2xx.
        """
        method = method.lower()
        if method not in ("get", "post"):
            raise ValueError(f"method must be 'get' or 'post', got {method!r}")

        if files is not None:
            method = "post"

        # ضمان JSON وحقن معاملات الأمان
        params = self._enrich_params({"format": "json", **params})

        logger.debug(
            "%s %s params=%s files=%s",
            method.upper(),
            self.api_url,
            {k: ("***" if k == "token" else v) for k, v in params.items()},
            list(files.keys()) if files else None,
        )

        if method == "get":
            return self._request_with_retry(
                "GET",
                self.api_url,
                params=params,
            )
        else:
            # دائماً نجلب توكن جديداً لطلبات POST — حلقة الإعادة ستُجدّده عند الحاجة
            params["token"] = self._site.get_token("csrf")
            return self._request_with_retry(
                "POST",
                self.api_url,
                data=params,
                files=files,
            )

    def post_continue(
        self,
        params: dict,
        action: str,
        _p_: str = "pages",
        p_empty: Optional[Union[list, dict]] = None,
        Max: int = 500_000,
        first: bool = False,
        _p_2: str = "",
        _p_2_empty: Optional[Union[list, dict]] = None,
    ) -> Union[list, dict]:
        """
        أدِر استعلام continuation في MediaWiki API حتى اكتماله.

        يُكرّر على رمز continue حتى جلب كل الصفحات أو بلوغ Max نتيجة.

        Args:
            params:      معاملات API الأساسية.
            action:      المفتاح الرئيسي في JSON لاستخراج النتائج (مثل "query").
            _p_:         المفتاح الفرعي داخل action (افتراضي "pages").
            p_empty:     القيمة الابتدائية للمجمّع (list أو dict).
            Max:         توقف بعد هذا العدد من النتائج.
            first:       أعِد العنصر الأول فقط من القائمة.
            _p_2:        مفتاح فرعي ثانوي عند first=True.
            _p_2_empty:  قيمة ابتدائية للمجمّع الثانوي.

        Returns:
            النتائج المجمّعة كـ list أو dict حسب p_empty.
        """
        logger.debug("post_continue start. action=%s _p_=%s", action, _p_)

        if isinstance(Max, str) and Max.isdigit():
            Max = int(Max)
        if Max == 0:
            Max = 500_000

        p_empty = p_empty if p_empty is not None else []
        _p_2_empty = _p_2_empty if _p_2_empty is not None else []

        results = p_empty
        continue_params: dict = {}
        iterations = 0

        while continue_params or iterations == 0:
            page_params = copy.deepcopy(params)
            iterations += 1

            if continue_params:
                logger.debug("Applying continue_params: %s", continue_params)
                page_params.update(continue_params)

            body = self.client_request(page_params)

            if not body:
                logger.debug("post_continue: empty response, stopping")
                break

            continue_params = {}

            if action == "wbsearchentities":
                data = body.get("search", [])
            else:
                continue_params = body.get("continue", {})
                data = body.get(action, {}).get(_p_, p_empty)

                if _p_ == "querypage":
                    data = data.get("results", [])
                elif first:
                    if isinstance(data, list) and data:
                        data = data[0]
                        if _p_2:
                            data = data.get(_p_2, _p_2_empty)

            if not data:
                logger.debug("post_continue: no data in response, stopping")
                break

            logger.debug(
                "post_continue: +%d items (total %d)", len(data), len(results)
            )

            if Max <= len(results) > 1:
                logger.debug("post_continue: Max=%d reached, stopping", Max)
                break

            if isinstance(results, list):
                results.extend(data)
            else:
                results = {**results, **data}

        logger.debug("post_continue: done, %d total results", len(results))
        return results

    # ------------------------------------------------------------------
    # المساعدات الخاصة
    # ------------------------------------------------------------------

    def _ensure_logged_in(self) -> None:
        """تحقق من المصادقة؛ حاول إحياء الجلسة عبر الكوكيز أولاً."""
        if self._site.logged_in:
            logger.info(
                "Session already authenticated (logged_in=%s)", self._site.logged_in
            )
            return
        if self._cookie_path.exists():
            try:
                self._site.site_init()
                if self._site.logged_in:
                    logger.info(
                        "Revived session via cookies as %s", self._site.username
                    )
                    return
            except Exception as exc:
                logger.error("site_init failed: %s", exc)

        # لا نُسجّل الدخول تلقائياً — المُستدعي يستدعي login() عند الحاجة

    def _enrich_params(self, params: dict) -> dict:
        """
        حقن معاملات أمان طلبات الكتابة.

        لطلبات الكتابة:
          - bot=1        يُعلّم التعديلات كبوت في سجل التغييرات.
          - assertuser   يُرفض الطلب إذا لم يتطابق المستخدم مع الجلسة.

        طلبات القراءة (query) تُنظَّف من المفاتيح الخاصة بالكتابة.
        """
        params = dict(params)
        action = params.get("action", "")

        if action == "query":
            params.pop("bot", None)
            params.pop("summary", None)
            return params

        is_write = (
            action in self._WRITE_ACTIONS
            or action.startswith("wb")
            or self.family == "wikidata"
        )
        if is_write and self.username:
            params.setdefault("bot", 1)
            params.setdefault("assertuser", self.username)

        return params

    def _do_login(self) -> None:
        """
        نفّذ مصافحة تسجيل الدخول عبر mwclient واحفظ الكوكيز الناتجة.

        Raises:
            LoginError: إذا رفض mwclient بيانات الاعتماد.
        """
        try:
            self._site.login(self.username, self._password)
        except mwclient.errors.LoginError as exc:
            raise LoginError(
                f"Login failed for {self.username} on {self.lang}.{self.family}: {exc}"
            ) from exc

        if self._site.logged_in:
            logger.info(
                "Logged in successfully as %s on %s.%s",
                self.username, self.lang, self.family,
            )
            self.save_cookies(self.cj)

    def __repr__(self) -> str:
        return (
            f"WikiLoginClient(lang={self.lang!r}, family={self.family!r}, "
            f"username={self.username!r})"
        )


__all__ = [
    "RequestsHandler",
    "WikiLoginClient",
]
