#!/usr/bin/env python
import os
import sys

import dotenv

if __name__ == "__main__":
    dotenv.load_dotenv()

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webcdi.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as e:
        raise ImportError(
            f"Couldn't import Django. Are you sure it's installed and available on your PYTHONPATH environment variable? Did you forget to activate a virtual environment? \n Error {e}"
        )
    execute_from_command_line(sys.argv)
