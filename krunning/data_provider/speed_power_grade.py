from typing import Optional, Tuple, Dict, Any
import numpy as np

from .fit_files_template import FitFilesDataProviderTemplate
from ..fitfile import FitFile


class SpeedPowerFitFilesDataProvider(FitFilesDataProviderTemplate):
    uuid = "290e069f-80a7-422e-a568-66b8d3e23311"

    def __init__(
        self,
        min_pace_per_mile=12,
        min_power=125,
        min_distance_change=0.1,
        grade_range: Optional[Tuple[float, float]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.min_pace_per_mile = min_pace_per_mile
        self.min_power = min_power
        self.min_distance_change = min_distance_change
        self.grade_range = grade_range

    @property
    def cache_key(self):
        return (
            super().cache_key,
            self.min_pace_per_mile,
            self.min_power,
            self.min_distance_change,
            self.grade_range,
        )

    def compute(self) -> Dict[str, Any]:
        speeds = []
        powers = []
        grades = []
        hrs = []
        for filepath in self.files:
            min_speed = pace_to_speed(self.min_pace_per_mile)
            print(filepath)
            with FitFile(filepath) as file:
                df = load_pandas_from_fitfile(file)
                speed = df["enhanced_speed"].to_numpy()
                power = df["Power"].to_numpy()
                distance = df["distance"].to_numpy()
                hr = df["heart_rate"].to_numpy()
                ddistance = difference(distance)
                grade = derivative(df["enhanced_altitude"].to_numpy(), distance)
                mask = (
                    (speed > min_speed)
                    & (power > self.min_power)
                    & (ddistance > self.min_distance_change)
                )
                if self.grade_range is not None:
                    mask &= (grade >= self.grade_range[0]) & (
                        grade <= self.grade_range[1]
                    )

                masked_speed = speed[mask]
                masked_power = power[mask]
                masked_grade = grade[mask]
                masked_hr = hr[mask]

                speeds.append(masked_speed)
                powers.append(masked_power)
                grades.append(masked_grade)
                hrs.append(masked_hr)

        speeds = np.concatenate(speeds, 0)
        powers = np.concatenate(powers, 0)
        grades = 100 * np.concatenate(grades, 0)
        hrs = np.concatenate(hrs)
        return {"speeds": speeds, "powers": powers, "grades": grades, "hrs": hrs}
