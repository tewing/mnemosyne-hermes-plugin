"""mnemosyne plugin: thin loader for the official Mnemosyne Hermes plugin.

This repo exists only so Hermes' clone-and-discover plugin loader (which needs
a `plugin.yaml` + `register(ctx)` at the plugin-dir root) can load the upstream
Mnemosyne integration. The upstream repo (github.com/AxDSan/Mnemosyne) has no
root plugin.yaml and is built for `pip install mnemosyne-hermes`, so it can't be
git-cloned into the plugins dir directly.

On load this:
  1. Installs the official `mnemosyne-hermes` package (which pulls
     `mnemosyne-memory`) into a writable PVC dir via `uv pip install --target`,
     because the hermes-agent venv is read-only and ships no pip. The
     `[embeddings]` extra (fastembed + sqlite-vec, compiler-free wheels) gives
     vector recall.
  2. Delegates registration to the upstream `mnemosyne_hermes` module —
     `register(ctx)` (the `hermes mnemosyne` CLI) and, best-effort,
     `register_memory_provider(ctx)` (the memory backend).
"""

import importlib
import importlib.util
import os
import shutil
import subprocess
import sys

REQUIREMENTS = ["mnemosyne-hermes", "mnemosyne-memory[embeddings]"]


def _target_dir():
    """Writable install dir on the PVC (the venv site-packages is read-only)."""
    return os.path.join(os.environ.get("HERMES_HOME", "/opt/data"), "pydeps")


def _ensure_on_path(target):
    if target not in sys.path:
        sys.path.insert(0, target)


def _ensure_installed():
    """Install the official mnemosyne-hermes package if not already importable.

    Idempotent: the target is put on sys.path first, so a warm PVC where the
    package is already present skips the install entirely.
    """
    target = _target_dir()
    _ensure_on_path(target)
    if importlib.util.find_spec("mnemosyne_hermes") is not None:
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
    import mnemosyne_hermes

    # CLI command (`hermes mnemosyne ...`) + any tool registration upstream does.
    mnemosyne_hermes.register(ctx)

    # Memory provider (the remember/recall backend). Hermes' memory-provider
    # discovery also calls this once the package is importable + config has
    # memory.provider=mnemosyne; we register directly when the plugin ctx
    # supports it, and never fail the load if it doesn't.
    provider_fn = getattr(mnemosyne_hermes, "register_memory_provider", None)
    if provider_fn is not None and hasattr(ctx, "register_memory_provider"):
        try:
            provider_fn(ctx)
        except Exception as exc:  # noqa: BLE001 - best-effort; don't break load
            print(f"[mnemosyne] register_memory_provider skipped: {exc}", file=sys.stderr)
