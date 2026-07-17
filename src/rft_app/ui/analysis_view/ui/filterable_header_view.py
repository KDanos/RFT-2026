from __future__ import annotations

from PyQt6.QtCore import QPoint, QRect, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QPainter
from PyQt6.QtWidgets import QHeaderView, QStyle, QStyleOptionHeader, QTableView, QWidget


class FilterableHeaderView(QHeaderView):
    """Horizontal table header with separate sort and filter click zones."""

    sort_requested = pyqtSignal(int)
    filter_requested = pyqtSignal(int)

    _FILTER_BUTTON_WIDTH = 20
    _RESIZE_HANDLE_WIDTH = 6

    def __init__(
        self,
        orientation: Qt.Orientation = Qt.Orientation.Horizontal,
        parent: QWidget | None = None,
        ) -> None:
        super().__init__(orientation, parent)
        self._filtered_sections: set[int] = set()

        self.setSectionsClickable(True)
        self.setHighlightSections(True)
        self.setSortIndicatorShown(True)
        self.setDefaultAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )

    def set_filtered_sections(self, sections: set[int]) -> None:
        """Mark columns that currently have an active filter."""
        self._filtered_sections = set(sections)
        self.viewport().update() #what does this line achieve?

    def set_filtered_column_names(self, column_names: set[str]) -> None:
        """Helper when we know filter names, not indices."""
        sections: set[int] = set()
        model = self.model()

        if model is None:
            self.set_filtered_sections(set())
            return

        for section in range(self.count()):
            header_text = model.headerData(
                section,
                Qt.Orientation.Horizontal,
                Qt.ItemDataRole.DisplayRole,
            )
            if header_text in column_names:
                sections.add(section)

        self.set_filtered_sections(sections)

    def sectionSizeFromContents(self, logical_index: int) -> QSize:
        """Reserve space for the filter button when sizing columns from header text."""
        size = super().sectionSizeFromContents(logical_index)
        return QSize(size.width() + self._FILTER_BUTTON_WIDTH + 4, size.height())

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
        if self._is_on_resize_handle(pos):
            super().mousePressEvent(event)
            return

        logical_index = self.logicalIndexAt(pos)
        if logical_index < 0:
            super().mousePressEvent(event)
            return

        if self._is_filter_click(logical_index, pos):
            self.filter_requested.emit(logical_index)
            event.accept()
            return

        self.sort_requested.emit(logical_index)
        event.accept()

    def paintSection(self, painter: QPainter, rect: QRect, logical_index: int) -> None:
        painter.save()
        model = self.model()
        if model is None:
            painter.restore()
            return

        filter_rect = self._filter_button_rect(rect)
        header_text = model.headerData(
            logical_index,
            Qt.Orientation.Horizontal,
            Qt.ItemDataRole.DisplayRole,
        )
        text_width = max(0, rect.width() - self._FILTER_BUTTON_WIDTH - 8)
        elided_text = painter.fontMetrics().elidedText(
            header_text or "",
            Qt.TextElideMode.ElideRight,
            text_width,
        )

        option = QStyleOptionHeader()
        self.initStyleOption(option)
        option.rect = rect
        option.section = logical_index
        option.text = elided_text
        self.style().drawControl(QStyle.ControlElement.CE_Header, option, painter, self)

        is_filtered = logical_index in self._filtered_sections
        painter.setFont(QFont(self.font().family(), max(7, self.font().pointSize() - 1)))
        if is_filtered:
            painter.fillRect(
                filter_rect.adjusted(1, 1, -1, -1),
                QColor(220, 235, 255),
            )
            painter.setPen(QColor(40, 90, 180))
            glyph = "▼"
        else:
            painter.setPen(QColor(90, 90, 90))
            glyph = "▾"
        painter.drawText(filter_rect, Qt.AlignmentFlag.AlignCenter, glyph)
        painter.restore()

    def _filter_button_rect(self, section_rect: QRect) -> QRect:
        return QRect(
            section_rect.right() - self._FILTER_BUTTON_WIDTH + 1,
            section_rect.top() + 2,
            self._FILTER_BUTTON_WIDTH - 2,
            section_rect.height() - 4,
        )

    def _is_on_resize_handle(self, pos: QPoint) -> bool:
        if self.orientation() != Qt.Orientation.Horizontal:
            return False
        for section in range(self.count()):
            edge = self.sectionViewportPosition(section) + self.sectionSize(section)
            if abs(pos.x() - edge) <= self._RESIZE_HANDLE_WIDTH:
                return True
        return False

    def _is_filter_click(self, logical_index: int, pos: QPoint) -> bool:
        section_pos = self.sectionViewportPosition(logical_index)
        section_rect = QRect(
            section_pos,
            0,
            self.sectionSize(logical_index),
            self.height(),
        )
        return self._filter_button_rect(section_rect).contains(pos)

    @classmethod
    def install_on(cls, table_view: QTableView) -> FilterableHeaderView:
        """Replace the default horizontal header on a QTableView."""
        header = cls(Qt.Orientation.Horizontal, table_view)
        table_view.setHorizontalHeader(header)
        return header
