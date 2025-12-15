import logging
from logging.config import dictConfig


def setup_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"}
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "level": "INFO",
                }
            },
            "root": {"handlers": ["console"], "level": "INFO"},
        }
    )
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Retourne un logger pour un module donné."""
    return logging.getLogger(name)

