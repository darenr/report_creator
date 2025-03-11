import logging
import os
from typing import Optional

from ..utilities import (
    _convert_filepath_to_datauri,
    _convert_imgurl_to_datauri,
    _generate_anchor_id,
    _strip_whitespace,
)
from .base import Base

# Configure logging
logger = logging.getLogger("report_creator")


class Image(Base):
    """
    Embeds an image within the report, optionally linking it to an external URL.

    The `Image` component allows you to include images in your report,
    either by referencing an external URL or by embedding a base64-encoded
    image directly within the HTML. You can also make the image clickable,
    linking it to another webpage.

    Args:
        src (str): The source of the image. This can be either:
            A URL pointing to an image on the web, a local file path,
            or a base64-encoded image string.
        link_to (Optional[str], optional): An optional URL that the image
            will link to when clicked. If not provided, the image will
            not be clickable. Defaults to None.
        label (Optional[str], optional): An optional label or caption for
            the image. If provided, it will be displayed below the image
            and can be used as a linkable anchor within the report.
            Defaults to None.
        extra_css (Optional[str], optional): Additional inline CSS styles
            to be applied to the image element. This allows for custom
            styling beyond the basic options. Defaults to None.
        rounded (bool, optional): If True, the image will be displayed with
            rounded corners. Defaults to True.
        convert_to_base64 (bool, optional): If True, the `src` will be
            treated as a URL. The image at that URL will be fetched,
            and its content will be embedded in the report as a
            base64-encoded image. This ensures that the image is
            always available, even if the original URL becomes inaccessible.
            Defaults to False.
    """

    def __init__(
        self,
        src: str,
        *,
        link_to: Optional[str] = None,
        label: Optional[str] = None,
        extra_css: Optional[str] = None,
        rounded: Optional[bool] = True,
        convert_to_base64: Optional[bool] = False,
    ):
        super().__init__(label=label)
        self.link_to = link_to
        self.extra_css = extra_css or ""
        self.rounded_css = "border-radius: 0.75rem;" if rounded else ""

        if src.startswith("data:image"):
            # Base64 image
            self.src = src
        elif os.path.exists(src):
            # Local file
            self.src = _convert_filepath_to_datauri(src)
        elif convert_to_base64:
            # URL that should be fetched and rendered as base64
            self.src = _convert_imgurl_to_datauri(src)
        else:
            # URL (external image)
            self.src = src

        logger.info(f"Image: label: {self.label}")

    @_strip_whitespace
    def to_html(self) -> str:
        html_output = """<div class="image-block"><figure>"""

        image_markup = f"""<img src="{self.src}" style="{self.rounded_css} {self.extra_css}" alt="{self.label or self.src}">"""
        if self.link_to:
            html_output += f"""<a href="{self.link_to}" target="_blank">{image_markup}</a>"""
        else:
            html_output += image_markup

        if self.label:
            html_output += f"<figcaption><report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</a></report-caption></figcaption>"

        html_output += "</figure></div>"

        return html_output


class Diagram(Base):
    """
    Renders a diagram using Mermaid.js syntax within the report.

    The `Diagram` component allows you to create and embed diagrams
    directly within your report using the Mermaid.js library. Mermaid
    allows you to define diagrams using a simple text-based syntax,
    which is then rendered visually by the library.

    This component is highly versatile, enabling the creation of various
    diagram types, including flowcharts, sequence diagrams, Gantt charts,
    class diagrams, state diagrams, and more. For detailed syntax
    examples, refer to the Mermaid.js documentation: https://mermaid.js.org/syntax/examples.html.
    ChatGPT is also able to create the diagrams for you simply by describing them in text.

    Args:
        src (str): The Mermaid.js source code defining the diagram.
            This is the text that describes the diagram's structure
            and elements using Mermaid's syntax.
        pan_and_zoom (Optional[bool], optional): Enables panning and zooming
            functionality for the diagram in the rendered report.
            Users can pan by dragging the mouse and zoom using shift + mouse wheel.
            Defaults to True.
        extra_css (Optional[str], optional): Additional inline CSS styles to be
            applied to the diagram. This allows for custom styling beyond
            Mermaid's default appearance. Defaults to None.
        label (Optional[str], optional): An optional label or caption for the
            diagram. If provided, a caption with a linkable anchor will be
            displayed above the diagram. Defaults to None.
    """

    def __init__(
        self,
        src: str,
        *,
        pan_and_zoom: Optional[bool] = True,
        extra_css: Optional[str] = None,
        label: Optional[str] = None,
    ):
        super().__init__(label=label)

        self.src = src
        self.extra_css = extra_css or ""
        self.pan_and_zoom = pan_and_zoom
        logger.info(f"Diagram: {len(self.src)} characters")

    @_strip_whitespace
    def to_html(self) -> str:
        html_output = """
            <div class="diagram-block">
                <figure>
        """

        if self.label:
            html_output += f"<figcaption><report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</a></report-caption></figcaption>"

        html_output += f"""<pre class='mermaid include_mermaid {"mermaid-pan-zoom" if self.pan_and_zoom else ""}' style="{self.extra_css}">
                        {self.src}
                    </pre>"""

        if self.pan_and_zoom:
            html_output += "<small>"
            html_output += "pan (mouse) and zoom (shift+wheel)"
            html_output += """&nbsp;<a href="#" onclick="event.preventDefault();" class="panzoom-reset">(reset)</a>"""
            html_output += "</small>"

        html_output += """
                </figure>
            </div>"""

        return html_output
