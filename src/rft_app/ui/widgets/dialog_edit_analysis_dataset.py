from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLabel, QMessageBox, QWidget

from project import AnalysisObject, ColumnSpec, DataSet, ProjectDataManager
from ui.main_window.project_signals import ProjectSignals
from ui.widgets.dialog_data_loader_analysis import DataLoaderDialogAnalysis


class DialogEditViewAnalysisDataSet(DataLoaderDialogAnalysis):
    # Inherited variables (declared here for readability / typing; set by bases)

    # Project
    # DataLoaderDialogAnalysis
    project: ProjectDataManager | None

    # Module
    # DataLoaderDialogAnalysis
    analysis_dataset: DataSet | None
    selected_dataset: DataSet | None
    selected_columns: list[str]
    selected_columns_specs: list[ColumnSpec]
    result_analysis: AnalysisObject | None

    # Initialisation Methods
    # DataLoaderDialogAnalysis
    """
    (_build_ui)
    (_connect_signals)
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        project: ProjectDataManager | None = None,
        analysis: AnalysisObject | None = None,
        signals: ProjectSignals | None = None,
        ) -> None:
        # Set project variables before super so overridden _build_ui can use them
        self.analysis: AnalysisObject | None = analysis
        self.signals: ProjectSignals | None = signals

        # Set module variables

        # Initialisation methods
        super().__init__(parent, project)

    #--------Private UI--------

    def _build_ui(self) -> None:
        super()._build_ui()

        # Modify the dialog window for update of dataset, rather than starting a new analysis from scratch
        self.setWindowTitle(f"Update Analysis Dataset: {self.analysis.name}")

        # Replace the 'name' line edit with a label
        idx = self.data_frame_layout.indexOf(self.name_lineEdit)
        self.data_frame_layout.removeWidget(self.name_lineEdit)
        self.name_lineEdit.hide()
        self.name_lineEdit.deleteLater()

        self.analysis_name = QLabel()
        self.analysis_name.setText(f"Analysis: {self.analysis.name}")
        font = self.analysis_name.font()
        font.setBold(True)
        self.analysis_name.setFont(font)
        self.data_frame_layout.insertWidget(idx, self.analysis_name)

        # Replace the button name
        self.start_btn.setText("Replace Dataset")

    def _connect_signals(self) -> None:
        super()._connect_signals()
        self.start_btn.clicked.disconnect(self._start_analysis)
        self.start_btn.clicked.connect(self._replace_dataset)

    def _get_analysis_name(self) -> str:
        return self.analysis.name

    def _replace_dataset(self) -> None:
        new = self._create_analysis_object()

        result = QMessageBox.question(
            self,
            "Confirm Dataset replacement",
            (
                f"Are you sure you want to change the dataset associated with {self.analysis.name}?\n"
                f"\nThis action will affect all views under the analysis, not just the current view.\n"
                f"\nThis action is reversible."
                ),
            )
        if result is QMessageBox.StandardButton.No:
            return

        # Update the analysis object (SSOT)
        self.analysis.source_datasets = new.source_datasets
        self.analysis.analysis_dataset = new.analysis_dataset
        self.analysis.vert_depth_src_col = new.vert_depth_src_col
        self.analysis.formation_pres_src_col = new.formation_pres_src_col

        # Emit the signal and complete the change
        self.project.mark_modified()
        self.signals.analysis_dataset_changed.emit(self.analysis)
        self.accept()

    #--------Public API--------
    # (none)
