# rimutil
Utility helpers for config management, logging, timers, and deep learning.

## Installation
Core package:

```bash
pip install rimutil
```

With the deep-learning helpers:

```bash
pip install "rimutil[dl]"
```

## Config And Entrypoints
`BaseConfig` gives each project a shared `project_name`, and `setup_entrypoint()` handles:

- merging the structured dataclass config with CLI overrides
- initializing logging

Example:

```python
from dataclasses import dataclass

from rimutil import BaseConfig, setup_entrypoint


@dataclass(kw_only=True)
class ProjectConfig(BaseConfig):
  project_name: str = "mnist_train"


@dataclass
class TrainConfig(ProjectConfig):
  batch_size: int = 32
  learning_rate: float = 1e-3
  epochs: int = 10


@setup_entrypoint(TrainConfig)
def main(cfg: TrainConfig) -> None:
  print(cfg)


if __name__ == "__main__":
  main()
```

CLI overrides are merged automatically:

```bash
python train.py batch_size=64 epochs=20
```

`BaseConfig.log_filename` defaults to `<project_name>.log`, so the config above writes logs to `mnist_train.log`.

## Logging
`setup_entrypoint()` already calls `setup_logger(cfg.log_filename)` for you, but you can also initialize logging manually:

```python
from loguru import logger

from rimutil import setup_logger

setup_logger("debug.log")
logger.info("hello from rimutil")
```

Current logger behavior:

- logs to stderr and to a file
- uses `DEBUG` level for both sinks
- rotates files at `50 MB`
- keeps logs for `7 days`

If you use `tenacity`, `loguru_before_sleep()` can be passed to `before_sleep`:

```python
from tenacity import retry, stop_after_attempt, wait_fixed

from rimutil import loguru_before_sleep


@retry(
  stop=stop_after_attempt(3),
  wait=wait_fixed(2),
  before_sleep=loguru_before_sleep,
)
def flaky_call() -> None:
  raise RuntimeError("try again")
```

## Timer
`Timer` works as:

- a context manager
- an async context manager
- a decorator for sync functions
- a decorator for async functions

Basic context-manager usage:

```python
from rimutil import Timer

with Timer("load_data"):
  ...
```

Decorator usage:

```python
from rimutil import Timer


@Timer()
def train_epoch() -> None:
  ...
```

Writing timings to a file or logger:

```python
from loguru import logger

from rimutil import Timer, setup_logger

setup_logger("timings.log")

with Timer("eval", fpath="timings.tsv", logger=logger, do_print=False):
  ...
```

Behavior notes:

- `desc` is used as the label in printed and logged messages
- when used as a decorator, the function name is used if `desc` is empty
- `fpath` appends lines like `<desc>:\t<elapsed>`
- `logger.info(...)` is called when a logger is provided

## Deep Learning Helpers
The DL utilities live in `rimutil.dl` and require the optional `dl` extra.

Seed Python, NumPy, and PyTorch:

```python
from rimutil.dl import seed_all

seed_all(42)
```

What `seed_all()` does:

- seeds `random`
- seeds `numpy`
- seeds `torch`
- seeds all CUDA devices when CUDA is available
- sets deterministic cuDNN mode
- disables cuDNN benchmarking

Free cached GPU memory:

```python
from rimutil.dl import cleanup_gpu_mem

cleanup_gpu_mem()
```

`cleanup_gpu_memory()` is an alias for `cleanup_gpu_mem()`.

## Publishing To PyPI
Run `scripts/bump_and_publish.sh`.
It bumps the version, refreshes `uv.lock`, creates a release commit, tags it, and pushes both `main` and the new release tag.
