import json
import logging


class JsonFormatter(logging.Formatter):
    """One JSON object per line; Cloud Logging maps "severity" to log level."""

    def format(self, record):
        entry = {
            "severity": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry)
