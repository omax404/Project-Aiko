import logging
import json
import datetime
import traceback
import os

class StructuredJSONFormatter(logging.Formatter):
    """
    Format logs as structured JSON for easy shipping to observability stacks.
    Filters out sensitive data if needed.
    """
    def format(self, record):
        log_record = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "level": record.levelname,
            "logger_name": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineNo": record.lineno,
        }

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            log_record["traceback"] = "".join(traceback.format_tb(record.exc_info[2]))

        if hasattr(record, "custom_data"):
            log_record["data"] = record.custom_data

        return json.dumps(log_record)


def setup_structured_logging(logger_name="AikoSystem", level=logging.INFO):
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # Clear existing handlers to prevent duplicates
    if logger.hasHandlers():
        logger.handlers.clear()

    # Console Handler with JSON formatting
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(StructuredJSONFormatter())
    logger.addHandler(console_handler)

    # File Handler
    logs_dir = os.path.join(os.path.dirname(__file__), "..", "data", "logs")
    os.makedirs(logs_dir, exist_ok=True)
    file_handler = logging.FileHandler(os.path.join(logs_dir, "system_audit.log"))
    file_handler.setFormatter(StructuredJSONFormatter())
    logger.addHandler(file_handler)

    return logger

# Global setup
system_logger = setup_structured_logging()
