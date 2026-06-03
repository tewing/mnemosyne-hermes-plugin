# mnemosyne-hermes-plugin

Hermes-agent plugin that installs the [Mnemosyne](https://github.com/AxDSan/Mnemosyne)
memory backend into the hermes-agent environment.

On load, `register(ctx)` ensures the `mnemosyne-memory[all]` package is present
by running `pip install "mnemosyne-memory[all]"`. The install is idempotent — it
is skipped when the `mnemosyne` module already imports, so it only runs on a
fresh pod and is a no-op on warm PVCs.

`mnemosyne-memory` installs as the importable `mnemosyne` module and exposes the
memory primitives (`remember`, `recall`, `triple_*`, `scratchpad_*`).

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
