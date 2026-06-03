"""mnemosyne plugin: thin loader for the official Mnemosyne Hermes integration.

This repo exists only so Hermes' clone-and-discover plugin loader (which needs
a `plugin.yaml` + `register(ctx)` at the plugin-dir root) can load the upstream
Mnemosyne integration. The upstream repo (github.com/AxDSan/Mnemosyne) has no
root plugin.yaml and is built for `pip install`, so it can't be git-cloned into
the plugins dir and discovered directly.

The official Hermes integration ships INSIDE the `mnemosyne-memory` package as
the top-level `hermes_memory_provider` module (exposing `register` and
`register_memory_provider`). On load this:
  1. Installs `mnemosyne-memory[embeddings]` (fastembed + sqlite-vec for vector
     recall; compiler-free wheels) into a writable PVC dir via
     `uv pip install --target`, because the hermes-agent venv is read-only and
     ships no pip.
  2. Delegates to `hermes_memory_provider.register(ctx)` (the `hermes mnemosyne`
     CLI) and, best-effort, `register_memory_provider(ctx)` (the memory backend).
"""

import importlib
import importlib.util
import os
import shutil
import subprocess
import sys

REQUIREMENTS = ["mnemosyne-memory[embeddings]"]
PROVIDER_MODULE = "hermes_memory_provider"


def _target_dir():
    """Writable install dir on the PVC (the venv site-packages is read-only)."""
    return os.path.join(os.environ.get("HERMES_HOME", "/opt/data"), "pydeps")


def _ensure_on_path(target):
    if target not in sys.path:
        sys.path.insert(0, target)


def _ensure_installed():
    """Install mnemosyne-memory if its hermes provider module isn't importable.

    Idempotent: the target is put on sys.path first, so a warm PVC where the
    package is already present skips the install entirely.
    """
    target = _target_dir()
    _ensure_on_path(target)
    if importlib.util.find_spec(PROVIDER_MODULE) is not None:
        return
    os.makedirs(target, exist_ok=True)
    installer = shutil.which("uv")
    base = [installer, "pip", "install", "--target", target] if installer \
        else [sys.executable, "-m", "pip", "install", "--target", target]
    subprocess.check_call(base + REQUIREMENTS)
    importlib.invalidate_caches()
    _ensure_on_path(target)


def register(ctx):
    _ensure_installed()
    provider = importlib.import_module(PROVIDER_MODULE)

    # CLI command (`hermes mnemosyne ...`).
    provider.register(ctx)

    # Memory provider (the remember/recall backend). Hermes' memory-provider
    # discovery also calls this once the module is importable + config has
    # memory.provider=mnemosyne; we register directly when the plugin ctx
    # supports it, and never fail the load if it doesn't.
    provider_fn = getattr(provider, "register_memory_provider", None)
    if provider_fn is not None and hasattr(ctx, "register_memory_provider"):
        try:
            provider_fn(ctx)
        except Exception as exc:  # noqa: BLE001 - best-effort; don't break load
            print(f"[mnemosyne] register_memory_provider skipped: {exc}", file=sys.stderr)
