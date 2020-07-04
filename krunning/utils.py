import numpy as np

from .constants import SECONDS_PER_MINUTE, METERS_PER_MILE


def speed_to_pace(speed):
    """
    Args:
        speed: speed in meters per second

    Returns:
        pace in minutes per mile
    """
    return (1 / speed) * (1 / SECONDS_PER_MINUTE) * METERS_PER_MILE


def pace_to_speed(pace):
    return 1 / (pace * SECONDS_PER_MINUTE / METERS_PER_MILE)


def difference(x):
    dx = x[1:] - x[:-1]
    return np.pad(dx, [[1, 0]], mode="constant", constant_values=0)


def derivative(y, x, eps=1e-12):
    dy = difference(y)
    dx = difference(x)
    out = dy / np.maximum(dx, eps)
    return out
