import fitparse
import pandas as pd
from typing import Dict, List, Optional, Iterator, Any


class FitFile:
    """Used to read Garmin's raw fit file."""

    def __init__(self, path: str):
        """Open fit file

        Args:
            path: Path to the .fit file
        """
        self.__fitfile = fitparse.FitFile(path)
        self.__fields = None
        self.__length = None

    def close(self):
        """Close the fit file."""
        self.__fitfile.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __populate(self):
        """Populate lazily populated fields."""
        fields = {}
        i = 0
        for record in self.__fitfile.get_messages("record"):
            i += 1
            for record_data in record:
                fields[record_data.name] = record_data.units
        self.__fields = fields
        self.__length = i

    @property
    def fields(self) -> Dict[str, Optional[str]]:
        """Get the fields and the units of the fields

        The unit will be None if there is no unit for that field.

        Returns:
            dictionary mapping field name to unit. Fields without units will have unit, None
        """
        if self.__fields is None:
            self.__populate()
        return self.__fields

    def __len__(self) -> int:
        """Get the number of records in the fit file"""
        if self.__length is None:
            self.__populate()
        return self.__length

    def get_fields(self, names: List[str]) -> Iterator[List[Any]]:
        """Generate a list of records. Each yielded list will be parallel to the list of field names you request.

        Args:
            names: ordered list of field names you want to load

        Yields:
            Parallel lists to names with values for each requested field, in the order that the fields were requested
        """
        for name in names:
            if name not in self.fields:
                raise KeyError(name)
        class_map = {name: i for i, name in enumerate(names)}
        for record in self.__fitfile.get_messages("record"):
            out = [None for _ in class_map]
            for record_data in record:
                if record_data.name in class_map:
                    out[class_map[record_data.name]] = record_data.value
            yield out


def load_pandas_from_fitfile(
    fitfile: FitFile, fields: Optional[List[str]] = None
) -> pd.DataFrame:
    """Load records from a fit file into a pandas DataFrame.

    Args:
        fitfile: the fit file to load from
        fields: only load these fields. If not specified, loads all fields available in the fitfile

    Returns:
        pd.DataFrame containing fit file records
    """
    if fields is None:
        fields = sorted(fitfile.fields)
    data = {field: [] for field in fields}
    for record in fitfile.get_fields(fields):
        for key, value in zip(fields, record):
            data[key].append(value)
    return pd.DataFrame(data)
