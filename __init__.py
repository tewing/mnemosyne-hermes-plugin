"""mnemosyne plugin: installs the Mnemosyne memory backend.

On load, ensures `mnemosyne-memory[all]` is pip-installed into the
hermes-agent environment so other plugins / agent code can `import mnemosyne`
and use its memory primitives (remember, recall, triple_*, scratchpad_*).

Install-only in v0.1 — this plugin registers no tools of its own.
"""

import importlib.util
import subprocess
import sys

MNEMOSYNE_REQUIREMENT = "mnemosyne-memory[all]"


def _ensure_mnemosyne():
    """Install Mnemosyne if it isn't already importable.

    Idempotent: skips the pip call when `mnemosyne` already imports, so it's
    a no-op on warm PVCs and only pays the install cost on a fresh pod.
    """
    if importlib.util.find_spec("mnemosyne") is not None:
        return
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", MNEMOSYNE_REQUIREMENT]
    )


def register(ctx):
    del ctx
    _ensure_mnemosyne()
