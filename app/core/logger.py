import logging
import sys
import colorlog

LOG_FORMAT = (
    "%(log_color)s"
    "%(asctime)s | "
    "%(levelname)-8s | "
    "%(name)s | "
    "%(filename)s:%(lineno)d | "
    "%(message)s"
)

LOG_COLORS = {
    "DEBUG": "cyan",
    "INFO": "green",
    "WARNING": "yellow",
    "ERROR": "red",
    "CRITICAL": "bold_red",
}


def get_logger(name: str = "FastAPI") -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    console_handler = colorlog.StreamHandler(sys.stdout)

    console_handler.setFormatter(
        colorlog.ColoredFormatter(
            LOG_FORMAT,
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors=LOG_COLORS,
        )
    )

    logger.addHandler(console_handler)

    return logger


logger = get_logger()
