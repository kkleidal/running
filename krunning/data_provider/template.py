from abc import ABC, abstractmethod
import os
import gzip
import pickle
from typing import Dict, Any


class DataProviderTemplate(ABC):
    uuid = None

    def __init__(self, cache_directory: str = "cache"):
        os.makedirs(cache_directory, exist_ok=True)
        assert self.uuid is not None
        self.cache_directory = cache_directory

    @property
    @abstractmethod
    def cache_key(self):
        pass

    @abstractmethod
    def compute(self) -> Dict[str, Any]:
        pass

    def get(self):
        cache_key = self.cache_key
        cache_file = os.path.join(self.cache_directory, self.uuid + ".pkl.gz")
        if os.path.exists(cache_file):
            with gzip.open(cache_file, "rb") as f:
                cached = pickle.load(f)
            if cached["cache_key"] == cache_key:
                return cached["data"]
        out = self.compute()
        out = {"cache_key": cache_key, "data": out}
        with gzip.open(cache_file, "wb") as f:
            pickle.dump(out, f)
        return out["data"]
