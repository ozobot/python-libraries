import json

import nox
import nox_uv

nox.options.default_venv_backend = "uv"


def workspace_members(session):
    with open("/dev/null") as f:
        raw_metadata = session.run("uv", "workspace", "metadata", silent=True, stderr=f)
    metadata = json.loads(raw_metadata)
    members = metadata["members"]
    root = metadata["workspace_root"]
    yield from (m["path"] for m in members if m["path"] != root)


def get_target_packages(session):
    return [session.posargs[0]] if session.posargs else workspace_members(session)


class UvRunner:
    def __init__(self, *, session, path):
        self._session = session
        self._path = path

    def run_cmd(self, *cmd):
        with self._session.chdir(self._path):
            run_cmd = "uv", "run", "--exact", "--with", "../[dev]"
            self._session.run(*run_cmd, *cmd)


@nox_uv.session()
def test(session):
    for path in get_target_packages(session):
        UvRunner(session=session, path=path).run_cmd("pytest", "-vv")


@nox_uv.session()
def lint(session):
    for path in get_target_packages(session):
        UvRunner(session=session, path=path).run_cmd("ruff", "check")
        UvRunner(session=session, path=path).run_cmd("ruff", "format", "--check")


@nox_uv.session(name="type-check")
def type_check(session):
    for path in get_target_packages(session):
        UvRunner(session=session, path=path).run_cmd("mypy", ".")
