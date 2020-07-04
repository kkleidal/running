import numpy as np
import pandas as pd
from typing import Tuple, Union


def smooth_sliding_time_window(
    time: np.ndarray, series: np.ndarray, window: Union[int, float]
) -> np.ndarray:
    """Smooth a time series using a trailing time-window (so could be used in an online fashion).

    Args:
        time: T ndarray. timestamps of samples, in seconds
        series: T ndarray. value of samples
        window: size of window, in seconds

    Returns:
        T ndarray. Smoothed series
    """
    out = np.zeros_like(series)
    total = 0
    length = 0
    start = 0
    for i in range(time.shape[0]):
        total += series[i]
        length += 1
        now = time[i]
        while now - time[start] > window:
            total -= series[start]
            length -= 1
            start += 1
        assert length == i - start + 1
        out[i] = total / length
    return out


def percentile(x: np.ndarray, percentile: float = 99) -> Tuple[float, float]:
    """Get the (low, high) limit for the series by only including the data within the given percentile.

    For example, if percentile is 99, (1st percentile, 99th percentile) will be returned.

    Also, if percentile is 1, (1st percentile, 99th percentile) will be returned.

    Args:
        x: the series
        percentile: the percentile, beyond which to exclude data.

    Returns:
        (low, high) percentiles of series
    """
    percentile = max(percentile, 100 - percentile)
    high = np.percentile(x, percentile)
    low = np.percentile(x, 100 - percentile)
    return (low, high)


def relative_seconds_from_timestamps(timestamps: pd.Series) -> pd.Series:
    """Get the number of relative seconds (since start) from timestamps.

    Args:
        timestamps: pandas series of Timestamps

    Returns:
        Pandas float64 series of seconds since start
    """
    if len(timestamps) == 0:
        raise ValueError("Undefined behavior for empty series")
    first = timestamps.loc[0]
    seconds = (timestamps - first) / np.timedelta64(1, "s")
    return seconds
