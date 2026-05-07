from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd

from .models import ColumnSpec


class ProjectDataManager:
    """Owns imported DataFrames and their per-column unit metadata.

    Units-only first pass: no DataSetMeta, no persistence. Just enough to
    receive (DataFrame, column_specs) from the data loader and hand them
    back out by name.
    """

    def __init__(self) -> None:
        self.datasets: Dict[str, pd.DataFrame] = {}
        self.column_specs_by_dataset: Dict[str, List[ColumnSpec]] = {}

    def add_dataframe(
        self,
        df: pd.DataFrame,
        column_specs: List[ColumnSpec],
        name: Optional[str] = None,
    ) -> str:
        """Store a DataFrame and its column specs under a unique key.

        Rules:
          - If `name` is None or empty, auto-generate one ("dataset_1", ...).
          - If `name` already exists, append a numeric suffix to make it unique.

        Returns the key actually used.
        """
        chosen = self._unique_name(name)
        self.datasets[chosen] = df
        self.column_specs_by_dataset[chosen] = list(column_specs)  # defensive copy
        return chosen

    def get_dataframe(self, name: str) -> pd.DataFrame:
        return self.datasets[name]

    def get_column_specs(self, name: str) -> List[ColumnSpec]:
        return self.column_specs_by_dataset[name]

    def list_datasets(self) -> List[str]:
        return list(self.datasets.keys())

    def _unique_name(self, name: Optional[str]) -> str:
        """Generate a unique dataset key based on `name` and the current store."""
        if not name:
            i = len(self.datasets) + 1
            candidate = f"dataset_{i}"
            while candidate in self.datasets:
                i += 1
                candidate = f"dataset_{i}"
            return candidate

        if name not in self.datasets:
            return name

        i = 2
        while f"{name}_{i}" in self.datasets:
            i += 1
        return f"{name}_{i}"