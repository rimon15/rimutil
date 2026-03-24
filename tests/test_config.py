from dataclasses import dataclass
from unittest.mock import Mock

from omegaconf import OmegaConf
import pytest

import rimutil.config as config_module


@dataclass
class AppConfig(config_module.BaseConfig):
  greeting: str = "hello"
  count: int = 1


@dataclass(kw_only=True)
class ProjectConfig(config_module.BaseConfig):
  project_name: str = "train"


@dataclass
class AppConfigWithProjectName(ProjectConfig):
  greeting: str = "hello"
  count: int = 1


def test_setup_entrypoint_merges_cli_overrides_and_infers_log_filename_from_project_name(
  monkeypatch,
) -> None:
  setup_logger = Mock()
  monkeypatch.setattr(config_module, "setup_logger", setup_logger)
  monkeypatch.setattr(
    config_module.OmegaConf,
    "from_cli",
    lambda: OmegaConf.create({"greeting": "hola", "count": 3}),
  )

  @config_module.setup_entrypoint(AppConfigWithProjectName)
  def run(cfg: AppConfigWithProjectName, suffix: str, *, excited: bool = False):
    return cfg, suffix, excited

  cfg, suffix, excited = run("!", excited=True)

  setup_logger.assert_called_once_with("train.log")
  assert cfg == AppConfigWithProjectName(project_name="train", greeting="hola", count=3)
  assert suffix == "!"
  assert excited is True
  assert run.__name__ == "run"


def test_setup_entrypoint_uses_default_log_filename_when_config_has_none(monkeypatch) -> None:
  setup_logger = Mock()
  monkeypatch.setattr(config_module, "setup_logger", setup_logger)
  monkeypatch.setattr(config_module.OmegaConf, "from_cli", lambda: OmegaConf.create({}))

  @config_module.setup_entrypoint(AppConfig)
  def run(cfg: AppConfig):
    return cfg

  cfg = run()

  setup_logger.assert_called_once_with("app.log")
  assert cfg == AppConfig()


def test_setup_entrypoint_raises_when_config_does_not_inherit_base_config(monkeypatch) -> None:
  @dataclass
  class InvalidConfig:
    greeting: str = "hello"

  setup_logger = Mock()
  monkeypatch.setattr(config_module, "setup_logger", setup_logger)
  monkeypatch.setattr(config_module.OmegaConf, "from_cli", lambda: OmegaConf.create({}))

  @config_module.setup_entrypoint(InvalidConfig)
  def run(cfg: InvalidConfig):
    return cfg

  with pytest.raises(TypeError, match="InvalidConfig must inherit from BaseConfig"):
    run()

  setup_logger.assert_not_called()


def test_base_config_computes_log_filename() -> None:
  cfg = config_module.BaseConfig(project_name="demo")

  assert cfg.log_filename == "demo.log"
