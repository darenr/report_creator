import logging
from typing import Optional
from uuid import uuid4

from ..utilities import (
    _generate_anchor_id,
    _strip_whitespace,
)

# Configure logging
logger = logging.getLogger("report_creator")

from .base import Base


class Block(Base):
    """
    A container for vertically stacking report components.

    The `Block` component is fundamental for structuring a report's layout.
    It arranges its child components in a single, vertical column,
    rendering them sequentially from top to bottom. This allows for
    the creation of visually organized sections within a report.
    """

    def __init__(self, *components: Base, label: Optional[str] = None):
        super().__init__(label=label)
        self.components = components
        logger.info(f"Block: {len(self.components)} components")

    @_strip_whitespace
    def to_html(self) -> str:
        html_output = "<block>"

        for component in self.components:
            html_output += "<block-component>"
            html_output += component.to_html()
            html_output += "</block-component>"

        html_output += "</block>"

        return html_output


class Group(Base):
    """
    A container for horizontally arranging report components.

    The `Group` component is used to arrange multiple report
    components side-by-side within a horizontal row. It acts as a
    wrapper that renders its child components next to each other,
    allowing you to create layouts with columns or multiple elements
    on the same horizontal line.
    """

    def __init__(self, *components: Base, label: Optional[str] = None):
        super().__init__(label=label)
        self.components = components
        logger.info(f"Group: {len(self.components)} components {label=}")

    @_strip_whitespace
    def to_html(self) -> str:
        html_output = "<div>"

        if self.label:
            anchor_id = _generate_anchor_id(self.label)
            html_output += (
                f"<report-caption><a href='#{anchor_id}'>{self.label}</a></report-caption>"
            )

        html_output += """<div class="group">"""

        for component in self.components:
            html_output += "<div class='group-content'>"
            html_output += component.to_html()
            html_output += "</div>"

        html_output += "</div>"  # group
        html_output += "</div>"  # outer block div

        return html_output


class Collapse(Base):
    """
    A container for creating collapsible sections in a report.

    The `Collapse` component allows you to group a set of report
    components under a single, clickable header. When the header
    is clicked, the content within the `Collapse` is either revealed
    or hidden, allowing for a more compact and organized presentation
    of information. This is useful for hiding less important or
    detailed content that the user may choose to view on demand.
    """

    def __init__(self, *components: Base, label: Optional[str] = None):
        super().__init__(label=label)
        self.components = components
        logger.info(f"Collapse: {len(self.components)} components, {label=}")

    @_strip_whitespace
    def to_html(self) -> str:
        html_output = f"""<details class="collapse"><summary>{self.label}</summary>"""

        for component in self.components:
            html_output += component.to_html()

        html_output += "</details>"
        return html_output


class Select(Base):
    """
    Creates a dropdown select element for user interaction within the report.

    The `Select` component allows you to include a dropdown list within your report,
    enabling users to select a single option from a predefined set of choices.
    This can be useful for filtering data, choosing between different views,
    or otherwise controlling the report's behavior.

    Args:
        blocks (list[Base]): A list of `Base` components to be displayed
            within the dropdown. Each component will be associated with
            a separate option in the dropdown list. When the user selects
            an option, the corresponding component will be displayed in
            the report.
        label (Optional[str], optional): An optional label or description
            for the select element. If provided, this label will be displayed
            above the dropdown, helping to explain its purpose to the user.
            Defaults to None.

    Raises:
        ValueError: If the `default_value` is provided but is not present in the `options`.
    """

    def __init__(self, blocks: list[Base], *, label: Optional[str] = None):
        super().__init__(label=label)
        self.blocks = blocks

        for b in self.blocks:
            if not b.label:
                raise ValueError("All blocks must have a label to use in a Select")

        logger.info(
            f"Select: {len(self.blocks)} tabs: {', '.join([c.label for c in self.blocks])}"
        )

    @_strip_whitespace
    def to_html(self) -> str:
        html_output = (
            f"<report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</a></report-caption>"
            if self.label
            else ""
        )

        # unique ID for select grouping.
        # Ensures no clashes between different selects with the same block.label set
        # self.label may not be unique
        data_table_index = int(uuid4()) % 10000

        # assemble the button bar for the tabs
        html_output += """<div class="tab">"""
        for i, block in enumerate(self.blocks):
            extra = "defaultOpen" if i == 0 else ""
            html_output += f"""<button class="tablinks {extra}" onclick="openTab(event, '{block.label}', {data_table_index})" data-table-index={data_table_index}>{block.label}</button>"""
        html_output += """</div>"""

        # assemble the tab contents
        for block in self.blocks:
            html_output += f"""<div id="{block.label}" data-table-index={data_table_index} class="tabcontent">"""
            html_output += block.to_html()
            html_output += """</div>"""

        return html_output


class Accordion(Base):
    """
    Creates an accordion element for organizing and collapsing content sections within a report.

    The `Accordion` component allows you to group multiple `Collapse` components
    into a single, vertically stacked accordion. Each `Collapse` acts as an
    expandable/collapsible panel within the accordion. Only one panel can be
    expanded at a time, providing a compact and organized way to present
    multiple sections of content.

    Args:
        blocks (list[Base]): A list of `Base` components to be displayed
            within the accordion. Each component will be associated with
            a separate collapsible panel. When the user expands a panel,
            the corresponding component will be displayed in the report.
        label (Optional[str], optional): An optional label or heading for
            the entire accordion. If provided, a caption with a linkable
            anchor will be generated above the accordion. Defaults to None.

    Raises:
        ValueError: If any of the components do not have a label.
    """

    def __init__(
        self,
        blocks: list[Base],
        *,
        label: Optional[str] = None,
        open_first: Optional[bool] = False,
    ):
        super().__init__(label=label)
        self.blocks = blocks
        self.open_first = open_first

        for b in self.blocks:
            if not b.label:
                raise ValueError("All blocks must have a label to use in an Accordion")

        logger.info(
            f"Select: {len(self.blocks)} tabs: {', '.join([c.label for c in self.blocks])}"
        )

    @_strip_whitespace
    def to_html(self) -> str:
        html_output = (
            f"<report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</a></report-caption>"
            if self.label
            else ""
        )

        # assesmble the accordion
        for i, block in enumerate(self.blocks):
            html_output += f"""<details {" open " if i == 0 and self.open_first else ""} class="accordion">"""
            html_output += f"""<summary>{block.label}</summary>"""
            html_output += block.to_html()
            html_output += """</details>"""

        return html_output


class Heading(Base):
    """
    Displays a large heading within the report.

    The `Heading` component is used to create visually distinct
    headings or titles within a report. It provides a way to
    structure content and create clear sections.

    Args:
        text (str): The text content of the heading. This will be
            displayed as a large heading within the report.
        level (int, optional): The HTML heading level to use (h1-h6).
            Lower numbers are larger and more prominent. Defaults to 1 (h1).
        label (Optional[str], optional): An optional label for the
            heading. If provided, a caption with a linkable anchor
            will be generated above the heading. Defaults to None.

    Raises:
        ValueError: If the specified `level` is not between 1 and 6.
    """

    def __init__(
        self,
        label: str,
        *,
        level: Optional[int] = 1,
    ):
        super().__init__(label=label)
        assert level >= 1 and level <= 5, (
            f"heading level ({level}) must be between 1 and 5 (inclusive)"
        )
        assert label, "No heading label provided"
        self.level = level
        logger.info(f"Heading: (h{level}): [{label}]")

    @_strip_whitespace
    def to_html(self) -> str:
        """
        Converts the heading to an HTML string.

        Returns:
            str: The HTML representation of the heading.
        """
        return f"<br /><h{self.level}>{self.label}</h{self.level}><br />"


class Separator(Base):
    """
    Inserts a visual separator (horizontal rule) into the report.

    The `Separator` component provides a way to create clear visual
    breaks between sections of a report. It renders as a horizontal
    line, making it easy to distinguish different parts of the content.

    Args:
        label (Optional[str], optional): An optional label for the separator.
            If provided, a caption with a linkable anchor will be generated
            above the separator line. This can be used for internal
            referencing or to provide a brief description of the break.
            Defaults to None.
    """

    def __init__(self, label: Optional[str] = None):
        super().__init__(label=label)
        logger.info(f"Separator: {label=}")

    @_strip_whitespace
    def to_html(self) -> str:
        """Converts the Separator object to its HTML representation.

        Returns:
            str: The HTML representation of the Separator.
        """
        if self.label:
            return f"<br><hr><report-caption><a href='#{_generate_anchor_id(self.label)}'>{self.label}</a></report-caption>"
        else:
            return "<br><hr>"
