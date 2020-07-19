from abc import ABC, abstractmethod
from typing import Optional, List, Any
import argparse
import pandas as pd

import matplotlib.pyplot as plt

from ..registry import Registry


class ReportBuilder(ABC):
    @abstractmethod
    def body(self) -> "ReportSection":
        pass

    @abstractmethod
    def write_to(self, path: str):
        pass


class ReportSection(ABC):
    @abstractmethod
    def add_section(self) -> "ReportSection":
        pass

    @abstractmethod
    def add_title(self, text: str, level: int = 1):
        pass

    @abstractmethod
    def add_paragraph(self, text: str):
        pass

    @abstractmethod
    def add_table(self) -> "ReportTable":
        pass

    def add_table_from_df(self, df: pd.DataFrame):
        table = self.add_table()
        table.add_row(df.columns)
        for _, row in df.iterrows():
            table.add_row([str(cell) for cell in row])

    @abstractmethod
    def add_figure(self, figure: plt.Figure, caption: Optional[str] = None):
        pass


class ReportTable(ABC):
    @abstractmethod
    def add_row(self, cells: List[str]):
        pass


class ReportGenerator(ABC):
    @abstractmethod
    def build_parser(self, parser: argparse.ArgumentParser):
        pass

    def generate_report(self, args: Any, report_builder: ReportBuilder):
        pass


reports: Registry[ReportGenerator] = Registry()
