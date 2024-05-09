import base64
import logging
import random
from html.parser import HTMLParser
from typing import Tuple

logging.basicConfig(level=logging.INFO)


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
                logging.error(f"Unexpected closing tag {tag} or tag not opened.")

        def validate_html(self, html):
            self.feed(html)
            if self.stack:
                return (False, self.stack)  # Some tags are not closed
            else:
                return (True, None)

    return HTMLValidator().validate_html(html_content)


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
            return (
                "<div class='codehilite'><pre><code>"
                + mistune.escape(code)
                + "</code></pre></div>"
            )

    return mistune.create_markdown(
        renderer=HighlightRenderer(), plugins=["task_lists", "def_list", "math"]
    )(text)


def strip_whitespace(func):
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


def _random_color_generator(word: str) -> Tuple[str, str]:
    """returns auto selected (background_color, text_color) as tuple

    Args:
        word (str): word to generate color for
    """
    random.seed(word.encode())  # must be deterministic
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)

    background_color = f"#{r:02x}{g:02x}{b:02x}"
    text_color = "black" if (0.299 * r + 0.587 * g + 0.114 * b) / 255 > 0.5 else "white"

    return background_color, text_color


def _convert_imgurl_to_datauri(imgurl: str) -> str:
    """convert url to base64 datauri

    Args:
        imgurl (str): url of the image
    """
    from io import BytesIO

    import requests
    from PIL import Image

    response = requests.get(imgurl)
    img = Image.open(BytesIO(response.content))
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue())
    return f"data:image/jpeg;base64,{img_str.decode('utf-8')}"
