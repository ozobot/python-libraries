# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys
from pathlib import Path

sys.path.append(str(Path("_ext").resolve()))

project = "Ozobot Python SDK"
copyright = "2026, Ozo EDU, Inc."
author = "Ondrej Novak"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx_external_toc",
    "sphinx.ext.autodoc",
    "autodoc_enumflag",
    "sphinx_tabs.tabs",
]

templates_path = ["_templates"]
exclude_patterns: list[str] = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_css_files = [
    "custom.css",
]
html_theme_options = {
    "style_external_links": True,
}

# -- Options for autodoc -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
autodoc_type_aliases = {
    # ora type aliases
    "domains.SpeedDomain": "SpeedDomain",
    "domains.AccelerationDomain": "AccelerationDomain",
    "domains.JerkDomain": "JerkDomain",
    "domains.AngularSpeedDomain": "AngularSpeedDomain",
    "domains.AngularAccelerationDomain": "AngularAccelerationDomain",
    "domains.AngularJerkDomain": "AngularJerkDomain",
}

autodoc_mock_imports = [
    "ozobot.ora.driver",  # ora.simple loads unimplemented native driver on import
]
