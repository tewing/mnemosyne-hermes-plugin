# mnemosyne-hermes-plugin

A thin **loader shim** for the official [Mnemosyne](https://github.com/AxDSan/Mnemosyne)
Hermes plugin.

The upstream repo has no `plugin.yaml` at its root and is built for
`pip install mnemosyne-hermes` / `hermes plugins install <url>` — so it can't be
git-cloned into Hermes' plugins dir and discovered directly. This repo provides
the root `plugin.yaml` + `register(ctx)` that Hermes' clone-and-discover loader
needs, and delegates to the upstream package.

On load, `register(ctx)`:

1. Installs the official **`mnemosyne-hermes`** package (which pulls
   `mnemosyne-memory`) plus the `mnemosyne-memory[embeddings]` extra into a
   writable per-agent directory on the PVC (`$HERMES_HOME/pydeps`) via
   `uv pip install --target`. The hermes-agent image ships a **read-only venv
   with no `pip`**, so installing into site-packages isn't possible; the target
   dir is prepended to `sys.path`. Idempotent — skipped when `mnemosyne_hermes`
   already imports.
2. Delegates to the upstream module: `mnemosyne_hermes.register(ctx)` (the
   `hermes mnemosyne` CLI) and, best-effort, `register_memory_provider(ctx)`
   (the memory backend that exposes remember/recall).

### Why the `[embeddings]` extra

`[embeddings]` (fastembed + sqlite-vec, prebuilt wheels) gives vector recall and
is compiler-free. The `llm`/`all` extras are avoided — they pull
`llama-cpp-python`, which needs a C/C++ compiler the runtime image lacks, and the
local inference backend is unused (the agent's LLM provider is remote).

## How hermes-agent loads this

hermes-agent scans its plugins dir, finds this directory's `plugin.yaml`, and
calls `register(ctx)` from `__init__.py` — which installs and delegates to the
upstream `mnemosyne_hermes`. The plugin only loads if `mnemosyne` appears under
`plugins.enabled` in hermes-agent's `config.yaml`.

## Local development

```bash
mkdir -p ~/.hermes/plugins/mnemosyne
cp -r ./{plugin.yaml,__init__.py} ~/.hermes/plugins/mnemosyne/
printf 'plugins:\n  enabled:\n    - mnemosyne\n' >> ~/.hermes/config.yaml
hermes chat -q "what memory tools do you have?"
```

## Versioning

Pinned tags (`vX.Y.Z`) drive production clones. `main` is for active
development. Bump the version in `plugin.yaml` on each release.
