"""log message"""

import json
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Optional

import numpy as np

from molmidial.project import __project__

NOW = datetime.now()
DATE_STRING = NOW.strftime("%d%b%Y")
TIME_STRING = NOW.strftime("%H-%M")

LOG_PADDING_WIDTH = 40

LOGGING = True


def setup_logging():
    """Set up logging configuration"""
    try:
        # Create logs shader_directory in user's home shader_directory
        _ = logging.getLogger(__project__)
        log_dir = Path.home() / f".{__project__}" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        # Log file path
        log_file = log_dir / f"{__project__}-{DATE_STRING}-{TIME_STRING}.log"

        # Reset root handlers
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # Configure rotating file logging
        file_handler = RotatingFileHandler(
            str(log_file),
            maxBytes=1024 * 1024,  # 1MB per file
            backupCount=5,  # Keep 5 backup files
            encoding="utf-8",
        )
        file_handler.setLevel(logging.CRITICAL)
        file_formatter = logging.Formatter(
            "%(filename)-20s| %(lineno)-5s| %(levelname)-8s| %(message)-24s"
        )
        file_handler.setFormatter(file_formatter)

        # Configure console logging
        console_handler = logging.StreamHandler(
            sys.__stdout__
        )  # Use sys.__stdout__ explicitly
        console_handler.setLevel(logging.CRITICAL)
        console_formatter = logging.Formatter(
            "%(filename)-20s| %(lineno)-5s| %(levelname)-8s| %(message)-24s"
        )
        console_handler.setFormatter(console_formatter)

        # Configure root logger
        logging.root.setLevel(logging.CRITICAL)
        logging.root.addHandler(file_handler)
        logging.root.addHandler(console_handler)

        logger = logging.getLogger(__project__)
        logger.info(f"{__project__} starting up with log file {log_file}...")
        logging.getLogger("OpenGL").setLevel(logging.WARNING)

        # Restore saved log level from preferences
        _restore_log_level_from_settings()

        return logger

    except Exception as ex:
        print(f"Error setting up logging: {str(ex)}")
        raise


def _restore_log_level_from_settings():
    """Restore log level from saved preferences at startup."""
    try:
        from PySide6.QtCore import QSettings

        # Load saved log level from settings
        settings = QSettings("elmo", "preferences")
        saved_level = settings.value("log_level", None, type=str)

        if saved_level:
            # Apply the saved log level using the same comprehensive method
            _apply_log_level_comprehensive(saved_level)
            print(f"🔧 Restored log level from preferences: {saved_level}")
        else:
            print("🔧 No saved log level found, using default CRITICAL level")

    except Exception as ex:
        print(f"⚠️ Could not restore log level from settings: {ex}")


def _apply_log_level_comprehensive(level_name: str):
    """Apply the specified log level to all loggers and handlers (comprehensive version)."""
    try:
        numeric_level = getattr(logging, level_name.upper(), logging.CRITICAL)

        # Set root logger level
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)

        # Set all handler levels to match
        for handler in root_logger.handlers:
            handler.setLevel(numeric_level)

        # Set ALL existing loggers to the new level
        for logger_name in logging.Logger.manager.loggerDict:
            logger = logging.getLogger(logger_name)
            logger.setLevel(numeric_level)

        # Set project-specific logger level
        project_logger = logging.getLogger(__project__)
        project_logger.setLevel(numeric_level)

        # Set OpenGL logger level
        opengl_logger = logging.getLogger("OpenGL")
        opengl_logger.setLevel(numeric_level)

    except Exception as ex:
        print(f"⚠️ Error applying log level {level_name}: {ex}")


LEVEL_EMOJIS = {
    logging.DEBUG: "🔍",
    logging.INFO: "ℹ️",
    logging.WARNING: "⚠️",
    logging.ERROR: "❌",
    logging.CRITICAL: "💥",
}


def get_qc_tag(msg: str) -> str:
    """
    get QC emoji etc
    :param msg: str
    :return: str
    """
    msg = f"{msg}".lower()
    if "success rate" in msg:
        return "📊"
    if (
        "updat" in msg
        or "success" in msg
        or "passed" in msg
        or "Enabl" in msg
        or "Setting up" in msg
    ):
        return "✅"
    if "fail" in msg or "error" in msg:
        return "❌"
    return " "


def decorate_log_message(message: str, level: int) -> str:
    """
    Adds emoji decoration to a log message based on its content and log level.
    :param message: The original log message
    :param level: The logging level
    :return: Decorated log message string
    """

    level_emoji_tag = LEVEL_EMOJIS.get(level, "🔔")
    qc_tag = get_qc_tag(message)
    return f"{level_emoji_tag}{qc_tag}{message}"


class Logger:
    def __init__(self):
        pass

    @staticmethod
    def error(
        message: str,
        exception: Optional[Exception] = None,
        level: int = logging.ERROR,
        stacklevel: int = 4,
        silent: bool = False,
    ) -> None:
        """
        Log an error message, optionally with an exception.
        """
        if exception:
            message = f"{message}: {exception}"
        Logger.message(message, stacklevel=stacklevel, silent=silent, level=level)

    exception = error

    @staticmethod
    def warning(
        message: str,
        exception: Optional[Exception] = None,
        level: int = logging.WARNING,
        stacklevel: int = 4,
        silent: bool = False,
    ) -> None:
        """
        Log an error message, optionally with an exception.
        """
        if exception:
            message = f"{message}: {exception}"
        Logger.message(message, stacklevel=stacklevel, silent=silent, level=level)

    @staticmethod
    def json(data: Any, silent: bool = False) -> None:
        """
        Log a JSON object or JSON string as a single compact line.
        """
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                Logger.message(
                    "Invalid JSON string provided.", level=logging.WARNING, stacklevel=3
                )
                return

        try:
            compact_json = json.dumps(data, separators=(",", ":"))
        except (TypeError, ValueError) as e:
            Logger.error("Failed to serialize JSON", e)
            return

        if not silent:
            Logger.message(compact_json, stacklevel=3)

    @staticmethod
    def message(
        message: str,
        level: int = logging.INFO,
        stacklevel: int = 3,
        silent: bool = False,
    ) -> None:
        """
        Log a plain message with optional formatting.
        """
        full_message = decorate_log_message(message, level)
        if LOGGING and not silent:
            # Use the project logger instead of logging.log() to respect level settings
            logger = logging.getLogger(__project__)
            logger.log(level, full_message, stacklevel=stacklevel)

    debug = message
    info = message

    @staticmethod
    def parameter(
        message: str,
        parameter: Any,
        float_precision: int = 2,
        max_length: int = 300,
        level: int = logging.INFO,
        stacklevel: int = 4,
        silent: bool = False,
    ) -> None:
        """
        Log a structured message including type and a summarized value of a parameter.
        Fast for large collections, arrays, enums, and dicts.
        """

        def format_value(param: Any) -> str:
            if param is None:
                return "None"

            # Handle enums (use .name if available, fallback to value)
            try:
                import enum

                if isinstance(param, enum.Enum):
                    return param.name
            except ImportError:
                pass

            # Float formatting
            if isinstance(param, float):
                return f"{param:.{float_precision}f}"

            # List / tuple
            if isinstance(param, (list, tuple)):
                n = len(param)
                if n > 5:
                    preview = ", ".join(str(item) for item in param[:5])
                    return f"{type(param).__name__}[len={n}, preview=[{preview}, ...]]"
                return str(param)

            # Dictionary
            if isinstance(param, dict):
                items = list(param.items())
                n = len(items)
                if n > 3:
                    preview = ", ".join(f"{k}={v}" for k, v in items[:3])
                    return (
                        f"{type(param).__name__}[len={n}, preview={{ {preview}, ... }}]"
                    )
                return str(param)

            # Bytes / bytearray
            if isinstance(param, (bytes, bytearray)):
                n = len(param)
                if n > 8:
                    preview = " ".join(f"0x{b:02X}" for b in param[:8])
                    return f"{type(param).__name__}[len={n}, preview={preview} ...]"
                return " ".join(f"0x{b:02X}" for b in param)

            # NumPy arrays
            try:
                import numpy as np

                if isinstance(param, np.ndarray):
                    return f"ndarray(shape={param.shape}, dtype={param.dtype})"
            except ImportError:
                pass

            # Default string with recursion protection
            try:
                return str(param)
            except RecursionError:
                return f"<{type(param).__name__} with circular reference>"

        type_name = type(parameter).__name__
        formatted_value = format_value(parameter)

        # Truncate final string if still too long
        if len(formatted_value) > max_length:
            formatted_value = formatted_value[: max_length - 3] + "..."

        padded_message = f"{message:<{LOG_PADDING_WIDTH}}"
        padded_type = f"{type_name:<12}"
        final_message = f"{padded_message} {padded_type} {formatted_value}".rstrip()

        Logger.message(final_message, silent=silent, stacklevel=stacklevel, level=level)

    @staticmethod
    def header_message(
        message: str,
        level: int = logging.INFO,
        silent: bool = False,
        stacklevel: int = 3,
    ) -> None:
        """
        Logs a visually distinct header message with separator lines and emojis.

        :param stacklevel: int
        :param silent: bool whether or not to write to the log
        :param message: The message to log.
        :param level: Logging level (default: logging.INFO).
        """
        full_separator = f"{'=' * 142}"
        separator = f"{'=' * 100}"

        Logger.message(
            f"\n{full_separator}", level=level, stacklevel=stacklevel, silent=silent
        )
        Logger.message(f"{message}", level=level, stacklevel=stacklevel, silent=silent)
        Logger.message(separator, level=level, stacklevel=stacklevel, silent=silent)

    @staticmethod
    def debug_info(successes: list, failures: list, stacklevel: int = 3) -> None:
        """
        Logs debug information about the parsed SysEx data.

        :param stacklevel: int - stacklevel
        :param successes: list – Parameters successfully decoded.
        :param failures: list – Parameters that failed decoding.
        """
        for listing in [successes, failures]:
            try:
                listing.remove("SYNTH_TONE")
            except ValueError:
                pass  # or handle the error

        total = len(successes) + len(failures)
        success_rate = (len(successes) / total * 100) if total else 0.0

        Logger.message(
            f"Successes ({len(successes)}): {successes}", stacklevel=stacklevel
        )
        Logger.message(f"Failures ({len(failures)}): {failures}", stacklevel=stacklevel)
        Logger.message(f"Success Rate: {success_rate:.1f}%", stacklevel=stacklevel)
        Logger.message("=" * 100, stacklevel=3)
