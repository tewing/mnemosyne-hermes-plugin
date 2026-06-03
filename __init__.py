"""mnemosyne plugin: installs the Mnemosyne memory backend.

On load, ensures `mnemosyne-memory[embeddings,mcp]` is importable so other
plugins / agent code can `import mnemosyne` and use its memory primitives
(remember, recall, triple_*, scratchpad_*).

The hermes-agent image ships a read-only venv with no `pip`, so the package
can't be installed into site-packages at runtime. Instead this installs into a
writable per-agent directory on the PVC (`$HERMES_HOME/pydeps`) with
`uv pip install --target` and prepends that directory to `sys.path`.

Extras: `embeddings` (fastembed + sqlite-vec for vector recall) and `mcp`. The
`llm`/`all` extras are deliberately excluded — they pull `llama-cpp-python`,
which needs a C/C++ compiler the runtime image lacks, and the local llama-cpp
inference backend is unused (the agent's LLM provider is remote).

Install-only in v0.1 — this plugin registers no tools of its own.
"""

import importlib
import importlib.util
import os
import shutil
import subprocess
import sys

MNEMOSYNE_REQUIREMENT = "mnemosyne-memory[embeddings,mcp]"


def _target_dir():
    """Writable install dir on the PVC (the venv site-packages is read-only)."""
    return os.path.join(os.environ.get("HERMES_HOME", "/opt/data"), "pydeps")


def _ensure_on_path(target):
    if target not in sys.path:
        sys.path.insert(0, target)


def _ensure_mnemosyne():
    """Install Mnemosyne into the PVC target dir if it isn't already importable.

    Idempotent: the target is put on `sys.path` first, so a warm PVC where the
    package is already present skips the install entirely.
    """
    target = _target_dir()
    _ensure_on_path(target)
    if importlib.util.find_spec("mnemosyne") is not None:
        return
    os.makedirs(target, exist_ok=True)
    installer = shutil.which("uv")
    cmd = (
        [installer, "pip", "install", "--target", target, MNEMOSYNE_REQUIREMENT]
        if installer
        else [sys.executable, "-m", "pip", "install", "--target", target,
              MNEMOSYNE_REQUIREMENT]
    )
    subprocess.check_call(cmd)
    importlib.invalidate_caches()
    _ensure_on_path(target)


def register(ctx):
    del ctx
    _ensure_mnemosyne()
