""" """
import logging
import os
import stat
from datetime import datetime, timedelta
from pathlib import Path
from ....config import settings

logger = logging.getLogger(__name__)


def del_cookies_file(file_path: str | Path) -> None:
    file = Path(str(file_path))
    if file.exists():
        try:
            file.unlink(missing_ok=True)
            logger.debug(f"<<green>> unlink: file:{file}")
        except Exception as e:
            logger.warning(f"<<red>> unlink: Exception:{e}")


def check_if_file_is_old(file):
    if file.exists():
        file_time = datetime.fromtimestamp(file.stat().st_mtime)

        if not file.stat().st_size:
            del_cookies_file(file)
        elif datetime.now() - file_time > timedelta(days=3):
            del_cookies_file(file)


def get_file_name(lang: str, family: str, username: str) -> Path:
    statgroup = stat.S_IRWXU | stat.S_IRWXG
    tool = os.getenv("HOME")
    if not tool:
        tool = Path(__file__).parent
    else:
        tool = Path(tool)
    cookies_dir = tool / "cookies"
    if not cookies_dir.exists():
        cookies_dir.mkdir(exist_ok=True, parents=True)

        logger.debug("<<green>> mkdir:")
        logger.debug(f"cookies_dir:{cookies_dir}")
        logger.debug("<<green>> mkdir:")

        try:
            os.chmod(cookies_dir, statgroup)
        except Exception as e:
            logger.warning(f"<<red>> chmod: Exception:{e}")

    if settings.bot.no_cookies:
        randome = os.urandom(8).hex()
        return cookies_dir / f"{randome}.txt"

    lang = lang.lower()
    family = family.lower()
    username = username.lower().replace(" ", "_").split("@")[0]
    file = cookies_dir / f"{family}_{lang}_{username}.txt"
    check_if_file_is_old(file)

    return file


__all__ = [
    "get_file_name",
    "del_cookies_file",
]
