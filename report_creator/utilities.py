import base64
import logging
import mimetypes
import random
import uuid
from html.parser import HTMLParser
from typing import Tuple
from urllib.parse import urlparse

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
        Tuple[bool, Optional[List[str]]]: A tuple containing a boolean value indicating if all tags are closed and a list of tags that are not closed.
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


def _markdown_to_html(text: str) -> str:
    """
    Converts markdown text to HTML.

    Args:
        text (str): The markdown text to be converted.

    Returns:
        str: The converted HTML string.
    """
    import mistune

    class HighlightRenderer(mistune.HTMLRenderer):
        # need to wrap code/pre inside a div that is styled with codehilite at rendertime
        def block_code(
            self, code, **_
        ):  # **_ gathers unused key-value pairs (to avoid lint warning of unused param(s))
            return "<div class='codehilite'><pre><code>" + mistune.escape(code) + "</code></pre></div>"

    escape_html = False
    return mistune.create_markdown(
        renderer=HighlightRenderer(escape=escape_html),
        escape=escape_html,
        hard_wrap=False,
        plugins=["task_lists", "def_list", "math", "table", "strikethrough", "footnotes", "url", "spoiler"],
    )(text)


def _strip_whitespace(func):
    """
    A decorator that strips leading and trailing whitespace from the result of a function.

    Args:
        func: The function to be decorated.

    Returns:
        The decorated function.

    """

    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        if isinstance(result, str):
            return result.strip()
        else:
            return result

    return wrapper


def _random_light_color_generator(word: str) -> Tuple[str, str]:
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


def _random_color_generator(word: str) -> Tuple[str, str]:
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
    """convert file path to base64 datauri

    Args:
        imgurl (str): url of the image
    """

    with open(filepath, "rb") as image_file:
        # Detect the MIME type of the file from the URL
        mime_type, _ = mimetypes.guess_type(filepath)
        logger.info(f"{filepath=} mime_type: {mime_type}")

        # Encode the content as base64
        base64_content = base64.b64encode(image_file.read()).decode("utf-8")

        logger.info(f"Image: ({_ellipsis_url(filepath)}) - {mime_type}, {len(base64_content)} bytes")

        # Create the Data URI
        data_uri = f"data:{mime_type};base64,{base64_content}"

    return data_uri


def _convert_imgurl_to_datauri(imgurl: str) -> str:
    """convert url to base64 datauri

    Args:
        imgurl (str): url of the image
    """

    headers = {"Referer": _get_url_root(imgurl)}

    response = requests.get(imgurl, headers=headers)
    response.raise_for_status()  # Check if the download was successful

    # Detect the MIME type of the file from the URL
    mime_type, _ = mimetypes.guess_type(imgurl)

    # Encode the content as base64
    base64_content = base64.b64encode(response.content).decode("utf-8")

    logger.info(f"Image: ({_ellipsis_url(imgurl)}) - {mime_type}, {len(base64_content)} bytes")

    # Create the Data URI
    data_uri = f"data:{mime_type};base64,{base64_content}"

    return data_uri
