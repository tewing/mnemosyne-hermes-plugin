# mnemosyne-hermes-plugin

Hermes-agent plugin that installs the [Mnemosyne](https://github.com/AxDSan/Mnemosyne)
memory backend into the hermes-agent environment.

On load, `register(ctx)` ensures the `mnemosyne-memory[embeddings,mcp]` package
is importable. The hermes-agent image ships a **read-only venv with no `pip`**,
so the package can't be installed into site-packages at runtime. Instead it is
installed into a writable per-agent directory on the PVC
(`$HERMES_HOME/pydeps`) via `uv pip install --target`, and that directory is
prepended to `sys.path`. The install is idempotent — the target is put on
`sys.path` first, so it's skipped when `mnemosyne` already imports (no-op on
warm PVCs; only runs on a fresh PVC).

`mnemosyne-memory` installs as the importable `mnemosyne` module and exposes the
memory primitives (`remember`, `recall`, `triple_*`, `scratchpad_*`).

### Why `[embeddings,mcp]` and not `[all]`

The `llm`/`all` extras pull `llama-cpp-python` (+ `ctransformers`), which compile
native C++ — the runtime image has no compiler (`CMAKE_CXX_COMPILER not set`), so
`[all]` cannot install at runtime. The local llama-cpp inference backend is also
unused (the agent's LLM provider is remote). `[embeddings]` (fastembed +
sqlite-vec, both prebuilt wheels) gives vector recall; `[mcp]` adds the MCP
server. Both are compiler-free.

## Scope

v0.1 is **install-only** — this plugin registers no tools of its own. Tool
registration for the Mnemosyne primitives is provided separately by the upstream
Mnemosyne hermes plugin (`github.com/AxDSan/Mnemosyne`).

## How hermes-agent loads this

hermes-agent scans `~/.hermes/plugins/`, finds this directory's `plugin.yaml`,
and calls `register(ctx)` from `__init__.py`. The plugin only loads if
`mnemosyne` appears under `plugins.enabled` in hermes-agent's `config.yaml`.

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
