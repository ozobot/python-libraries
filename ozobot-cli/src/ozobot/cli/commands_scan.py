from __future__ import annotations

import asyncio
import contextlib
import math
import sys
import time
import typing

import typer
from ozobot.ble.connection import scan_devices

from .output import make_formatter
from .runner import run

app = typer.Typer(
    name="scan",
    short_help="Discover nearby Ozobots over BLE.",
    help=(
        "Discover nearby Ozobots over BLE. "
        "Scanning continues until --timeout elapses, --max-devices unique devices "
        "are seen, or Ctrl-C is pressed."
    ),
    invoke_without_command=True,
)

_JSON_DEFAULT_MAX_DEVICES = 1


async def _async_scan(
    *,
    timeout: float | None,  # noqa: ASYNC109
    refresh: float,
    json_output: bool,
    max_devices: int | None,
    stdout: typing.TextIO,
    stderr: typing.TextIO,
) -> None:
    formatter = make_formatter(
        json_output=json_output,
        stream=stdout,
        keys=["name", "id", "address", "product", "version", "rssi"],
        column_size=[20, 32, 17, 8, 10, 7],
    )
    last_seen: dict[str, float] = {}
    unique: set[str] = set()
    timeout_cm = asyncio.timeout(timeout) if timeout else contextlib.nullcontext()

    with contextlib.suppress(asyncio.TimeoutError):
        async with timeout_cm, scan_devices() as stream, formatter:
            async for device, _handle in stream:
                key = device.address
                now = time.monotonic()
                previous = last_seen.get(key)
                if previous is not None and now - previous < refresh:
                    continue
                last_seen[key] = now
                if device.product is None:
                    continue
                unique.add(key)
                device_dict = device.__dict__
                device_dict["version"] = (
                    None if device_dict["version"] is None else ".".join(str(v) for v in device_dict["version"])
                )
                await formatter.emit(device_dict)

                if max_devices is not None and len(unique) >= max_devices:
                    break


@app.callback()
def scan_callback(
    ctx: typer.Context,
    timeout: float | None = typer.Option(
        None,
        "--timeout",
        min=0.0,
        help="Stop scanning after N seconds. Overrides --max-devices if both are set.",
    ),
    refresh: float | None = typer.Option(
        None,
        "--refresh",
        min=0.0,
        help=(
            "Suppress repeat sightings of the same device within N seconds. "
            "Default: infinity (each device is printed at most once)."
        ),
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help=(
            "Print results as a JSON array. Defaults --max-devices to "
            f"{_JSON_DEFAULT_MAX_DEVICES} so the array has a bounded size when no stop condition is set."
        ),
    ),
    max_devices: int | None = typer.Option(
        None,
        "--max-devices",
        min=1,
        help=(
            "Stop after N unique devices are seen. Ignored when --timeout is set. "
            "When unset: human output runs until Ctrl-C; --json output runs until "
            f"the internal default of {_JSON_DEFAULT_MAX_DEVICES} unique device(s) is seen."
        ),
        show_default=False,
    ),
) -> None:
    effective_max = _JSON_DEFAULT_MAX_DEVICES if (json_output and max_devices is None) else max_devices
    effective_refresh = math.inf if refresh is None else refresh
    has_stop = timeout is not None or max_devices is not None

    if not has_stop:
        if json_output:
            print(
                f"# no stop condition set: --json will terminate after the default "
                f"--max-devices={_JSON_DEFAULT_MAX_DEVICES} unique device(s); "
                "Ctrl-C terminates early",
                file=sys.stderr,
            )
        else:
            print(
                "# no stop condition set: scanning continues until Ctrl-C is pressed",
                file=sys.stderr,
            )

    run(
        _async_scan,
        timeout=timeout,
        refresh=effective_refresh,
        json_output=json_output,
        max_devices=effective_max,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


__all__ = ["app"]
