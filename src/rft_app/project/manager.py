
from datetime import datetime

import pandas as pd
from units.units_manager import BUILT_IN_UNIT_SYSTEMS, UnitSystem
from .models import AnalysisObject, ColumnSpec, DataSet, DataSetLogEntry
from utilities import unique_name



class ProjectDataManager:
    """Owns imported DataFrames and their per-column unit metadata.

    Units-only first pass: no DataSetMeta, no persistence. Just enough to
    receive (DataFrame, column_specs) from the data loader and hand them
    back out by name.
    """

    def __init__(self) -> None:
        self.datasets :list[DataSet]=[]
        self.user_unit_systems:list[UnitSystem] = []
        self.current_unit_system: UnitSystem = BUILT_IN_UNIT_SYSTEMS[2] #default to Field
        self.analyses: list[AnalysisObject]= []
        self._is_modified: bool =False

    @property
    def available_unit_systems(self)-> tuple[UnitSystem,...]:
        "Built-ins + user defined. Used to populate the project units combo"
        return BUILT_IN_UNIT_SYSTEMS + tuple(self.user_unit_systems)

    def add_loaded_dataset(
        self,
        df: pd.DataFrame,
        column_specs: list[ColumnSpec],
        name:str,
        info_log:list[DataSetLogEntry],
        user_comment: tuple[datetime, str] | None
                        ) -> str:
        """Store a DataFrame and its column specs under a unique key.

        Rules:
          - Name requested on dataframe data import via the data_loader_project.py file
          - If name is empty, it defaults to "Dataset".
          - If `name` already exists, append a numeric suffix to make it unique.
        Returns the key actually used.
        """
        # Extract the dataset name from the dataset specs
        name =  (name.strip() or "") or "Dataset"

        # Verify if the name is unique or requires changing
        existing_names = {dataset.name for dataset in self.datasets}
        chosen = unique_name(name, existing_names)
        loaded_dataset = DataSet(
            name = chosen,
            dataframe = df, 
            column_specs= list(column_specs),
            info_log = list(info_log) if info_log else[],
            user_comments= [user_comment] if user_comment else []
        )
        self.datasets.append (loaded_dataset)
        return chosen

    def get_dataset_by_name(self, name:str) -> DataSet:
        for dataset in self.datasets:
            if dataset.name == name:
                return dataset
        raise KeyError (name)

    def mark_modified(self)->None:
        self._is_modified = True
    
    def mark_clean(self)->None:
        self._is_modified = False

    @property
    def is_modified(self)->bool:
        return self._is_modified