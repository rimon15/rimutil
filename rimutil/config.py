from dataclasses import dataclass
from omegaconf import OmegaConf
from collections.abc import Callable
from functools import wraps
from typing import Concatenate, ParamSpec, TypeVar, cast

from rimutil.log import setup_logger


@dataclass(kw_only=True)
class BaseConfig:
  project_name: str = "app"

  @property
  def log_filename(self) -> str:
    return f"{self.project_name}.log"


ConfigT = TypeVar("ConfigT", bound=BaseConfig)
P = ParamSpec("P")
R = TypeVar("R")


def setup_entrypoint(
  conf_cls: type[ConfigT],
) -> Callable[[Callable[Concatenate[ConfigT, P], R]], Callable[P, R]]:
  def decorator(fn: Callable[Concatenate[ConfigT, P], R]) -> Callable[P, R]:
    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
      merged_cfg = OmegaConf.merge(
        OmegaConf.structured(conf_cls),
        OmegaConf.from_cli(),
      )

      cfg = OmegaConf.to_object(merged_cfg)
      if not isinstance(cfg, BaseConfig):
        raise TypeError(f"{conf_cls.__name__} must inherit from BaseConfig")

      setup_logger(cfg.log_filename)
      return fn(cast(ConfigT, cfg), *args, **kwargs)

    return wrapper

  return decorator
