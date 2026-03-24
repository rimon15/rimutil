from dataclasses import dataclass
from unittest.mock import Mock

from omegaconf import OmegaConf

import rm_utils.config as config_module


@dataclass
class AppConfig:
  greeting: str = "hello"
  count: int = 1


def test_setup_entrypoint_merges_cli_overrides_and_calls_logger(monkeypatch) -> None:
  setup_logger = Mock()
  monkeypatch.setattr(config_module, "setup_logger", setup_logger)
  monkeypatch.setattr(
    config_module.OmegaConf,
    "from_cli",
    lambda: OmegaConf.create({"greeting": "hola", "count": 3}),
  )

  @config_module.setup_entrypoint(AppConfig)
  def run(cfg: AppConfig, suffix: str, *, excited: bool = False):
    return cfg, suffix, excited

  cfg, suffix, excited = run("!", excited=True)

  setup_logger.assert_called_once_with()
  assert cfg == AppConfig(greeting="hola", count=3)
  assert suffix == "!"
  assert excited is True
  assert run.__name__ == "run"
