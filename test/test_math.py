import numpy as np
import datetime
import pandas as pd

from krunning import (
    smooth_sliding_time_window,
    percentile,
    relative_seconds_from_timestamps,
)


def test_smooth_sliding_time_window():
    input_array = np.array([1, 1.5, 2, 3, 3.14, 5, 7.9, 8.1])
    timestamps = np.arange(len(input_array))
    window_size_seconds = 2.01
    expected_output = np.array(
        [1, 1.25, 1.5, 6.5 / 3, 8.14 / 3, 11.14 / 3, 16.04 / 3, 7]
    )
    output = smooth_sliding_time_window(timestamps, input_array, window_size_seconds)
    assert np.allclose(output, expected_output)


def test_percentile():
    N = 1000
    prng = np.random.RandomState(42)
    data = prng.normal(0, 1, size=[N])

    assert percentile(data) == (np.percentile(data, 1), np.percentile(data, 99))
    assert percentile(data, 98) == (np.percentile(data, 2), np.percentile(data, 98))
    assert percentile(data, 2) == (np.percentile(data, 2), np.percentile(data, 98))


def test_relative_seconds_from_timestamps():
    start = datetime.datetime(2020, 1, 1)
    second = datetime.timedelta(seconds=1)
    df = pd.DataFrame({"timestamp": [start, start + second, start + 2.5 * second],})
    seconds = relative_seconds_from_timestamps(df["timestamp"])
    assert np.allclose(seconds.to_numpy(), np.array([0, 1, 2.5]))
