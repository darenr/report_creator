# Standard library imports
import base64
import functools
import mimetypes
import os
import random
import time
import uuid
from collections.abc import Sequence  # Added Any, tuple
from html.parser import HTMLParser
from typing import Any, Optional, Union
from urllib.parse import unquote, urlparse

# Third-party imports
import emoji  # For Markdown emoji processing
import humanize  # For human-readable sizes
import requests  # For fetching images from URLs
import requests.exceptions  # For specific request error handling

# Loguru logger
from loguru import logger

# Internal imports
from .theming import report_creator_colors  # For deterministic color generation

# Default length for URL ellipsis
DEFAULT_ELLIPSIS_LENGTH = 45

# Module-level Random instance for deterministic color generation based on seeds.
# This ensures that repeated calls with the same seed word produce the same color,
# but different seed words can produce different colors.
_color_rng = random.Random()


def _generate_anchor_id(text: str) -> str:
    """
    Generates a deterministic UUID (version 5) based anchor ID from a text string.

    This creates a unique and stable identifier suitable for HTML anchors,
    ensuring that the same input text always results in the same anchor ID.
    UUID5 uses SHA-1 hashing with a namespace (DNS namespace is used here).
    The input `text` is automatically converted to `str`.

    Args:
        text (str): The input string to base the anchor ID on.

    Returns:
        str: A hexadecimal string representation of the generated UUID,
             e.g., "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6".
    """
    # Using uuid.NAMESPACE_DNS ensures that the same name under this namespace
    # will always produce the same UUID. str(text) ensures input is string.
    return uuid.uuid5(uuid.NAMESPACE_DNS, str(text)).hex


def _is_number(value: Any) -> bool:
    """
    Checks if a given value can be successfully converted to a float.

    This is a utility to determine if a value has a numeric nature. It attempts
    to cast the value to `float` and catches `ValueError` (e.g., for
    non-numeric strings like "abc") and `TypeError` (e.g., for `None` or
    other types that cannot be coerced to float).

    Args:
        value (Any): The value to check.

    Returns:
        bool: True if `value` can be converted to a float, False otherwise.
    """
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def _check_html_tags_are_closed(html_content: str) -> tuple[bool, Optional[list[str]]]:
    """
    Validates if all HTML tags in a given string are properly closed.

    Uses an inner class `HTMLTagValidator` (subclass of `html.parser.HTMLParser`)
    to perform a basic check of tag nesting by tracking opening and closing tags
    on a stack. This is a simple validation and may not catch all complex HTML
    errors but is useful for finding basic unclosed tag issues.

    Args:
        html_content (str): The HTML content string to validate. The content
                            is cast to `str` before parsing.

    Returns:
        tuple[bool, Optional[list[str]]]:
            - `(True, None)` if all HTML tags are properly closed.
            - `(False, list_of_unclosed_tags)` if there are unclosed tags.
              `list_of_unclosed_tags` contains a copy of the names of the tags
              that were left open at the end of parsing, in the order they
              were opened.
    """

    class HTMLTagValidator(HTMLParser):
        """
        Internal parser class to validate HTML tag closure.
        It maintains a stack of opened tags.
        """

        def __init__(self) -> None:
            super().__init__()
            self.tag_stack: list[str] = []  # Stack to keep track of opened tags

        def handle_starttag(self, tag: str, attrs: Any) -> None:  # noqa: ARG002
            # When a start tag is encountered, push it onto the stack.
            self.tag_stack.append(tag)

        def handle_endtag(self, tag: str) -> None:
            # When an end tag is encountered:
            # If the stack is not empty and the top of the stack matches the end tag,
            # it means the tag is properly closed, so pop it from the stack.
            if self.tag_stack and self.tag_stack[-1] == tag:
                self.tag_stack.pop()
            else:
                # This case indicates a mismatched closing tag or a closing tag
                # without a corresponding opening tag that was expected.
                # For this validator's purpose (checking for unclosed tags),
                # we are more concerned about the final state of the stack.
                logger.debug(
                    f"HTML structure issue: Encountered end tag '{tag}' "
                    f"but stack top is '{self.tag_stack[-1] if self.tag_stack else 'empty'}'."
                )

        def get_validation_result(self) -> tuple[bool, Optional[list[str]]]:
            """Returns the validation result based on the final state of the stack."""
            if not self.tag_stack:
                # If the stack is empty, all opened tags were properly closed.
                return (True, None)
            else:
                # If the stack is not empty, it contains unclosed tags.
                # Return a copy of the stack to prevent external modification.
                return (False, list(self.tag_stack))

    validator = HTMLTagValidator()
    validator.feed(str(html_content))  # Ensure content is string before feeding
    return validator.get_validation_result()


def _ellipsis_url(url: str, max_length: int = DEFAULT_ELLIPSIS_LENGTH) -> str:
    """
    Truncates a URL string to a specified maximum length.

    If the URL exceeds `max_length`, an ellipsis ("...") is inserted.
    - If `max_length` is very small (less than 4 characters), the URL is
      simply truncated to `max_length`.
    - If `max_length` is small (4 to 9 characters), an ellipsis is placed at
      the end (e.g., "abc...").
    - For larger `max_length`, the ellipsis is placed in the middle.

    This is useful for displaying long URLs concisely. Input `url` is cast to `str`.

    Args:
        url (str): The URL string to truncate.
        max_length (int, optional): The maximum desired length for the
            output URL string. Defaults to `DEFAULT_ELLIPSIS_LENGTH` (45 characters).

    Returns:
        str: The original or truncated URL string.
    """
    url_str = str(url)  # Ensure input is a string

    if len(url_str) <= max_length:
        return url_str

    if max_length < 4:  # Not enough space for ellipsis + context
        return url_str[:max_length]

    if max_length < 10:  # Ellipsis at the end for moderately short lengths
        return f"{url_str[: max_length - 3]}..."

    # For longer max_length, place ellipsis in the middle
    # Reserve 3 characters for "..."
    chars_to_show = max_length - 3
    # Distribute remaining length, favoring the start slightly
    start_length = (chars_to_show + 1) // 2
    end_length = chars_to_show // 2

    # Ensure start and end lengths are non-negative (should be covered by max_length < 10 check)
    # but as a safeguard:
    start_length = max(start_length, 0)
    end_length = max(end_length, 0)

    # Ensure we don't show more than available if start_length + end_length > len(url_str)
    # This path should ideally not be hit if len(url_str) > max_length
    if start_length + end_length >= len(url_str):
        return f"{url_str[: max_length - 3]}..."

    return f"{url_str[:start_length]}...{url_str[-end_length:]}"


def _gfm_markdown_to_html(text: str) -> str:
    """
    Converts GitHub Flavored Markdown (GFM) text to HTML using `mistune`.

    This function configures `mistune` with several plugins and a custom
    renderer to provide enhanced functionality:
    -   **Emoji Support**: Converts emoji cheat sheet codes (e.g., `:smile:`) to
        Unicode characters using the `emoji` library.
    -   **Custom `HighlightRenderer`**:
        -   **Script Tag Blocking**: Prevents direct embedding of `<script>` tags
            from Markdown to mitigate XSS risks. Such tags are replaced with a
            comment.
        -   **Code Block Highlighting**: Wraps standard code blocks (e.g., ```python ... ```)
            in HTML suitable for syntax highlighting by Highlight.js. The language
            specified in Markdown (e.g., "python") is used to set the class
            `language-<info>`.
        -   **Mermaid Diagram Handling**: Identifies code blocks marked with "mermaid"
            (i.e., ```mermaid ... ```) and wraps them in a `<div>` with class
            `mermaid include_mermaid`, which is then processed by Mermaid.js in the browser.
    -   **Standard GFM Plugins**: Enables `mistune` plugins for tables, task lists
        (e.g., `- [x] task`), definition lists, math (LaTeX-style), strikethrough,
        footnotes, URL auto-linking, and spoilers.

    Args:
        text (str): The Markdown string to convert.

    Returns:
        str: The HTML representation of the input Markdown.
             The `mistune` renderer is configured with `escape=False` because
             escaping is handled selectively (e.g., within `block_code` for
             non-Mermaid code).

    Dependencies:
        - `mistune`: For Markdown parsing and rendering.
        - `emoji`: For converting emoji codes to characters.
    """
    import mistune  # Lazily import mistune as it's a core dependency for this function.

    # Plugin for emoji support
    def emojis_plugin(md: mistune.Markdown) -> None:
        """Mistune plugin to parse and render emoji codes like :smile:."""
        # Regex for common emoji cheat sheet codes
        INLINE_EMOJI_PATTERN = r":[A-Za-z0-9+._’()_-]+:"

        def parse_inline_emoji(
            inline: mistune.InlineParser, match: Any, state: mistune.InlineState
        ) -> int:
            """Parses an emoji token."""
            state.append_token({"type": "emoji_text", "attrs": {"text": match.group(0)}})
            return match.end()

        def render_html_emoji(text: str) -> str:
            """Renders the emoji token to its Unicode character."""
            return emoji.emojize(text, variant="emoji_type", language="en")

        md.inline.register("emoji", INLINE_EMOJI_PATTERN, parse_inline_emoji)
        # Add 'emoji' to the default inline methods list
        md.inline.rules.append("emoji")
        if md.renderer and hasattr(md.renderer, "register"):
            md.renderer.register("emoji_text", render_html_emoji)

    class CustomHighlightRenderer(mistune.HTMLRenderer):
        """Custom renderer to handle script blocking and code block highlighting."""

        def block_html(self, html: str) -> str:
            # Prevent raw script tags from Markdown to avoid XSS
            stripped_html = html.strip()
            if stripped_html.lower().startswith("<script") and stripped_html.lower().endswith(
                "</script>"
            ):
                logger.warning("Blocked a <script> tag found in Markdown content.")
                return "<!-- Potentially unsafe script tag was blocked by Report Creator -->"
            return super().block_html(html)  # Use super for other HTML blocks

        def block_code(self, code: str, info: Optional[str] = None) -> str:
            language = (
                info.strip() if info else "plaintext"
            )  # Default to plaintext if no language info

            if language == "mermaid":
                # For Mermaid diagrams, wrap in a div for Mermaid.js to process.
                # The content itself should not be escaped here, as Mermaid.js needs the raw syntax.
                return f'<div class="mermaid include_mermaid">{mistune.escape_html(code)}</div>'
            else:
                # For other code blocks, prepare for Highlight.js.
                # Escape the code content to safely display it as preformatted text.
                escaped_code = mistune.escape(code)
                return (
                    f'<div class="codehilite code-block">'
                    f'<pre><code class="language-{mistune.escape(language)}">{escaped_code}</code></pre>'
                    f"</div>"
                )

    # Create Markdown parser with the custom renderer and plugins
    markdown_parser = mistune.create_markdown(
        renderer=CustomHighlightRenderer(escape=False),  # Renderer handles its own escaping
        plugins=[
            "task_lists",  # For `- [ ]` and `- [x]`
            "def_list",  # For definition lists
            "math",  # For LaTeX math (requires MathJax/KaTeX on client)
            "table",  # For GFM tables
            "strikethrough",  # For `~~strikethrough~~`
            "footnotes",  # For `[^1]` and `[^1]: footnote content`
            "url",  # For auto-linking URLs
            "spoiler",  # For `||spoiler||` (GFM-style)
            # emojis_plugin,  # Custom emoji plugin
        ],
        hard_wrap=False,  # Respect Markdown newlines for paragraphs
    )
    return markdown_parser(str(text))


def _time_it(func: callable) -> callable:
    """
    A decorator that measures and logs the execution time of the decorated function.

    The execution time is logged at the DEBUG level using the `report_creator` logger.
    The log message includes the function's qualified name (e.g., `ClassName.method_name`
    or `function_name`) and the time taken in seconds, formatted to four decimal places.

    Args:
        func (callable): The function to be timed.

    Returns:
        callable: The wrapped function, which when called, will execute the original
                  function, log its execution time, and return its result.
    """

    @functools.wraps(func)  # Preserves metadata of the original function
    def wrapper_timer(*args: Any, **kwargs: Any) -> Any:
        start_time = time.perf_counter()  # More precise than time.time() for short durations
        value = func(*args, **kwargs)
        end_time = time.perf_counter()
        run_time = end_time - start_time
        # func.__qualname__ gives Class.method or just function name, good for context
        logger.debug(f"Execution of [{func.__qualname__}] took: {run_time:.4f} secs")
        return value

    return wrapper_timer


def _strip_whitespace(func: callable) -> callable:
    """
    A decorator that strips leading and trailing whitespace from the string output
    of the decorated function.

    If the decorated function returns a value that is not a string, that value
    is returned unchanged without attempting to strip whitespace.

    Args:
        func (callable): The function whose string output should be stripped.

    Returns:
        callable: The wrapped function. If it returns a string, the string will
                  have leading/trailing whitespace removed. Otherwise, the original
                  return value is passed through.
    """

    @functools.wraps(func)  # Preserves metadata
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        result = func(*args, **kwargs)
        if isinstance(result, str):
            return result.strip()  # Strip whitespace if it's a string
        return result  # Return as-is if not a string

    return wrapper


def create_color_value_sensitive_mapping(
    values: list[Union[str, int, float, bool]],  # Added bool to Union
    error_keywords: Optional[Sequence[str]] = None,
    error_color: str = "red",
    success_color: str = "green",
    default_color: str = "gray",
    boolean_true_color: Optional[str] = None,  # Color for True booleans
    boolean_false_color: Optional[str] = None,  # Color for False booleans
) -> list[str]:
    """
    Creates a list of colors corresponding to a list of input values, assigning
    colors based on error conditions, success, boolean states, or a default.

    Color assignment priority:
    1.  **Error Conditions**:
        -   If a string value contains any of the `error_keywords` (case-insensitive).
        -   If a numeric value is negative.
        These are assigned `error_color`.
    2.  **Boolean Values** (if specific boolean colors are provided):
        -   If `value` is `True` and `boolean_true_color` is set.
        -   If `value` is `False` and `boolean_false_color` is set.
    3.  **Success/Default for Strings/Numbers**:
        -   If not an error, string or numeric values are assigned `success_color`.
    4.  **Default**:
        -   Any other value types, or booleans if their specific colors aren't set,
            receive `default_color`.

    Args:
        values (list[Union[str, int, float, bool]]): A list of values to be color-coded.
        error_keywords (Optional[Sequence[str]], optional): A sequence of strings.
            If any of these (case-insensitive) are found within a string value,
            it's marked as an error. Defaults to `("error", "fail", "failed", "failure", "404", "exception")`.
        error_color (str, optional): Color for error values. Defaults to "red".
        success_color (str, optional): Color for non-error strings/numbers.
            Defaults to "green".
        default_color (str, optional): Color for values not otherwise classified.
            Defaults to "gray".
        boolean_true_color (Optional[str], optional): Specific color for `True` values.
            If None, `True` falls into success/default logic. Defaults to None.
        boolean_false_color (Optional[str], optional): Specific color for `False` values.
            If None, `False` (often seen as non-error) might fall into success/default.
            Consider setting this to `error_color` or another distinct color if `False`
            should be highlighted differently from neutral/default. Defaults to None.


    Returns:
        list[str]: A list of color strings, one for each input value.
    """
    if error_keywords is None:
        error_keywords = ("error", "fail", "failed", "failure", "404", "exception", "critical")

    output_colors: list[str] = []
    # Prepare error keywords for case-insensitive matching
    lower_error_keywords = {keyword.lower() for keyword in error_keywords}

    for value in values:
        assigned_color = None  # Color for the current value

        # Check for error conditions first
        if isinstance(value, str):
            if any(err_kw in value.lower() for err_kw in lower_error_keywords):
                assigned_color = error_color
        elif isinstance(value, (int, float)) and value < 0:
            assigned_color = error_color

        # If not an error, check for boolean-specific colors
        if assigned_color is None and isinstance(value, bool):
            if value is True and boolean_true_color is not None:
                assigned_color = boolean_true_color
            elif value is False and boolean_false_color is not None:
                assigned_color = boolean_false_color

        # If still no color assigned, apply success or default
        if assigned_color is None:
            assigned_color = (
                success_color if isinstance(value, (str, int, float, bool)) else default_color
            )

        output_colors.append(assigned_color)

    return output_colors


def _random_light_color_generator(seed_word: str) -> tuple[str, str]:
    """
    Generates a light background color and a fixed text color ("black")
    deterministically based on an input `seed_word`.

    The background color is chosen from a predefined list (`report_creator_colors`)
    and then programmatically lightened. The selection from the list is made
    randomly but seeded with the `seed_word`, ensuring that the same word
    always produces the same initial color choice and thus the same final light color.

    Args:
        seed_word (str): The string used to seed the random color selection,
            ensuring deterministic output for the same seed.

    Returns:
        tuple[str, str]: A tuple where the first element is the lightened
                         background color (hex string, e.g., "#aabbcc") and
                         the second element is the text color ("black").
    """
    # Seed the module-level RNG instance to ensure deterministic color choice
    # based on the input word. Adding affixes to seed for this specific generator.
    _color_rng.seed(f"light_{seed_word}_gen".encode())

    def lighten_hex_color(hex_color_str: str, factor: float = 0.64) -> str:
        """
        Lightens a given hex color string.
        Factor = 0.0: no change. Factor = 1.0: completely white.
        """
        hex_color_str = hex_color_str.lstrip("#")
        rgb = [int(hex_color_str[i : i + 2], 16) for i in (0, 2, 4)]  # Convert hex to R, G, B
        # Calculate lightened RGB components
        light_rgb = [min(255, int(c + (255 - c) * factor)) for c in rgb]
        return "#{:02x}{:02x}{:02x}".format(*light_rgb)

    # Choose a base color from the predefined list using the seeded RNG
    base_color = _color_rng.choice(report_creator_colors)
    lightened_bg_color = lighten_hex_color(base_color, factor=0.64)

    return lightened_bg_color, "black"  # Text color is fixed to black for light backgrounds


def _random_color_generator(seed_word: str) -> tuple[str, str]:
    """
    Generates a random background color and a contrasting text color (black or white)
    deterministically based on an input `seed_word`.

    The random color generation is seeded with the `seed_word` to ensure that
    the same word always produces the same background color. The text color
    (black or white) is then chosen based on the calculated luminance of the
    background color to ensure good readability.

    Args:
        seed_word (str): The string used to seed the random color generation.

    Returns:
        tuple[str, str]: A tuple containing:
                         - The generated background color (hex string, e.g., "#1a2b3c").
                         - The contrasting text color ("black" or "white").
    """
    # Seed the module-level RNG with a combination of word and a salt for this generator
    _color_rng.seed(f"contrast_{seed_word}_gen".encode())

    # Generate random R, G, B components
    r_val = _color_rng.randint(0, 255)
    g_val = _color_rng.randint(0, 255)
    b_val = _color_rng.randint(0, 255)

    background_color_hex = f"#{r_val:02x}{g_val:02x}{b_val:02x}"

    # Calculate luminance of the background color to determine text color
    # Formula for luminance: Y = 0.299*R + 0.587*G + 0.114*B
    # (standard formula for perceived brightness)
    luminance = (0.299 * r_val + 0.587 * g_val + 0.114 * b_val) / 255

    # If luminance is greater than 0.5, background is light, use black text.
    # Otherwise, background is dark, use white text.
    text_color = "black" if luminance > 0.5 else "white"

    return background_color_hex, text_color


def _get_url_root(url: str) -> str:
    """
    Extracts the root (scheme and network location) from a given URL string.

    For example, for "https://www.example.com/path/page?query=1", this function
    would return "https://www.example.com".

    Args:
        url (str): The URL string to parse.

    Returns:
        str: The root of the URL, consisting of the scheme (e.g., "http", "https")
             and the network location (e.g., "www.example.com"). Returns an empty
             string if the URL is malformed and cannot be parsed.
    """
    try:
        parsed_url = urlparse(str(url))  # Ensure URL is a string
        # Reconstruct the root URL from scheme and netloc
        root_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        return root_url
    except Exception:  # Catch potential errors from urlparse on malformed URLs
        logger.warning(f"Could not parse URL to get root: {_ellipsis_url(str(url))}")
        return ""


def _convert_filepath_to_datauri(filepath: str) -> str:
    """
    Converts a local file's content into a base64-encoded data URI.

    The function reads the file in binary mode, guesses its MIME type based
    on the file extension, and then constructs the data URI. This is useful
    for embedding images or other file content directly into HTML.

    Args:
        filepath (str): The absolute or relative path to the local file.

    Returns:
        str: The data URI string (e.g., "data:image/png;base64,iVBORw0KGgo...").

    Raises:
        FileNotFoundError: If the specified `filepath` does not exist or is not a file.
        ValueError: If the MIME type cannot be determined for the file,
                    if an `IOError` occurs during file reading, or if any other
                    unexpected error happens during the conversion process.
    """
    if not os.path.isfile(filepath):  # More specific check than os.path.exists
        raise FileNotFoundError(f"File not found or is not a regular file: {filepath}")

    try:
        # Guess MIME type from file extension
        mime_type, encoding = mimetypes.guess_type(filepath)
        if mime_type is None:
            # Fallback or raise error if MIME type is crucial
            logger.warning(
                f"Could not determine MIME type for {filepath}. Defaulting to 'application/octet-stream'."
            )
            mime_type = "application/octet-stream"

        with open(filepath, "rb") as file_handle:
            file_bytes = file_handle.read()

        base64_encoded_data = base64.b64encode(file_bytes).decode("utf-8")
        data_uri = f"data:{mime_type};base64,{base64_encoded_data}"

        logger.info(
            f"Converted local file to data URI: '{_ellipsis_url(filepath)}' "
            f"(MIME: {mime_type}, Original Size: {humanize.naturalsize(len(file_bytes))})"
        )
        return data_uri

    except OSError as e:
        logger.error(f"IOError when reading file '{filepath}': {e}")
        raise ValueError(
            f"Could not convert file '{filepath}' to data URI due to an IO error."
        ) from e
    except Exception as e:  # Catch any other unexpected errors
        logger.error(
            f"An unexpected error occurred while converting file '{filepath}' to data URI: {e}"
        )
        raise ValueError(
            f"Could not convert file '{filepath}' to data URI due to an unexpected error."
        ) from e


def _convert_imgurl_to_datauri(image_url: str) -> str:
    """
    Fetches an image from a given URL and converts it into a base64-encoded data URI.

    This function uses the `requests` library to download the image. The MIME type
    is determined from the 'Content-Type' HTTP header of the server's response.
    If the header is missing or uninformative, it attempts to guess the MIME type
    from the URL's file extension. A 'Referer' header (using the root of the
    image URL) and a network timeout are used for the HTTP GET request.

    Args:
        image_url (str): The URL of the image to fetch and convert.

    Returns:
        str: The data URI string (e.g., "data:image/png;base64,iVBORw0KGgo...").

    Raises:
        ValueError: If the image cannot be fetched (due to network issues, HTTP errors,
                    timeouts), if the MIME type cannot be reliably determined, or if any
                    other unexpected error occurs during the process. This wraps exceptions
                    from `requests.exceptions.RequestException`.
    """
    if not isinstance(image_url, str) or not image_url.startswith(("http://", "https://")):
        raise ValueError(
            f"Invalid image URL provided: {_ellipsis_url(str(image_url))}. Must be a valid HTTP/HTTPS URL."
        )

    try:
        # Use the root of the image URL as the Referer. Some servers might require this.
        # Also, set a reasonable timeout for the request.
        headers = {"Referer": _get_url_root(image_url)}
        timeout_seconds = 10
        response = requests.get(image_url, headers=headers, timeout=timeout_seconds)
        response.raise_for_status()  # Raises HTTPError for bad responses (4XX or 5XX)

        # Determine MIME type primarily from Content-Type header
        content_type_header = response.headers.get("Content-Type")
        mime_type = None
        if content_type_header:
            mime_type = content_type_header.split(";")[0].strip().lower()  # Normalize

        # If Content-Type is missing or generic, try guessing from URL extension
        if not mime_type or mime_type == "application/octet-stream":
            guessed_mime_type, _ = mimetypes.guess_type(
                urlparse(image_url).path
            )  # Use path part of URL
            if guessed_mime_type:
                mime_type = guessed_mime_type
            elif (
                mime_type == "application/octet-stream" and not guessed_mime_type
            ):  # Still generic
                raise ValueError(
                    f"Could not reliably determine MIME type for image URL: {image_url}. Content-Type: '{content_type_header}'."
                )

        if not mime_type:  # Final fallback if still no MIME type
            raise ValueError(f"MIME type for image URL {image_url} could not be determined.")

        base64_encoded_content = base64.b64encode(response.content).decode("utf-8")
        data_uri = f"data:{mime_type};base64,{base64_encoded_content}"

        logger.info(
            f"Fetched image from URL and converted to data URI: '{_ellipsis_url(unquote(image_url))}' "
            f"(MIME: {mime_type}, Original Size: {humanize.naturalsize(len(response.content))})"
        )
        return data_uri

    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout while fetching image URL '{image_url}': {e}")
        raise ValueError(f"Timeout converting image URL '{image_url}' to data URI.") from e
    except requests.exceptions.HTTPError as e:
        logger.error(
            f"HTTP error {e.response.status_code} while fetching image URL '{image_url}': {e}"
        )
        raise ValueError(f"HTTP error converting image URL '{image_url}' to data URI.") from e
    except requests.exceptions.RequestException as e:
        # Catches other general request issues like connection errors
        logger.error(f"Failed to fetch image URL '{image_url}' due to a request exception: {e}")
        raise ValueError(
            f"Could not convert image URL '{image_url}' to data URI due to a request failure."
        ) from e
    except Exception as e:
        # Catch any other unexpected errors (e.g., base64 encoding, unexpected NoneTypes)
        logger.error(
            f"An unexpected error occurred while converting image URL '{image_url}' to data URI: {e}"
        )
        raise ValueError(
            f"Could not convert image URL '{image_url}' to data URI due to an unexpected error."
        ) from e
