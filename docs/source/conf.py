# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys

# sys.path.insert(0, os.path.abspath("../../../report_creator"))
sys.path.append(os.path.abspath(".."))
sys.path.append(os.path.abspath("../../../report_creator"))


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
    "sphinxcontrib.video",
]
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_copy_source = False
html_show_sourcelink = False

html_theme = "sphinx_book_theme"

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

mermaid_params = ["--theme", "forest"]

html_title = "Report Creator"

html_theme_options = {
    "repository_url": "https://github.com/darenr/report_creator",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_download_button": True,
    "path_to_docs": "docs/source",
    "show_navbar_depth": 2,
    "home_page_in_toc": True,
}
