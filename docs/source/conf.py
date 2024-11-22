# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

add_path = os.path.abspath("../../../report_creator")
sys.path.insert(0, add_path)


project = "report_creator"
copyright = "2025, Daren Race"
author = "Daren Race"

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.doctest",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "sphinxcontrib.mermaid",
    "sphinx.ext.inheritance_diagram",
]
templates_path = ["_templates"]
exclude_patterns = []

html_copy_source = False
html_show_sourcelink = False

html_theme = "sphinx_book_theme"

mermaid_params = ["--theme", "forest"]

html_logo = "https://raw.githubusercontent.com/darenr/report_creator/refs/heads/main/rc-logo.png"


html_theme_options = {
    "repository_url": "https://github.com/darenr/report_creator",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_download_button": True,
    "path_to_docs": "docs/source",
    "show_navbar_depth": 2,
    "home_page_in_toc": True,
}
