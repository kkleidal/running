from abc import ABC, abstractmethod
from typing import Optional, List, Any
import argparse

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
