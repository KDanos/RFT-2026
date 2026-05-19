from typing import Optional
import pandas as pd
from units.units_manager import BUILT_IN_UNIT_SYSTEMS, UnitSystem
from .models import AnalysisObject, ColumnSpec, LoadedDataSet
from utils.naming import unique_name



class ProjectDataManager:
    """Owns imported DataFrames and their per-column unit metadata.

    Units-only first pass: no DataSetMeta, no persistence. Just enough to
    receive (DataFrame, column_specs) from the data loader and hand them
    back out by name.
    """

    def __init__(self) -> None:
        self.loaded_datasets :list[LoadedDataSet]=[]
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
        name: str = "Dataset",
                        ) -> str:
        """Store a DataFrame and its column specs under a unique key.

        Rules:
          - Name defaults to "Dataset".
          - If `name` already exists, append a numeric suffix to make it unique.
        Returns the key actually used.
        """
        existing_names = {dataset.name for dataset in self.loaded_datasets}
        chosen = unique_name(name, existing_names)
        loaded_dataset = LoadedDataSet(
            name = chosen,
            dataframe = df, 
            column_specs= list(column_specs),
        )
        self.loaded_datasets.append (loaded_dataset)
        return chosen

    def get_dataframe(self, name: str) -> pd.DataFrame:
        return self._get_loaded_dataset(name).dataframe

    def get_column_specs(self, name: str) -> list[ColumnSpec]:
        return self._get_loaded_dataset(name).column_specs

    def list_datasets(self) -> list[str]:
        return list(dataset.name for dataset in self.loaded_datasets)

    def _get_loaded_dataset(self, name:str) -> LoadedDataSet:
        for dataset in self.loaded_datasets:
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