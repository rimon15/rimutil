from omegaconf import OmegaConf
from collections.abc import Callable
from functools import wraps
from typing import Concatenate, ParamSpec, TypeVar, cast

from rm_utils.log import setup_logger


ConfigT = TypeVar("ConfigT")
P = ParamSpec("P")
R = TypeVar("R")


def setup_entrypoint(
  conf_cls: type[ConfigT],
) -> Callable[[Callable[Concatenate[ConfigT, P], R]], Callable[P, R]]:
  def decorator(fn: Callable[Concatenate[ConfigT, P], R]) -> Callable[P, R]:
    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
      setup_logger()

      merged_cfg = OmegaConf.merge(
        OmegaConf.structured(conf_cls),
        OmegaConf.from_cli(),
      )

      cfg = cast(ConfigT, OmegaConf.to_object(merged_cfg))
      return fn(cfg, *args, **kwargs)

    return wrapper

  return decorator
