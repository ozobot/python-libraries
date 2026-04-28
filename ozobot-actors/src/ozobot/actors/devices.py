from ozobot.ari import Ari
from ozobot.evo import Evo

# workaround for the editor using older release with different driver location
try:
    from ozobot.ora.driver.web import OraWebDriver
except ModuleNotFoundError:
    from ozobot.ora.drivers.browser import OraWebDriver  # type: ignore

# FIXME: refactor this to use names stored as class variables instead (e.g., Evo.model_name, Ari.model_name, ...)
compatible_devices = {
    (Ari, "Ari"),
    (Evo, "Evo"),
    (OraWebDriver, "Ora"),
}
