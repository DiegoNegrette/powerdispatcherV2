LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} [{asctime}] {message}",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "filters": [],
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file_scraper": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "logs/scraper.log",
            "formatter": "simple",
        },
        "file_callrail": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "logs/callrail.log",
            "formatter": "simple",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "propagate": True,
        },
        "scraper": {
            "handlers": ["console", "file_scraper"],
            "level": "INFO",
            "propagate": False,
        },
        "callrail": {
            "handlers": ["console", "file_callrail"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
