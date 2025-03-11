import html
import json
import logging
import re
import textwrap
from typing import Optional, Union

import yaml
from markupsafe import escape

from ..utilities import (
    _check_html_tags_are_closed,
    _generate_anchor_id,
    _gfm_markdown_to_html,
    _random_color_generator,
    _strip_whitespace,
)
from .base import Base

# Configure logging
logger = logging.getLogger("report_creator")


class Markdown(Base):
    """
    Embeds Markdown-formatted text within the report, with optional styling and borders.

    The `Markdown` component allows you to include rich text content in your report
    using Markdown syntax. It supports Github Falvored Markdown formatting and provides
    options for adding custom CSS styles and borders.

    Args:
        text (str): The Markdown-formatted text to be rendered. This string will be
            processed and displayed as formatted text in the report.
        label (Optional[str], optional): An optional label or heading for the
            Markdown section. If provided, a caption with a linkable anchor will
            be displayed above the Markdown content. Defaults to None.
        extra_css (Optional[str], optional): Additional inline CSS styles to be
            applied to the Markdown content. This allows for custom styling
            beyond the basic Markdown rendering. Defaults to None.
        bordered (bool, optional): If True, the Markdown content will be
            rendered within a bordered container, providing a visual
            separation from surrounding content. Defaults to False.
    """

    def __init__(
        self,
        text: str,
        *,
        label: Optional[str] = None,
        extra_css: Optional[str] = None,
        bordered: Optional[bool] = False,
    ):
        super().__init__(label=label)
        self.text = textwrap.dedent(text)
        self.extra_css = extra_css or ""
        self.bordered = bordered

        logger.info(f"Markdown: {len(self.text)} characters")

    @_strip_whitespace
    def to_html(self) -> str:
        border = "round-bordered" if self.bordered else ""
        html_output = f"<div class='markdown-wrapper include_hljs {border}'>"
        if self.label:
            html_output += f"<report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</a></report-caption>"

        html_output += f'<div style="{self.extra_css}">' if self.extra_css else "<div>"
        html_output += _gfm_markdown_to_html(self.text)
        html_output += "</div>"
        html_output += "</div>"

        return html_output


class Text(Markdown):
    """Alias for Markdown component."""

    pass


class Html(Base):
    """
    Embeds raw HTML content, optionally with inline CSS styling, into the report.

    The `Html` component provides a way to include arbitrary HTML markup directly
    within a report. This is useful for embedding custom web elements, adding
    specialized formatting, or integrating content from external sources that
    provide HTML snippets.

    Args:
        html (str): The raw HTML content to be embedded. This can include any
            valid HTML tags and content.
        css (Optional[str], optional): Optional inline CSS styles to be applied
            to the HTML content. If provided, these styles will be wrapped in
            `<style>` tags and inserted before the HTML content. Defaults to None.
        label (Optional[str], optional): An optional label for the HTML component.
            If provided, a caption with a linkable anchor will be displayed above
            the HTML content in the rendered report. Defaults to None.
        bordered (Optional[bool], optional): If True, the HTML content will be
            rendered within a bordered container. Defaults to False.

    Raises:
        ValueError: If the provided HTML content contains unclosed tags.
    """

    def __init__(
        self,
        html: str,
        *,
        css: Optional[str] = None,
        label: Optional[str] = None,
        bordered: Optional[bool] = False,
    ):
        super().__init__(label=label)
        self.html = html
        self.css = css
        self.bordered = bordered
        status, errors = _check_html_tags_are_closed(html)
        if not status:
            raise ValueError(
                f"HTML component with label {self.label}, tags are not closed: {', '.join(errors)}"
            )
        logger.info(f"HTML: {len(self.html)} characters")

    @_strip_whitespace
    def to_html(self) -> str:
        border = "round-bordered" if self.bordered else ""

        html_output = f"<style>{self.css}</style>" if self.css else ""
        if self.label:
            html_output += f"<report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</a></report-caption>"
        html_output += f'<div class="{border}">' + self.html + "</div>"
        return html_output


class Unformatted(Base):
    """
    Displays data as text without any specific formatting or structure.

    The `Unformatted` component renders raw text or data directly within
    the report without applying any special HTML formatting or styling.
    This is useful for displaying data that is not intended to be part
    of the main content flow, such as debug output, code snippets, or
    raw data dumps.

    Args:
        text (str): The raw text or data to be displayed as-is within
            the report. This can be any string or data type that you
            want to present without modification.
        label (Optional[str], optional): An optional label for the
            unformatted data. If provided, a caption with a linkable
            anchor will be displayed above the data. Defaults to None.
    """

    def __init__(self, text: str, *, label: Optional[str] = None):
        super().__init__(label=label)
        self.text = text

    @_strip_whitespace
    def to_html(self) -> str:
        formatted_text = f"<pre><code>{self.text.strip()}</code></pre>"

        if self.label:
            return f"""<report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</a></report-caption><div>{formatted_text}</div>"""
        else:
            return f"""<div>{formatted_text}</div>"""


class Language(Base):
    """
    Base class for components that display code or text in a specific programming language.
    """

    def __init__(
        self,
        text: str,
        language: str,
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        super().__init__(label=label)
        self.text = text
        self.language = language.lower()
        self.scroll_long_content = scroll_long_content
        logger.info(f"{language}: {len(self.text)} characters, {scroll_long_content=}")

        if not self.language:
            assert self.language, "Language must be specified"
        else:
            assert self.language in [
                "java",
                "python",
                "prolog",
                "shell",
                "sql",
                "yaml",
                "json",
                "plaintext",
            ], f"Language {self.language} not supported"

    @_strip_whitespace
    def to_html(self) -> str:
        formatted_text = f"<pre><code class='language-{self.language} syntax-color'>\n{self.text.strip()}</code></pre>"
        if self.label:
            label_background, label_text_color = _random_color_generator(self.language)
            label_span = f"""
                <span class="code-block-label" style="background-color: {label_background}; color:{label_text_color};">
                    {self.label}
                </span>
            """
        else:
            label_span = ""
        return f"""
                <div class="code-block include_hljs">
                    {label_span}{formatted_text}
                </div>
        """


class Python(Language):
    """
    Displays the code within the report.

    The `Python` component allows you to add Python code that will be inserted
    into the report with code formatting applied.

    Args:
        code (str): The Python code or text to be displayed.
        label (Optional[str], optional): An optional label for the
            prolog. This label does not appear in the rendered
            report but can be helpful for internal identification
            or debugging purposes. Defaults to None.
    """

    def __init__(
        self,
        code: str,
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        super().__init__(
            escape(textwrap.dedent(code)),
            "python",
            scroll_long_content=scroll_long_content,
            label=label,
        )


class Prolog(Language):
    """
    Displays the code within the report.

    The `Prolog` component allows you to add Prolog code that will be inserted
    into the report with code formatting applied.

    Args:
        code (str): The Prolog code or text to be displayed.
        label (Optional[str], optional): An optional label for the
            prolog. This label does not appear in the rendered
            report but can be helpful for internal identification
            or debugging purposes. Defaults to None.

    Attributes:
        html (str): The raw HTML content to be inserted.
        label (Optional[str]): The optional label of the prolog.

    Methods:
        to_html() -> str: Generates the HTML representation of the prolog.
    """

    def __init__(
        self,
        code: str,
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        super().__init__(
            escape(code), "prolog", scroll_long_content=scroll_long_content, label=label
        )


class Shell(Language):
    """
    Displays the code within the report.

    The `Shell` component allows you to add `sh` code that will be inserted
    into the report with code formatting applied.

    Args:
        code (str): The Shell code or text to be displayed.
        label (Optional[str], optional): An optional label for the
            prolog. This label does not appear in the rendered
            report but can be helpful for internal identification
            or debugging purposes. Defaults to None.
    """

    def __init__(
        self,
        code: str,
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        super().__init__(
            escape(code), "shell", scroll_long_content=scroll_long_content, label=label
        )


# Alias for Shell
class Sh(Shell):
    pass


class Bash(Shell):
    pass


class Java(Language):
    """
    Displays the code within the report.

    The `Java` component allows you to add Java code that will be inserted
    into the report with code formatting applied.

    Args:
        code (str): The Prolog code or text to be displayed.
        label (Optional[str], optional): An optional label for the
            prolog. This label does not appear in the rendered
            report but can be helpful for internal identification
            or debugging purposes. Defaults to None.
    """

    def __init__(
        self,
        code: str,
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        super().__init__(
            escape(code), "java", scroll_long_content=scroll_long_content, label=label
        )


class Sql(Language):
    """
    Displays the code within the report.

    The `Sql` component allows you to add SQL code that will be inserted
    into the report with code formatting applied.

    Args:
        code (str): The SQL query to be rendered
        scroll_long_content (Optional[bool], optional): If True, and the output is long,
            the output will be rendered within a scrollable element. If false it will
            render in place, which may make the report very long. This can be used to
            help manage the length of the report. Defaults to False.
        prettify (Optional[bool], optional): If True, the SQL query will be formatted
            before execution. Defaults to False.
        label (Optional[str], optional): An optional label for the SQL query
            output. If provided, a caption with a linkable anchor will be
            displayed above the output. Defaults to None.

    Raises:
        Exception: If any error occurs during database connection or query execution.
    """

    @staticmethod
    def format_sql(sql: str) -> str:
        BLOCK_STATEMENTS = [
            "create.*?table",  # regex for all variants, e.g. CREATE OR REPLACE TABLE
            "create.*?view",  # regex for all variants, e.g. CREATE OR REPLACE VIEW
            "select distinct",
            "select",
            "from",
            "left join",
            "inner join",
            "outer join",
            "right join",
            "union",
            "on",
            "where",
            "group by",
            "order by",
            "asc",
            "desc",
            "limit",
            "offset",
            "insert.*?into",
            "update",
            "set",
            "delete",
            "drop",
            "alter",
            "add",
            "modify",
            "rename",
            "truncate",
            "begin",
            "commit",
            "rollback",
            "grant",
            "revoke",
        ]
        RESERVED_WORDS = ["as"]

        sql = re.sub(r"(?<!['\"]),\s*(?!['\"])", ",\n\t", sql, flags=re.DOTALL)

        for reserved_word in RESERVED_WORDS:
            sql = re.sub(
                rf"(?<!['\"]){reserved_word}(?!['\"])",
                reserved_word.upper(),
                sql,
                flags=re.DOTALL,
            )

        def format_block_statement(matchobj):
            return f"\n{matchobj.group(0).strip()}\n\t".upper()

        for statement in BLOCK_STATEMENTS:
            sql = re.sub(
                rf"(?<!['\"])^|\s+{statement}\s+|$(?!['\"])",
                format_block_statement,  # add newline before each statement, upper case
                sql,
                flags=re.IGNORECASE | re.DOTALL,
            )
        return sql

    def __init__(
        self,
        code: str,
        *,
        scroll_long_content: Optional[bool] = False,
        prettify: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        super().__init__(
            Sql.format_sql(code) if prettify else code,
            "sql",
            scroll_long_content=scroll_long_content,
            label=label,
        )


class Yaml(Language):
    """
    Displays formatted YAML content within the report.

    The `Yaml` component is designed to embed YAML-formatted data
    directly into the report, presenting it in a structured and
    human-readable way. It's useful for displaying configuration files,
    data structures, or any other information that is naturally
    represented in YAML format.

    Args:
        data (Union[dict, list, str]): The YAML data to be displayed.
            This can be either a Python dictionary (which will be
            converted to YAML), a list, or a string containing valid
            YAML content.
        scroll_long_content (Optional[bool], optional): If True, and the output is long,
            the output will be rendered within a scrollable element. If false it will
            render in place, which may make the report very long. This can be used to
            help manage the length of the report. Defaults to False.
        label (Optional[str], optional): An optional label or heading
            for the YAML content. If provided, a caption with a linkable
            anchor will be displayed above the YAML data.
            Defaults to None.

    Raises:
        ValueError: If the data type is not valid for the Yaml component.
        yaml.YAMLError: If the provided YAML data is invalid or cannot be parsed.
    """

    def __init__(
        self,
        data: Union[str, dict, list],
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        if isinstance(data, (dict, list)):
            content = yaml.dump(data, indent=2, Dumper=yaml.SafeDumper)
        elif isinstance(data, str):
            content = yaml.dump(
                yaml.load(data, Loader=yaml.SafeLoader), indent=2, Dumper=yaml.SafeDumper
            )
        else:
            raise ValueError("Invalid data type for Yaml component")

        super().__init__(
            content,
            "yaml",
            scroll_long_content=scroll_long_content,
            label=label,
        )


class Json(Language):
    """
    Displays formatted JSON content within the report.

    The `Json` component is designed to embed JSON-formatted data
    directly into the report, presenting it in a structured and
    human-readable way. It's useful for displaying configuration data,
    API responses, or any other information that is naturally
    represented in JSON format.

    Args:
        data (Union[dict, list, str]): The JSON data to be displayed.
            This can be either a Python dictionary (which will be
            converted to JSON) or a string containing valid JSON content.
        scroll_long_content (bool, optional): If True and the content is long, it will be
            rendered within a scrollable element. If false it will
            render in place, which may make the report very long. This can be used to help
            manage the length of the report. Defaults to False.
        label (Optional[str], optional): An optional label or heading
            for the JSON content. If provided, a caption with a linkable
            anchor will be displayed above the JSON data.
            Defaults to None.

    Methods:
        to_html() -> str: Generates the HTML representation of the formatted JSON content.
    """

    def __init__(
        self,
        data: Union[dict, list, str],
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        class HTMLEscapingEncoder(json.JSONEncoder):
            def encode(self, obj):
                obj = json.loads(super().encode(obj))  # Ensure JSON structure
                if isinstance(obj, dict):
                    obj = {
                        k: html.escape(v) if isinstance(v, str) else v for k, v in obj.items()
                    }
                return super().encode(obj)

        if isinstance(data, (dict, list)):
            content = json.dumps(data, indent=2, cls=HTMLEscapingEncoder)
        elif isinstance(data, str):
            content = json.dumps(json.loads(data), indent=2, cls=HTMLEscapingEncoder)
        else:
            raise ValueError("Invalid data type for JSON component")

        super().__init__(
            content,
            "json",
            scroll_long_content=scroll_long_content,
            label=label,
        )


class Plaintext(Language):
    """
    Displays text content with minimal formatting within the report.

    The `Plaintext` component is used to embed text content into the
    report with basic, pre-defined styling. Unlike the `Markdown`
    component, it does not support Markdown formatting, but it does
    provide a simple way to display blocks of text in a consistent
    and readable way.

    Args:
        text (str): The text content to be displayed. This should be a
            string containing the text you want to include in the report.
        scroll_long_content (bool, optional): If True and the content is long, it will be
            rendered within a scrollable element. If false it will
            render in place, which may make the report very long. This can be used to help
            manage the length of the report. Defaults to False.
        label (Optional[str], optional): An optional label or heading
            for the plaintext content. If provided, a caption with a
            linkable anchor will be displayed above the text.
            Defaults to None.
    """

    def __init__(
        self,
        text: str,
        *,
        scroll_long_content: Optional[bool] = False,
        label: Optional[str] = None,
    ):
        super().__init__(
            text,
            "plaintext",
            scroll_long_content=scroll_long_content,
            label=label,
        )
