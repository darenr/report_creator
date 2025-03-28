import base64
import functools
import logging
import mimetypes
import os
import random
import time
import uuid
from html.parser import HTMLParser
from typing import Optional
from urllib.parse import unquote, urlparse

import emoji
import humanize
import requests

from .theming import report_creator_colors

logger = logging.getLogger("report_creator")


def _generate_anchor_id(text: str) -> str:
    return uuid.uuid5(uuid.NAMESPACE_DNS, text).hex


def _is_number(x):
    try:
        float(x)
        return True
    except ValueError:
        return False


def _check_html_tags_are_closed(html_content: str):
    """Checks if any HTML tags are closed in the given string.

    Args:
        html_content (str): The HTML content to be checked.

    Returns:
        tuple[bool, Optional[list[str]]]: A tuple containing a boolean value indicating if all tags are closed and a list of tags that are not closed.
    """

    class HTMLValidator(HTMLParser):
        def __init__(self):
            super().__init__()
            self.stack = []  # To keep track of opened tags

        def handle_starttag(self, tag, _):
            self.stack.append(tag)  # Add the tag to the stack when it opens

        def handle_endtag(self, tag):
            if self.stack and self.stack[-1] == tag:
                self.stack.pop()  # Remove the tag from the stack when it closes
            else:
                logger.error(f"Unexpected closing tag {tag} or tag not opened.")

        def validate_html(self, html):
            self.feed(html)
            if self.stack:
                return (False, self.stack)  # Some tags are not closed
            else:
                return (True, None)

    return HTMLValidator().validate_html(html_content)


def _ellipsis_url(url, max_length=45):
    """Truncates a URL to a given maximum length, adding an ellipsis in the middle."""

    if len(url) <= max_length:
        return url

    # Calculate the length of each part of the URL
    start_length = max_length // 2 - 3  # Leave room for the ellipsis
    end_length = max_length - start_length - 3

    return f"{url[:start_length]}...{url[-end_length:]}"


def _gfm_markdown_to_html(text: str) -> str:
    """
    Converts markdown text to HTML.

    Args:
        text (str): The markdown text to be converted.

    Returns:
        str: The converted HTML string.
    """

    import mistune

    def emojis(md) -> None:
        # https://www.webfx.com/tools/emoji-cheat-sheet/
        INLINE_EMOJI_PATTERN = r":[A-Za-z0-9._’()_-]+:"

        def parse_inline_emoji_icon(inline, m, state) -> int:
            state.append_token(
                {
                    "type": "emoji_icon_ref",
                    "attrs": {"emoji_str": m.group(0)},
                }
            )
            return m.end()

        def render_inline_emoji_icon(renderer, emoji_str: str) -> str:
            return emoji.emojize(emoji_str, variant="emoji_type", language="en")

        md.inline.register("emojis", INLINE_EMOJI_PATTERN, parse_inline_emoji_icon)
        if md.renderer and md.renderer.NAME == "html":
            md.renderer.register("emoji_icon_ref", render_inline_emoji_icon)

    class HighlightRenderer(mistune.HTMLRenderer):
        def block_html(self, html: str) -> str:
            if html.strip().startswith("<script") and html.strip().endswith("</script>"):
                logging.info("Blocking script tag found in Markdown content.")
                return "<!-- blocked script tag - bad human! -->"  # block script tags
            return html

        def block_code(self, code: str, info: Optional[str] = None) -> str:
            if info is None:
                info = "plaintext"

            if info == "mermaid":
                # Replace the code block with a div for Mermaid diagrams
                return f"<div class='mermaid include_mermaid'>{code}</div>"
            else:
                # markup code in markdown for highlight.js
                return (
                    f"<div class='codehilite code-block'><pre><code class='language-{info}'>"
                    + mistune.escape(code)
                    + "</code></pre></div>"
                )

    return mistune.create_markdown(
        renderer=HighlightRenderer(escape=False),
        escape=False,
        hard_wrap=False,
        plugins=[
            "task_lists",
            "def_list",
            "math",
            "table",
            "strikethrough",
            "footnotes",
            "url",
            "spoiler",
            emojis,
        ],
    )(text)


def _time_it(func):
    """A decorator to time a function"""

    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        start_time = time.perf_counter()
        value = func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        class_name = args[0].__class__.__name__ if args else None  # Get class name

        logger.debug(f"[{class_name}::{func.__name__!r}] - {run_time:.4f} secs")
        return value

    return wrapper_timer


def _strip_whitespace(func):
    """
    A decorator to strip whitespace from the output of a function.

    Args:
        func (callable): The function to be decorated.

    Returns:
        callable: The decorated function.

    """

    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if isinstance(result, str):
            return result.strip()
        else:
            return result

    return wrapper


def create_color_value_sensitive_mapping(
    values,
    error_keywords=["error", "fail", "failed", "404"],  # noqa: B006
):
    """
    Creates a color mapping for Plotly based on values and error keywords.

    Args:
        values (list): List of values (strings or numbers).
        error_keywords (list): List of keywords indicating error/failure.

    Returns:
        list: List of colors corresponding to each value.
    """
    colors = []
    for value in values:
        if isinstance(value, str):
            value_lower = value.lower()
            if any(keyword in value_lower for keyword in error_keywords):
                colors.append("red")  # Or "orange" for a less harsh color
            else:
                colors.append(
                    "green"
                )  # Or another positive color like "lightgreen", "royalblue"
        elif isinstance(value, (int, float)):
            if value < 0:  # Example: negative numbers can be errors
                colors.append("red")
            else:
                colors.append("green")
        else:
            colors.append("gray")  # Default color for unknown types
    return colors


def _random_light_color_generator(word: str) -> tuple[str, str]:
    """returns auto selected light background_color

    Args:
        word (str): word to generate color for
    """
    random.seed(word.encode())  # must be deterministic

    def lighten_color(hex_color, factor=0.64):
        """Lightens a hex color by a given factor (0.0 to 1.0)."""
        hex_color = hex_color.lstrip("#")
        rgb = [int(hex_color[i : i + 2], 16) for i in (0, 2, 4)]
        light_rgb = [int((1 - factor) * c + factor * 255) for c in rgb]
        return "#{:02x}{:02x}{:02x}".format(*light_rgb)

    return lighten_color(random.choice(report_creator_colors)), "black"


def _random_color_generator(word: str) -> tuple[str, str]:
    """returns auto selected (background_color, text_color) as tuple

    Args:
        word (str): word to generate color for
    """
    random.seed(f"-{word}-".encode())  # must be deterministic
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)

    background_color = f"#{r:02x}{g:02x}{b:02x}"
    text_color = "black" if (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.5 else "white"

    return background_color, text_color


def _get_url_root(url):
    # Parse the URL into components
    parsed_url = urlparse(url)

    # Reconstruct the root URL (scheme + netloc)
    root_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

    return root_url


def _convert_filepath_to_datauri(filepath: str) -> str:
    """convert local file to base64 datauri

    Args:
        filepath (str): path to the image
    """

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Image file not found: {filepath}")

    with open(filepath, "rb") as image_file:
        # Detect the MIME type of the file from the URL
        mime_type, _ = mimetypes.guess_type(filepath)
        logger.info(f"{filepath=} mime_type: {mime_type}")

        # Encode the content as base64
        base64_content = base64.b64encode(image_file.read()).decode("utf-8")

        logger.info(
            f"Image: ({_ellipsis_url(filepath)}) - {mime_type}, {len(base64_content)} bytes"
        )

        # Create the Data URI
        data_uri = f"data:{mime_type};base64,{base64_content}"

    return data_uri


def _convert_imgurl_to_datauri(image_url: str) -> str:
    """convert url to base64 datauri

    Args:
        image_url (str): url of the image
    """

    headers = {"Referer": _get_url_root(image_url)}

    response = requests.get(image_url, headers=headers)
    response.raise_for_status()  # Check if the download was successful

    # Detect the MIME type of the file from the URL
    mime_type, _ = mimetypes.guess_type(image_url)

    # Encode the content as base64
    base64_content = base64.b64encode(response.content).decode("utf-8")

    logger.info(
        f"Image: {mime_type}, {humanize.naturalsize(len(base64_content))} ({unquote(image_url)})"
    )

    # Create the Data URI
    data_uri = f"data:{mime_type};base64,{base64_content}"

    return data_uri
