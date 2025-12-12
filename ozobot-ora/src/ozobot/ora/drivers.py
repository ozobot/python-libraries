"""
Dummy module that reexports `driver` package for backward compatibility.

TODO: Remove when the public async api is finished.
"""

from ozobot.ora.driver import get_driver

OraWebDriver = get_driver()
