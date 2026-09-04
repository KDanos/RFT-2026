import pandas as pd
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from project import AnalysisObject, AnalysisView, ColumnSpec, ProjectDataManager
from ..analysis_view.analysis_view_data_manager import insert_excess_pressure_column
from utilities import unique_name


class NewViewDialog(QDialog):
    def __init__(
        self,
        parent=None,
        analysis: AnalysisObject | None = None,
        project: ProjectDataManager | None = None,
    ) -> None:
        super().__init__(parent)

        # Set project variables
        self.project = project
        self.analysis = analysis

        # Set module variables
        self.copy_from: AnalysisView | None = None
        self.new_view_name = ""
        self.df: pd.DataFrame | None = None
        self.column_specs: list[ColumnSpec] = []
        self._has_existing_views = (
            analysis is not None and len(analysis.analysis_views) > 0
        )

        # Initialisation methods
        self._build_ui()
        self._connect_signals()

    #--------Private UI--------

    def _build_ui(self) -> None:
        # Design the window
        self.setWindowIcon(QIcon("resources/images/CY_LOGO_RGB.jpg"))
        self.setWindowTitle(f"{self.analysis.name}: Start a new view")

        # Chose a name
        self.name_line_edit = QLineEdit()
        self.name_line_edit.setPlaceholderText("New View Name")

        # Available views
        if self._has_existing_views:
            avail_views_layout = QHBoxLayout()
            avail_views_label = QLabel("Available Views: ")
            self.views_combo = QComboBox(self)
            self.existing_views_list = [
                (view.name, view) for view in self.analysis.analysis_views
            ]
            for name, view in self.existing_views_list:
                self.views_combo.addItem(name, view)

            avail_views_layout.addWidget(avail_views_label)
            avail_views_layout.addWidget(self.views_combo)

            # Button Box
            self.button_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok
                | QDialogButtonBox.StandardButton.Cancel,
                parent=self,
            )
            self.button_box.button(QDialogButtonBox.StandardButton.Ok).setText(
                "Copy Existing View"
            )
            self.button_box.button(QDialogButtonBox.StandardButton.Cancel).setText(
                "Create Empty View"
            )
        else:
            self.button_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Ok
                | QDialogButtonBox.StandardButton.Cancel,
                parent=self,
            )

        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.name_line_edit)
        if self._has_existing_views:
            main_layout.addLayout(avail_views_layout)
        main_layout.addWidget(self.button_box)

    def _connect_signals(self) -> None:
        self.button_box.accepted.connect(self._on_accept)
        if self._has_existing_views:
            self.button_box.rejected.connect(self._on_create_empty)
        else:
            self.button_box.rejected.connect(self.reject)

    def _create_new_view_instance(self) -> AnalysisView:
        new_view_object = AnalysisView(
            name=self.new_view_name,
            analysis_object=self.analysis,
            df=self.df,
            column_specs=self.column_specs,
        )
        return new_view_object

    def _make_name_unique(self) -> None:
        if self.new_view_name == "":
            self.new_view_name = "View"
        if len(self.analysis.analysis_views) > 0:
            existing_names = [view.name for view in self.analysis.analysis_views]
        else:
            return

        self.new_view_name = unique_name(self.new_view_name, existing_names)

    def _on_accept(self) -> None:
        if self._has_existing_views:
            self.copy_from = self.views_combo.currentData()
            self.new_view_name = (
                self.name_line_edit.text().strip() or self.views_combo.currentText()
            )
            self.df = self.copy_from.df.copy()
            self.column_specs = list(self.copy_from.column_specs)
            self.df, self.column_specs = insert_excess_pressure_column(
                self.df, self.column_specs, self.project
            )  # just in case something went wrong and a view ended up with the wrong content
        else:
            self.copy_from = None
            self.new_view_name = self.name_line_edit.text().strip()
            self.df = self.analysis.analysis_dataset.dataframe.copy()
            self.column_specs = list(self.analysis.analysis_dataset.column_specs)
            self.df, self.column_specs = insert_excess_pressure_column(
                self.df, self.column_specs, self.project
            )

        #Make sure the new view name is unique
        self._make_name_unique()
        #Create the new view instance
        new_view = self._create_new_view_instance()
        self.analysis.analysis_views.append(new_view)
        self.accept()

    def _on_create_empty(self) -> None:
        self.copy_from = None
        self.new_view_name = self.name_line_edit.text().strip()
        self.df = self.analysis.analysis_dataset.dataframe.copy()
        self.column_specs = list(self.analysis.analysis_dataset.column_specs)
        self.df, self.column_specs = insert_excess_pressure_column(
            self.df, self.column_specs, self.project
        )
        self._make_name_unique()
        new_view = self._create_new_view_instance()
        self.analysis.analysis_views.append(new_view)
        self.accept()

    #--------Public API--------

    def reject(self) -> None:
        #no append
        super().reject()
