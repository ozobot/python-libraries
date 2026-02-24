# Ozobot Python libraries

A monorepo repository with Python libraries for Ozobot Evo and Ari control. The libraries can be used in the [Ozobot Editor](https://editor.ozobot.com).

The local execution on a computer is currently work in progress.

<!-- ## Installation -->
<!-- All the libraries are hosted on [PyPI](https://pypi.org/user/ozobot/). -->

<!-- ```sh -->
  <!-- pip install ozobot-ari -->
<!-- ``` -->

<!-- or -->

<!-- ```sh -->
  <!-- pip install ozobot-evo -->
<!-- ``` -->

## Repository contents
The repository contains several directories with packages implementing either robot control functionality or a backend functionality used by the user facing control libraries.
Users are generally interested in the control libraries:

 - [`ozobot-ari`](/ozobot-ari) for Ari
 - [`ozobot-evo`](/ozobot-evo) for Evo
 - [`ozobot-actors`](/ozobot-actors) used by Blockly exported programs for Ari and Evo 

But there are also other back end libraries such as:

 - [`ozobot-ble`](/ozobot-ble)
 - [`ozobot-jsonrpc`](/ozobot-jsonrpc)
 - [`ozobot-webrtc`](/ozobot-webrtc)

## Development
### Project structure
The project uses `uv` and leverages [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/) to define multiple (namespaced) packages in directories
prefixed with `ozobot-`. Each package adheres to the same structure:
```
$ tree -L1 ozobot-evo
ozobot-evo
├── pyproject.toml
├── README.md
├── src
│   └── ozobot
│       └── evo
└── tests
```
In addition to the package-wise `pyproject.toml` files, there's also a repo level one that defines the uv workspace and
global configuration for `pytest`, `mypy` and `ruff`. `uv.lock` is used to lock project dependencies.

### Build
Run `uv build --wheel --all-packages` or `uv build --sdist --all-packages` to build all the packages to the `dist` directory. To build packages individually
use `--package <package-name>` (e.g., `--package ozobot-evo`) instead.

### Test
`nox` is used to run tests, type checking and linting, so executing
```
  $ uv run nox
```
is sufficient to test the whole repo. A session that executes `pytest`, `ruff` and `mypy` is run for each workspace member package.

Package name can be passed as an argument to only run tests in that package, for example
```
  $ uv run nox -- ozobot-ari
```

Test dependencies are declared in the workspace root project.

### Installation from sources
To install all the workspace packages and its dependencies to the uv venv, run
```
  $ uv venv
  $ uv sync --all-packages --inexact
  $ # activate the venv as usual
```

Omit `--inexact` to remove extra packages. Workspace packages are installed as editable.

### Documentation
The documentation sources can be found in `/docs` directory. It can be built by
```
  $ uv run \
    --all-packages --all-extras --group docs \
    make html -C docs
```
