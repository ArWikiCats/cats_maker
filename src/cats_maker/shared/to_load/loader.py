"""
Base json files loader.
"""

from __future__ import annotations

import json
import logging
import os
import stat
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

from ..newapi import AllAPIS

logger = logging.getLogger(__name__)
Dir = Path(__file__).parent.parent


def log_to_file(data: dict[str, Any] | list[Any], file: Path) -> None:

    statgroup = stat.S_IRWXU | stat.S_IRWXG

    file_path = str(file)

    should_delete = False

    try:
        file.parent.mkdir(exist_ok=True, mode=statgroup, parents=True)
    except Exception as e:
        logger.error(e)

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"<<green>> wrote to {file_path}")
    except PermissionError:
        logger.info(f"<<red>> PermissionError writing to {file_path}")
        should_delete = True
    except Exception as e:
        logger.error(e)

    if should_delete:
        try:
            os.remove(file_path)

            logger.debug(f"<<lightgreen>> deleted {file_path}")

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"<<green>> wrote to {file_path}")

            os.chmod(file_path, statgroup)
        except Exception:
            logger.exception("Exception:", exc_info=True)


class FilesBaseWorker(ABC):
    """
    Abstract base class for job workers with standardized lifecycle.

    This base class provides:
    - Standardized result structure initialization
    - Lifecycle management (start, run, finalize)
    - Exception handling at the worker level
    - Automatic job status updates
    - Result file generation and saving

    Subclasses must implement:
    - get_job_type(): Return the job type string
    - process_data(): Implement the actual processing logic

    Optional overrides:
    - before_run(): Called before processing starts
    - after_run(): Called after processing completes
    """

    def __init__(
        self,
        file: str,
        title: str,
        default_data: dict[str, Any] | None = None,
        ar_api: AllAPIS | None = None,
    ) -> None:
        self.ar_api = ar_api or AllAPIS.load_arwiki()

        self.file: Path = self.get_dir_path() / file
        self.title = title
        self.result: dict[str, Any] = {}
        self.save_new_data = False
        self.default_data = default_data or {}

    def get_dir_path(self) -> Path:
        data_path = os.getenv("JSON_DATA_PATH") or "data"
        return Path(data_path)

    def load_data_from_file(self) -> None | Any:
        if not self.file.exists():
            logger.debug(f"File not found: {self.file}")
            return None

        try:
            with open(str(self.file), encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.error("Error writing to file: %s", str(e))
            return None

        return data

    def is_data_good(self) -> bool:
        try:
            # Get the time of last modification
            last_modified_time = os.path.getmtime(str(self.file))

            date = datetime.fromtimestamp(last_modified_time).strftime("%Y-%m-%d")

            today = datetime.today().strftime("%Y-%m-%d")

            if date != today:
                logger.debug(f"<<purple>> last modified: {date} , today: {today}")
                return False
        except Exception as e:
            logger.error(f"Exception: {e}")
            return False

        return True

    @abstractmethod
    def load_new_data(self) -> dict[str, Any]:
        raise NotImplementedError

    def process_data(self) -> dict[str, Any]:
        """Execute the main processing logic.

        This method should contain the actual work of the job.
        It should check for cancellation via self.cancel_event periodically.

        Returns:
            The populated result WorkerObject
        """
        local_data = None
        if self.is_data_good():
            local_data = self.load_data_from_file()

        if os.getenv("APP_ENV") == "testing":
            return local_data or {}

        if not local_data:
            local_data = self.load_new_data()
            self.save_new_data = True

        return local_data

    def before_run(self) -> bool:
        """Called before processing starts.

        Returns:
            True to continue with processing, False to abort
        """
        return True

    def after_run(self) -> None:
        """
        Called after processing completes (success or failure).
        """
        # merge self.default_data with self.result
        if self.default_data and self.result:
            self.result.update(self.default_data)

        if self.save_new_data:
            log_to_file(self.result, self.file)

        logger.debug("Job %s Finished.", self.title)

    def load_text(self) -> str:
        page = self.ar_api.mainpage(self.title)
        text = page.get_text()
        return text or ""

    def handle_error(self, error: Exception) -> None:
        """
        Handle an error during processing.
        """
        logger.error(type(error).__name__)
        logger.error(str(error))

    def run(self) -> dict[str, Any]:
        """
        Execute the complete job lifecycle.
        """
        try:
            # Pre-processing setup
            if not self.before_run():
                return self.result

            # Main processing
            self.result = self.process_data()

        except Exception as e:
            self.handle_error(e)

        finally:
            # Post-processing cleanup
            self.after_run()

        return self.result


__all__ = [
    "FilesBaseWorker",
    "log_to_file",
]
