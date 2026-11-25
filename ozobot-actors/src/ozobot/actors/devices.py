def _try_import_ari() -> type | None:
    try:
        from ozobot.ari import Ari
    except ModuleNotFoundError:
        return None

    return Ari


def _try_import_evo() -> type | None:
    try:
        from ozobot.evo import Evo
    except ModuleNotFoundError:
        return None

    return Evo


def _try_import_ora() -> type | None:
    try:
        from ozobot.ora.driver.web import OraWebDriver
    except ModuleNotFoundError:
        return None

    return OraWebDriver


def _create_compatible_devices() -> set[tuple[type, str]]:
    # FIXME: refactor this to use names stored as class variables instead (e.g., Evo.model_name, Ari.model_name, ...)
    compatible_devices = set()

    if ari := _try_import_ari():
        compatible_devices.add((ari, "Ari"))

    if evo := _try_import_evo():
        compatible_devices.add((evo, "Evo"))

    if ora := _try_import_ora():
        compatible_devices.add((ora, "Ora"))

    return compatible_devices


compatible_devices = _create_compatible_devices()
