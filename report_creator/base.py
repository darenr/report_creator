from __future__ import annotations

from abc import ABC, abstractmethod


class Base(ABC):
    """
    Abstract Base Class for report components.

    This class serves as the foundation for all visual elements within a report.
    It defines the common interface and behavior expected of all report components.
    Each concrete component, such as a Block, Group, Metric, or Chart, should inherit
    from this class.
    """

    def __init__(self, label: str | None = None):
        self.label = label

    @abstractmethod
    def to_html(self) -> str:
        """Each component that derives from Base must implement this method"""
        pass
