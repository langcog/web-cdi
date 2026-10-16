import json
import logging
import os


class JsonFormatter(logging.Formatter):
    """One JSON object per line for Cloud Logging.

    "severity" maps to the log level; records with an exception carry the
    traceback in "stack_trace" plus "serviceContext", which is what Cloud Error
    Reporting needs to group them (K_SERVICE/K_REVISION are set by Cloud Run).
    """

    def format(self, record):
        entry = {
            "severity": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            entry["stack_trace"] = self.formatException(record.exc_info)
            entry["serviceContext"] = {
                "service": os.environ.get("K_SERVICE", "webcdi"),
                "version": os.environ.get("K_REVISION", "unknown"),
            }
        return json.dumps(entry)
