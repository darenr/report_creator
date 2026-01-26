import glob
import os
import sys

for path in ["./", "../", "../../", "../../../"]:
    candidate = f"{path}report_creator"
    if candidate in glob.glob(f"{path}*"):
        sys.path.append(candidate)
        break

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


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
    "sphinx_tabs.tabs",
    "myst_parser",
]

myst_enable_extensions = [
    "amsmath",
    "attrs_inline",
    "attrs_block",
    "colon_fence",
    "deflist",
    "dollarmath",
    "fieldlist",
    "html_admonition",
    "html_image",
    "replacements",
    "smartquotes",
    "strikethrough",
    "substitution",
    "tasklist",
]

# Copy button settings
copybutton_prompt_text = "$ "  # for bash prompts
copybutton_prompt_is_regexp = False
copybutton_remove_prompts = True
copybutton_line_continuation_character = "\\"

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
