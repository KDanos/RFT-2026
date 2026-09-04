from PyQt6.QtCore import QRect, QSize, Qt
from PyQt6.QtGui import QIcon, QMouseEvent, QPainter
from PyQt6.QtWidgets import QHeaderView

from ui import app_icon
from ui.filterable_table.filter_by_row_menu import FilterByRowMenu
from ui.filterable_table.proxy_model import ProxyFilterModel


class FilterableHeaderView(QHeaderView):
    """Horizontal header that reserves space for a small filter icon"""

    ICON_SIZE = 14
    ICON_MARGIN = 4

    def __init__(self, orientation: Qt.Orientation, parent=None) -> None:
        super().__init__(orientation, parent)

        # Set project variables
        # (none)

        # Set module variables
        self.filter_icon_active: QIcon = app_icon("mdi.filter-menu")
        self.filter_icon_idle: QIcon = app_icon("fa5s.sort-down")

        # Initialisation methods
        # (none)

    #--------Private UI--------

    def _icon_rect(self, section_rect: QRect) -> QRect:
        """Return the filter-icon rectangle inside a header section.

        Pinned to the right edge of the section and vertically centered,
        in the same coordinate system as ``section_rect``.
        """
        size = self.ICON_SIZE
        x = section_rect.right() - self.ICON_MARGIN - size
        y = section_rect.top() + (section_rect.height() - size) // 2
        return QRect(x, y, size, size)

    #--------Public API--------

    def mousePressEvent(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint()
        logical_index = self.logicalIndexAt(pos.x())

        if logical_index >= 0:
            section_rect = QRect(
                self.sectionViewportPosition(logical_index),
                0,
                self.sectionSize(logical_index),
                self.height(),
            )

            current_filter_icon = self._icon_rect(section_rect)
            if current_filter_icon.contains(pos):
                global_pos = self.mapToGlobal(current_filter_icon.bottomLeft())
                column_name = self.model().headerData(
                    logical_index,
                    Qt.Orientation.Horizontal,
                    Qt.ItemDataRole.DisplayRole,
                )
                menu = FilterByRowMenu(
                    logical_index,
                    column_name,
                    self.parent().proxy_model,
                )
                menu.exec(global_pos)
                return

        super().mousePressEvent(event)

    def paintSection(self, painter: QPainter, rect: QRect, logicalIndex: int) -> None:
        super().paintSection(painter, rect, logicalIndex)

        proxy = self.model()
        has_filter = (
            isinstance(proxy, ProxyFilterModel) and logicalIndex in proxy.active_filters
        )

        icon = self.filter_icon_active if has_filter else self.filter_icon_idle
        icon_rect = self._icon_rect(rect)
        icon.paint(painter, icon_rect)

    def sectionSizeFromContents(self, logicalIndex: int) -> QSize:
        size = super().sectionSizeFromContents(logicalIndex)
        extra = self.ICON_SIZE + (self.ICON_MARGIN * 2)
        return QSize(size.width() + extra, size.height())
