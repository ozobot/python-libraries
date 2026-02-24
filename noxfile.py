import json

import nox


def workspace_members(session):
    with open("/dev/null") as f:
        raw_metadata = session.run("uv", "workspace", "metadata", silent=True, stderr=f)
    metadata = json.loads(raw_metadata)
    members = metadata["members"]
    root = metadata["workspace_root"]
    yield from (m["path"] for m in members if m["path"] != root)


@nox.session(venv_backend="none")
def test(session):
    if session.posargs:
        _run_all(session=session, path=session.posargs[0])
    else:
        for path in workspace_members(session):
            _run_all(session=session, path=path)
            

def _run_all(*, session, path):
    _run_cmd("pytest", "-vv", session=session, path=path)
    _run_cmd("mypy", ".", session=session, path=path)
    _run_cmd("ruff", "check", session=session, path=path)
    _run_cmd("ruff", "format", "--check", session=session, path=path)


def _run_cmd(*cmd, session, path):
    with session.chdir(path):
        run_cmd = "uv", "run", "--exact", "--with", "../[dev]"
        session.run(*run_cmd, *cmd)
