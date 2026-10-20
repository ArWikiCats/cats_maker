# تقرير: المقارنة بين `ApiError` و `ApiResultError`

> **النطاق:** `src/arwikibot/shared/newapi/core/` > **الجمهور المستهدف:** المطورون العاملون على `newapi` (غلاف pywikibot المستخدَم في بوتات arwiki).

## الملخص السريع (TL;DR)

| الجانب              | `ApiError`                                                                       | `ApiResultError`                                                               |
| ------------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| **النوع**           | **استثناء في بايثون** (`Python Exception`) يتم رفعه (`raised`)                   | **كائن بيانات** (`@dataclass`) يُحمل داخل البيانات ولا يُرفع أبداً             |
| **مكان التعريف**    | `core/exceptions.py` (ضمن شجرة `NewApiExceptionError`)                           | `core/result_error.py`                                                         |
| **الدور**           | التمثيل _المرفوع_ **لخطأ في منطق عمل ميدياويكي (Business Error)**                | حمولة الخطأ الموحدة (_normalized error payload_) المخزنة داخل `ApiResult` فاشل |
| **أماكن الاستخدام** | `parse_api_error()`، `to_api_result()`، وطبقات النقل وإعادة المحاولة             | `ApiResult.fail()`، `unwrap()`، `to_dict()`، `from_anything()`                 |
| **الحقول الرئيسية** | `code`, `message`, `info`, `is_retryable`, `raw_error` (+ إضافات الفئات الفرعية) | `code`, `message`, `details`                                                   |
| **العلاقة**         | يتم **تحويله إلى** `ApiResultError` عند تغليفه داخل `ApiResult`                  | هو **النتيجة الناتجة عن** عملية التحويل تلك                                    |

**في جملة واحدة:** `ApiError` هو _الاستثناء_ الذي يُمثِّل خطأ واجهة API في ميدياويكي؛ بينما `ApiResultError` هو _القيمة_ التي يتحول إليها نفس هذا الخطأ عندما يتم إرجاعه كـ نتيجة العودة المعتادة (دون رفع استثناءات).

---

## 1. أين يقع كلاً منهما؟

### `ApiError` — شجرة الاستثناءات (`core/exceptions.py`)

```python
class NewApiExceptionError(Exception): ...


class ApiError(NewApiExceptionError):
    def __init__(self, code, message, info="", is_retryable=False, raw_error=None): ...
```

يمتلك `ApiError` العديد من الفئات الفرعية المخصصة لأخطاء منطق العمل، وتكون كل فئة مرتبطة برمز خطأ خاص بميدياويكي (`code`):

-   `AbuseFilterError` (`abusefilter-disallowed` - يضيف `filter_id` و `description` و `is_delay()`)
-   `MaxLagError` (`maxlag` - يضيف `lag` وقابل لإعادة المحاولة)
-   `ArticleExistsError` (`articleexists`)
-   `NoSuchEntityError` (`no-such-entity`)
-   `ProtectedPageError` (`protectedpage`)
-   `InvalidTokenError` (`badtoken` - قابل لإعادة المحاولة)

توجد أيضاً شجرة **منفصلة** باسم `WikiClientError` (تتضمن `LoginError` و `CSRFError` و `MaxlagError` و `MaxRetriesExceededError` و `CookieError`) مخصصة لأخطاء **طبقة النقل (Transport)** — وهذه الأخطاء _ليست_ من نوع `ApiError` وتظل مرفوعة دائماً عن عمد.

### `ApiResultError` — كائن القيمة (`core/result_error.py`)

```python
@dataclass(slots=True)
class ApiResultError:
    code: str
    message: str
    details: Any | None = None
```

إن `ApiResultError` **ليس** استثناءً (`Exception`). بل هو مجرد كائن قيمة بسيط يُحمل بواسطة `ApiResult.error` (انظر `core/result.py`). أما الكائن المجاور له `ApiResultExceptionError(Exception)` فهو استثناء بالفعل، لكنه يُرفع فقط بواسطة `ApiResult.unwrap()` — وهو يقوم _بتغليف_ `ApiResultError` وليس جزءاً منه.

---

## 2. الفارق المفاهيمي

-   **`ApiError` مخصص للتحكم بمسار التنفيذ (raise/catch):** يمثل مشكلة حدثت _عند حدود API_ وتم التعبير عنها كـ استثناء ليتمكن المستدعي من التفرع بناءً عليها (`except ArticleExistsError:`).
-   **`ApiResultError` مخصص لتدفق البيانات (return value):** يمثل الشكل الموحد والدائم للخطأ داخل غلاف `ApiResult` (`ApiResult.fail(...)`). تم تصميمه ليكون قابلاً للتسلسل (`to_dict()`) والاستهلاك من قبل أي مستدعي (CLI، أداة Toolforge، سكريبت خلفي، API خارجي، أو اختبارات) دون إجبارهم على التعامل مع الاستثناءات عبر `catch`.

ترسم سياسة التعامل مع الأخطاء بالمشروع (الموثقة في أعلى ملف `exceptions.py`) هذا الحد الفاصل:

-   **نتائج منطق العمل المتوقعة (Expected business outcomes)** → تتحول إلى `ApiResult.fail` (أي كائن `ApiResultError`). أمثلة: `page_not_found`، `invalid_summary`، `permission_denied`، `articleexists`. تُعتبر هذه نتائج _طبيعية_ وليست انهياراً للنظام.
-   **إخفاقات النقل / الشبكة / المصادقة** (`WikiClientError`) → **تظل مرفوعة كـ استثناءات**. ففشل الشبكة مثل `requests.Timeout` أو خطأ `CSRFError` المستمر هو فشل حقيقي يجب على المستدعي التعامل معه بشكل صريح، وليس نتيجة يتم التغاضي عنها.

وبذلك، فإن `ApiError` (منطق العمل) و `ApiResultError` (القيمة) هما وجهان لنفس مفهوم خطأ العمل، لكن يتم التعبير عنهما في مستويين مختلفين.

---

## 3. مقارنة الحقول

### `ApiError` (أغنى، موجه للاستثناءات)

```
code          str   مثال: "articleexists"
message       str   نص موجه للبشر (من NewApiExceptionError.message)
info          str   معلومات إضافية من الـ API
is_retryable  bool  هل العملية قابلة لإعادة المحاولة؟
raw_error     dict  قاموس الخطأ الأصلي القادم من الـ API
+ إضافات الفئات الفرعية: lag, filter_id, description, field ...

```

### `ApiResultError` (مبسط، موجه للتسلسل/Serialization)

```
code     str
message  str
details  Any | None   (عادة ما يكون dict، ولكنه قد يكون قائمة بأخطاء التحقق)

```

يتجاهل `ApiResultError` عن قصد حقول `info` و `is_retryable` و `raw_error` — محتفظاً فقط بما هو مطلوب لتوفير غلاف مستقر وقابل للتسلسل.

---

## 4. دورة الحياة: كيف يتحولان إلى بعضهما البعض؟

### من قاموس MediaWiki إلى `ApiError`: عبر `parse_api_error(error_dict)`

يقوم الدالة `exceptions.py::parse_api_error` بتحويل قاموس خطأ الـ API إلى _الفئة الفرعية المناسبة لـ `ApiError_`بناءً على الـ`code`:

```python
if err_code == "articleexists": return ArticleExistsError(message=err_info, raw_error=error_dict)
if err_code == "maxlag":        return MaxLagError(lag=..., message=err_info, ...)
...
return ApiError(code=err_code, message=err_info, ...)   # خيار احتياطي عام

```

هذا هو اتجاه "خطأ الـ API ← استثناء". يُستخدم في `client_wiki/pages/super_page.py` (في عمليات `save` و `create`).

### من `ApiError` إلى `ApiResultError`: عبر `ApiResult.fail()` / `to_api_result()`

يوجد مساران لذلك:

1. **`ApiResult.fail(code=..., error=...)`** والتي تقوم باستدعاء `ApiResultError.from_anything(code, error)`.
2. **`exceptions.py::to_api_result(exc)`** والتي تقوم بـ `ApiResult.fail(code=exc.code, error=exc.message)` — لاحظ أنها تمرر `exc.message` وتتجاهل `info`/`is_retryable`/`raw_error`.

تتعامل الدالة `from_anything` مع أربعة أشكال للمُدخلات:

| عندما يكون `error`…                         | النتيجة                                                                                   |
| ------------------------------------------- | ----------------------------------------------------------------------------------------- |
| كائن `ApiResultError` بالفعل                | يتم إرجاعه كما هو                                                                         |
| استثناء `Exception` (بما في ذلك `ApiError`) | `ApiResultError(code=code or type(error).__name__, message=str(error))`                   |
| قاموس `dict`                                | يتعامل بمرونة مع المفاتيح القديمة (`message`/`error`/`info`)؛ وما تبقى يذهب إلى `details` |
| أي شيء آخر (`str`, `None`)                  | `code or "UNKNOWN_ERROR"`, والملاحظة تكون `str(error)`                                    |

---

## 5. عدم التطابق الفعلي في الكود (مكمن الخلل في `super_page.py`)

في ملف `client_wiki/pages/super_page.py` (في الدالتين `save`/`create`)، يقوم الكود بـ:

```python
# ملاحظة: تعيد parse_api_error كائن ApiError بينما يتوقع fail.error كائن ApiResultError
error = parse_api_error(error_dict=error_dict)
return ApiResult.fail(error=error)
```

نظراً لأن `ApiError` عبارة عن استثناء (`Exception`)، فإن `from_anything` تدخل فرع **`isinstance(error, Exception)`** وتقوم بتغليفه بالشكل التالي:

```python
ApiResultError(code=code or type(error).__name__, message=str(error))
```

ولأن `ApiResult.fail(error=error)` تم استدعاؤها **بدون** التمرير الصريح لـ `code` (حيث يكون `code` قيمته `None`)، فإن قيمة `ApiResultError.code` الناتجة تصبح **اسم الفئة البرمجية** (`"ArticleExistsError"`)، بينما تصبح الرسالة `"articleexists: already exists"` (وهي القيمة الناتجة عن `__str__` للابستثناء). وبالتالي **تضيع** الحقول المهيكلة `code` و `info` و `is_retryable` و `raw_error` بالكامل.

السلوك الذي تم تحققه عملياً:

```python
ae = parse_api_error({"code": "articleexists", "info": "already exists"})
r = ApiResult.fail(error=ae)
r.error.code  # -> 'ArticleExistsError'   (خاطئ: كان ينبغي أن يكون 'articleexists')
r.error.message  # -> 'articleexists: already exists'
r.to_dict()  # -> {'success': False, 'data': None,
#     'error': {'code': 'ArticleExistsError', 'message': 'articleexists: already exists', 'details': None}}
```

في المقابل، فإن تمرير الرمز بشكل صريح يحافظ عليه:

```python
r2 = ApiResult.fail(code="articleexists", error=ae)
r2.error.code  # -> 'articleexists'
```

الجدير بالذكر أن الدالة `exceptions.py::to_api_result()` تقوم بالشيء الصحيح بالفعل (`code=exc.code, error=exc.message`)، لذا فإن هذا التضارب يقتصر بشكل خاص على مكان الاستدعاء في `super_page.py`.

### التوصيات والإصلاح

إما:

-   **(أ)** تمرير الرمز بشكل صريح عند موقع الاستدعاء:
    `return ApiResult.fail(code=error.code, error=error.message)` — محاكاةً لما تفعله `to_api_result()`.
-   **(ب)** تحديث `ApiResultError.from_anything` للتعرف على `ApiError` (حيث تحتوي بالفعل على تعليق `# TODO: what about ApiError ?`) وتحويل `code`/`info`/`is_retryable`/`raw_error` إلى `code`/`message`/`details` دون فقدان أي حقول.

الخيار **(ب)** هو الأكثر متانة لأنه يعالج الخلل في جميع عمليات التحويل من `ApiError` إلى `ApiResultError` في مكان واحد.

---

## 6. أيّهما تختار ومتى؟

-   **عند تمثيل خطأ منطق عمل من ميدياويكي تريد _رفعه_ أو التفرع بناءً عليه:** استخدم / أنشئ فئة فرعية من `ApiError` (ودع `parse_api_error` تتولى بناءه).
-   **عند إرجاع فشل من دالة على مستوى الخدمة (Service-level function):** قم بإرجاع `ApiResult.fail(...)` والتي تنتج بدورها كائن `ApiResultError` داخلياً. **لا تقم** برفع `ApiResultError` إطلاقاً (فهو ليس استثناءً).
-   **عند الحاجة لإجبار المستدعي على التعامل مع الفشل كـ استثناء:** استخدم `result.unwrap()` والتي ترفع `ApiResultExceptionError` (والذي يحمل داخله `ApiResultError`).
-   **تجنب تماماً** إرجاع أخطاء طبقة النقل من نوع `WikiClientError` كـ `ApiResult` — فهذه الأخطاء يجب أن تظل مرفوعة كـ استثناءات وفقاً لسياسة المشروع.

---

## 7. مخطط مرجعي سريع لمسار التحويل

```
API error dict (قاموس خطأ الـ API)
   │  parse_api_error()
   ▼
ApiError  (استثناء غني بالبيانات: code/info/is_retryable/raw_error)
   │  ApiResult.fail(code=..., error=...)  أو  to_api_result()
   ▼
ApiResultError  (كائن قيمة مبسط: code/message/details)  ──► ApiResult.error
   │  ApiResult.unwrap() عند الفشل
   ▼
ApiResultExceptionError  (استثناء يقوم بتغليف ApiResultError)

```

---

## ملحق: خريطة الملفات

| الملف                             | المسؤولية                                                                                       |
| --------------------------------- | ----------------------------------------------------------------------------------------------- |
| `core/exceptions.py`              | شجرة `ApiError`، شجرة `WikiClientError`، ودوال `parse_api_error` و `to_api_result`              |
| `core/result_error.py`            | كائن البيانات `ApiResultError` + دالة `from_anything` واستثناء `ApiResultExceptionError`        |
| `core/result.py`                  | غلاف `ApiResult`؛ حيث تستخدم الدالة `fail()` المعالج `ApiResultError.from_anything`             |
| `core/handel_errors.py`           | `HandleErrors.parse_api_error` — مسار _قديم_ يعيد `ApiResult.fail` مباشرة (ولا يبني `ApiError`) |
| `client_wiki/pages/super_page.py` | يستخدم `parse_api_error` ثم `ApiResult.fail(error=...)` (موقع عدم التطابق)                      |
