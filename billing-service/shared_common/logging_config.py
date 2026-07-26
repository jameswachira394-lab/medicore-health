import logging
import sys


def configure_logging(service_name: str, level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        f'{{"service": "{service_name}", "level": "%(levelname)s", '
        f'"logger": "%(name)s", "message": "%(message)s"}}'
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]
