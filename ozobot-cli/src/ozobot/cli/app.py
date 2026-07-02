from __future__ import annotations

import typer

from . import commands_scan

app = typer.Typer(
    name="ozobot",
    help="Ozobot command-line interface.",
    no_args_is_help=True,
)

app.add_typer(commands_scan.app)


__all__ = ["app"]
