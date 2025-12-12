import os
import sys

sys.path.insert(0, os.path.abspath("../src"))

from ozobot.ora.version import version  # type: ignore

split_version = version.split(".")
raw_version = ".".join(split_version[:3])

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Ozobot ORA API"
copyright = "2024, Ozo Edu, Inc."
author = "Ozo Edu, Inc."
release = version
version = raw_version

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx_rtd_theme",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]


# -- Options for autodoc -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
autodoc_type_aliases = {
    "domains.SpeedDomain": "SpeedDomain",
    "domains.AccelerationDomain": "AccelerationDomain",
    "domains.JerkDomain": "JerkDomain",
    "domains.AngularSpeedDomain": "AngularSpeedDomain",
    "domains.AngularAccelerationDomain": "AngularAccelerationDomain",
    "domains.AngularJerkDomain": "AngularJerkDomain",
}
