from types import SimpleNamespace

from loguru import logger

from rm_utils.log import loguru_before_sleep, setup_logger


def test_setup_logger_writes_messages_to_log_file(tmp_path) -> None:
  log_file = tmp_path / "app.log"

  setup_logger(str(log_file))
  logger.info("hello {}", "world")
  logger.complete()

  assert log_file.exists()
  contents = log_file.read_text()
  assert "INFO" in contents
  assert "hello world" in contents


def test_loguru_before_sleep_logs_retry_warning(tmp_path) -> None:
  log_file = tmp_path / "retry.log"

  setup_logger(str(log_file))

  def flaky_operation() -> None:
    return None

  retry_state = SimpleNamespace(
    outcome=SimpleNamespace(exception=lambda: ValueError("boom")),
    next_action=SimpleNamespace(sleep=1.5),
    attempt_number=2,
    fn=flaky_operation,
  )

  loguru_before_sleep(retry_state)
  logger.complete()

  contents = log_file.read_text()
  assert "WARNING" in contents
  assert "Retrying in 1.50s (attempt 2) due to: ValueError('boom')" in contents
