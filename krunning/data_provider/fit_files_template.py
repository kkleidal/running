import os

from .template import DataProviderTemplate


class FitFilesDataProviderTemplate(DataProviderTemplate):
    def __init__(self, directory: str = "data", **kwargs):
        super().__init__(**kwargs)
        self.directory = directory
        self.files = [
            os.path.join(self.directory, name)
            for name in sorted(os.listdir(self.directory))
            if name.endswith(".fit")
        ]

    @property
    def cache_key(self):
        return self.files
