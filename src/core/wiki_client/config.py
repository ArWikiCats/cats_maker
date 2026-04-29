# wiki_client/config.py
# All tuneable constants. No logic lives here.

MAX_RETRIES: int = 5
BACKOFF_BASE: int = 1  # seconds; delay = BACKOFF_BASE * 2 ** attempt
MAXLAG_HEADER: str = "Retry-After"
COOKIES_DIR: str = "cookies"

# mwclient Site() script path
DEFAULT_PATH: str = "/w/"
