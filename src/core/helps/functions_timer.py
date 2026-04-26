import functools
import logging
import time

logger = logging.getLogger(__name__)


def function_timer(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()

        result = func(*args, **kwargs)

        delta = time.perf_counter() - start_time

        logger.debug(f"{func.__name__} done in {delta:.4f} seconds")

        return result

    return wrapper
