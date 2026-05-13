from __future__ import annotations
from typing import Optional
import pandas as pd
from units.units_manager import BUILT_IN_UNIT_SYSTEMS, UnitSystem
from .models import Analysis, ColumnSpec, LoadedDataSet


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
        self.project_analyses: list[Analysis]= []

    @property
    def available_unit_systems(self)-> tuple[UnitSystem,...]:
        "Built-ins + user defined. Used to populate the project units combo"
        return BUILT_IN_UNIT_SYSTEMS + tuple(self.user_unit_systems)

    def add_loaded_dataset(
        self,
        df: pd.DataFrame,
        column_specs: list[ColumnSpec],
        name: Optional[str] = None,
                        ) -> str:
        """Store a DataFrame and its column specs under a unique key.

        Rules:
          - If `name` is None or empty, auto-generate one ("dataset_1", ...).
          - If `name` already exists, append a numeric suffix to make it unique.
        Returns the key actually used.
        """
        chosen = self._unique_name(name)
        loaded_dataset = LoadedDataSet(
            name = chosen,
            dataframe = df, 
            column_specs= list(column_specs),
        )
        self.loaded_datasets.append (loaded_dataset)
        return chosen

    def get_dataframe(self, name: str) -> pd.DataFrame:
        return self.datasets[name]

    def get_column_specs(self, name: str) -> list[ColumnSpec]:
        return self.column_specs_by_dataset[name]

    def list_datasets(self) -> list[str]:
        return list(self.datasets.keys())

    def _unique_name(self, name: Optional[str]) -> str:
        """Generate a unique dataset key based on `name` and the current store."""
        existing_names = {dataset.name for dataset in self.loaded_datasets}
        
        if not name:
            i = len(existing_names) + 1
            candidate = f"dataset_{i}"
            while candidate in existing_names:
                i += 1
                candidate = f"dataset_{i}"
            return candidate

        if name not in existing_names:
            return name

        i = 2
        while f"{name}_{i}" in existing_names:
            i += 1
        return f"{name}_{i}"

    def _get_loaded_dataset(self, name:str) -> LoadedDataSet:
        for dataset in self.loaded_datasets:
            if dataset.name == name:
                return dataset
        raise KeyError (name)