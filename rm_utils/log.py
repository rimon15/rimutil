import sys
from loguru import logger
from tenacity import RetryCallState


def setup_logger(log_filename: str = "app.log") -> None:
  logger.remove()
  logger.add(
    sys.stderr,
    level="DEBUG",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    enqueue=True,
    colorize=True,
  )
  logger.add(
    log_filename,
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    enqueue=True,
    colorize=False,
    rotation="50 MB",
    retention="7 days",
  )


def loguru_before_sleep(retry_state: RetryCallState) -> None:
  ex = retry_state.outcome.exception() if retry_state.outcome else None
  sleep = retry_state.next_action.sleep if retry_state.next_action else None

  logger.bind(
    attempt=retry_state.attempt_number,
    fn=getattr(retry_state.fn, "__name__", str(retry_state.fn)),
  ).warning(
    "Retrying in {sleep:.2f}s (attempt {attempt}) due to: {ex}",
    sleep=float(sleep or 0),
    attempt=retry_state.attempt_number,
    ex=repr(ex),
  )
