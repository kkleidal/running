import tempfile
import io
import base64
from typing import Dict, Iterable, List, Any, Optional

from pdf_reports import pug_to_html, write_report
import matplotlib.pyplot as plt

from .base import ReportBuilder, ReportSection, ReportTable


class PDFReportsReportBuilder(ReportBuilder):
    def __init__(self):
        self.__body = PDFReportsReportSection()

    def body(self) -> ReportSection:
        return self.__body

    def write_to(self, path: str):
        with tempfile.NamedTemporaryFile(suffix=".pug", mode="w") as pugfile:
            figures = 0
            for element in self.__body._flatten():
                if element["kind"] == "title":
                    level = max(min(element["level"], 6), 1)
                    pugfile.write("h%d %s\n\n" % (level, element["text"]))
                elif element["kind"] == "paragraph":
                    pugfile.write("p %s\n\n" % (element["text"],))
                elif element["kind"] == "figure":
                    figures += 1
                    pugfile.write(
                        'img(src="%s", alt="Figure %d")\n\n' % (element["url"], figures)
                    )
                elif element["kind"] == "table":
                    pugfile.write("table.ui.celled.table\n")
                    table: PDFReportsReportTable = element["table"]
                    for i, row in enumerate(table._rows):
                        row = [str(el) for el in row]
                        cell_el = "td"
                        if i == 0:
                            pugfile.write("  thead\n")
                            cell_el = "th"
                        elif i == 1:
                            pugfile.write("  tbody\n")
                        pugfile.write("    tr\n")
                        for cell in row:
                            pugfile.write("      %s %s\n" % (cell_el, cell))
                    pugfile.write("\n")
                else:
                    raise NotImplementedError(str(element))
            pugfile.flush()
            html = pug_to_html(pugfile.name)
            write_report(html, path)


class PDFReportsReportSection(ReportSection):
    def __init__(self):
        self.__elements: List[Dict[str, Any]] = []

    def _flatten(self) -> Iterable[Dict[str, Any]]:
        for element in self.__elements:
            if element["kind"] == "section":
                yield from element["section"]._flatten()
            else:
                yield element

    def add_section(self) -> ReportSection:
        sec = PDFReportsReportSection()
        self.__elements.append({"kind": "section", "section": sec})
        return sec

    def add_title(self, text: str, level: int = 1):
        self.__elements.append({"kind": "title", "text": text, "level": level})

    def add_paragraph(self, text: str):
        self.__elements.append({"kind": "paragraph", "text": text})

    def add_table(self) -> ReportTable:
        table = PDFReportsReportTable()
        self.__elements.append({"kind": "table", "table": table})
        return table

    def add_figure(self, figure: plt.Figure, caption: Optional[str] = None):
        buf = io.BytesIO()
        figure.set_size_inches(6, 4)
        figure.set_dpi(300)
        figure.savefig(buf, format="png")

        b64url = "data:image/png;base64,%s" % base64.b64encode(buf.getvalue()).decode(
            "utf8"
        )
        self.__elements.append({"kind": "figure", "url": b64url})
        plt.clf()


class PDFReportsReportTable(ReportTable):
    def __init__(self):
        self._rows = []

    def add_row(self, cells: List[str]):
        self._rows.append(cells)
