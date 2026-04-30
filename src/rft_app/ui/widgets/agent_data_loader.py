import csv
from io import StringIO

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class AgentDataLoaderDialog(QDialog):
    """Scaffold dialog for clipboard-based data loading and column mapping."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Data Loader")
        self.resize(1200, 700)
        self._headers: list[str] = []
        self._rows: list[list[str]] = []

        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        root_layout = QHBoxLayout(self)

        # Left: load controls panel
        self.controls_frame = QFrame(self)
        self.controls_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.controls_frame.setMinimumWidth(220)
        self.controls_frame.setMaximumWidth(320)
        controls_layout = QVBoxLayout(self.controls_frame)

        controls_form = QFormLayout()
        controls_form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self.max_rows_spin = QSpinBox(self.controls_frame)
        self.max_rows_spin.setRange(1, 1_000_000)
        self.max_rows_spin.setValue(50)
        controls_form.addRow("Show max rows", self.max_rows_spin)

        self.show_all_checkbox = QCheckBox("Show all", self.controls_frame)
        controls_layout.addLayout(controls_form)
        controls_layout.addWidget(self.show_all_checkbox)

        self.read_column_names_btn = QPushButton("Read column names", self.controls_frame)
        self.paste_clipboard_btn = QPushButton("Paste from clipboard", self.controls_frame)
        controls_layout.addWidget(self.read_column_names_btn)
        controls_layout.addWidget(self.paste_clipboard_btn)
        self.preview_status_label = QLabel("Showing 0 / 0 rows", self.controls_frame)
        controls_layout.addWidget(self.preview_status_label)

        controls_layout.addStretch(1)

        self.round_decimals_spin = QSpinBox(self.controls_frame)
        self.round_decimals_spin.setRange(0, 10)
        self.round_decimals_spin.setValue(0)
        controls_form_bottom = QFormLayout()
        controls_form_bottom.addRow("Round decimals", self.round_decimals_spin)
        controls_layout.addLayout(controls_form_bottom)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self.controls_frame,
        )
        controls_layout.addWidget(self.button_box)

        # Right: top mapping + bottom preview
        self.right_splitter = QSplitter(Qt.Orientation.Vertical, self)

        self.mapping_table = QTableWidget(self.right_splitter)
        self.mapping_table.setObjectName("mapping_table")
        self.mapping_table.setRowCount(4)
        self.mapping_table.setVerticalHeaderLabels(
            ["Unit Type", "Unit", "Base column", "Column name"]
        )
        self.mapping_table.setColumnCount(0)

        self.preview_table = QTableWidget(self.right_splitter)
        self.preview_table.setObjectName("preview_table")
        self.preview_table.setColumnCount(0)
        self.preview_table.setRowCount(0)

        self.right_splitter.setStretchFactor(0, 2)
        self.right_splitter.setStretchFactor(1, 5)
        self.right_splitter.setSizes([220, 480])

        root_layout.addWidget(self.controls_frame, 0)
        root_layout.addWidget(self.right_splitter, 1)

    def _connect_signals(self) -> None:
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.read_column_names_btn.clicked.connect(self._on_read_column_names)
        self.paste_clipboard_btn.clicked.connect(self._on_paste_clipboard)
        self.show_all_checkbox.toggled.connect(self._refresh_preview_table)
        self.max_rows_spin.valueChanged.connect(self._refresh_preview_table)
        self.round_decimals_spin.valueChanged.connect(self._refresh_preview_table)

    def _on_read_column_names(self) -> None:
        # Reuse clipboard parsing and only refresh mapping column headers.
        headers, _rows = self._parse_clipboard_table()
        if not headers:
            return
        self._set_mapping_columns(headers)

    def _on_paste_clipboard(self) -> None:
        
        headers, rows = self._parse_clipboard_table()
        if not headers:
            return
        self._headers = headers
        self._rows = rows
        self._set_mapping_columns(headers)
        self._set_preview_table(headers, rows)

    def _parse_clipboard_table(self) -> tuple[list[str], list[list[str]]]:
        
        clipboard = QApplication.clipboard()
        text = clipboard.text().strip()
        if not text:
            QMessageBox.warning(self, "Clipboard is empty", "No tabular text found in clipboard.")
            return [], []

        sample = text[:1000]
        delimiter = "\t"
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters="\t,;|")
            delimiter = dialect.delimiter
        except csv.Error:
            # Keep tab as default (most spreadsheet copy operations).
            pass

        reader = csv.reader(StringIO(text), delimiter=delimiter)
        parsed_rows = [[cell.strip() for cell in row] for row in reader if row]
        if not parsed_rows:
            QMessageBox.warning(self, "Invalid clipboard data", "Could not parse rows from clipboard.")
            return [], []

        headers = parsed_rows[0]
        data_rows = parsed_rows[1:]
        return headers, data_rows

    def _set_mapping_columns(self, headers: list[str]) -> None:
        self.mapping_table.setColumnCount(len(headers))
        self.mapping_table.setHorizontalHeaderLabels(headers)
        for col_idx, header in enumerate(headers):
            self.mapping_table.setItem(3, col_idx, QTableWidgetItem(header))

    def _set_preview_table(self, headers: list[str], rows: list[list[str]]) -> None:
        display_rows = rows if self.show_all_checkbox.isChecked() else rows[: self.max_rows_spin.value()]
        self.preview_table.clear()
        self.preview_table.setColumnCount(len(headers))
        self.preview_table.setHorizontalHeaderLabels(headers)
        self.preview_table.setRowCount(len(display_rows))

        for row_idx, row in enumerate(display_rows):
            for col_idx in range(len(headers)):
                value = row[col_idx] if col_idx < len(row) else ""
                value = self._format_preview_value(value)
                self.preview_table.setItem(row_idx, col_idx, QTableWidgetItem(value))
        self._update_preview_status(len(display_rows), len(rows))

    def _refresh_preview_table(self) -> None:
        if not self._headers:
            return
        self._set_preview_table(self._headers, self._rows)

    def _format_preview_value(self, value: str) -> str:
        decimals = self.round_decimals_spin.value()
        if decimals < 0:
            return value
        try:
            number = float(value)
        except (TypeError, ValueError):
            return value
        return f"{number:.{decimals}f}"

    def _update_preview_status(self, shown_count: int, total_count: int) -> None:
        self.preview_status_label.setText(f"Showing {shown_count} / {total_count} rows")

