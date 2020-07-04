from abc import ABC, abstractmethod
import matplotlib.pyplot as plt


class PlotBuilder(ABC):
    @abstractmethod
    def add_subplot(
        self,
        x_values,
        y_values,
        title=None,
        y_label=None,
        x_label=None,
        y_lim=None,
        average=None,
    ):
        pass

    @abstractmethod
    def preview(self):
        pass

    @abstractmethod
    def display(self):
        pass

    @abstractmethod
    def save_to_directory(self, directory_path: str):
        pass


class _MatplotlibPlot:
    def __init__(self, x_values, y_values, title, y_label, x_label, y_lim, average):
        self.x_values = x_values
        self.y_values = y_values
        self.title = title
        self.y_label = y_label
        self.x_label = x_label
        self.y_lim = y_lim
        self.average = average


class MatplotlibPlotBuilder(PlotBuilder):
    def __init__(self):
        self.__subplots = []

    def add_subplot(
        self,
        x_values,
        y_values,
        title=None,
        y_label=None,
        x_label=None,
        y_lim=None,
        average=None,
    ):
        self.__subplots.append(
            _MatplotlibPlot(x_values, y_values, title, y_label, x_label, y_lim, average)
        )

    def __build_plot(self):
        if len(self.__subplots) == 0:
            raise ValueError("No subplots added")
        f, axes = plt.subplots(len(self.__subplots), 1)
        subplot: _MatplotlibPlot
        for subplot, ax in zip(self.__subplots, axes):
            ax.plot(subplot.x_values, subplot.y_values)
            if subplot.title:
                ax.set_title(subplot.title)
            if subplot.average is not None:
                ax.axhline(subplot.average, c="r", ls="--")
            if subplot.y_lim:
                ax.set_ylim(subplot.y_lim)
            if subplot.y_label:
                ax.set_ylabel(subplot.y_label)
            if subplot.x_label:
                ax.set_xlabel(subplot.x_label)
        f.set_size_inches(
            (2 + subplot.x_values.shape[0] / 1000, 2 * len(self.__subplots))
        )
        return f

    def preview(self):
        self.__build_plot()
        plt.show()

    def display(self):
        raise NotImplementedError

    def save_to_directory(self, directory_path: str):
        raise NotImplementedError
