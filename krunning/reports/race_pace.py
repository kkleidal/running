import argparse
from typing import List
import numpy as np
import scipy
import scipy.stats
import matplotlib.pyplot as plt
import seaborn as sns

from ..constants import KG_PER_LB
from ..data_provider import SpeedPowerFitFilesDataProvider
from ..reports_gen import reports, ReportGenerator, ReportBuilder


@reports.register("race_pace")
class RacePaceGenerator(ReportGenerator):
    def build_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument("--not-only-flat", action="store_true")
        parser.add_argument("--critical-power", required=True, type=int)
        parser.add_argument("--weight-lbs", required=True, type=float)
        parser.add_argument(
            "--race-powers-from-stryd", required=True, nargs="+", type=int
        )
        parser.add_argument("--race-distance-meters", required=True, type=int)
        pass

    def generate_report(self, args, report_builder: ReportBuilder):
        # Adapt inputs
        only_flat: bool = not args.not_only_flat
        cp: int = args.critical_power
        weight: float = args.weight_lbs * KG_PER_LB
        race_powers_from_stryd: List[int] = list(args.race_powers_from_stryd)
        race_distance: int = args.race_distance_meters

        # Load Data
        provider = SpeedPowerFitFilesDataProvider()
        data = provider.get()
        powers = data["powers"]
        speeds = data["speeds"]
        grades = data["grades"]

        # Color range for grade
        grade_color_range_percentile = 5
        grade_color_range = (
            np.percentile(grades, grade_color_range_percentile),
            np.percentile(grades, 100 - grade_color_range_percentile),
        )

        # If only flat, drop samples from lower or higher grades
        if only_flat:
            mask = (grades >= -0.5) & (grades <= 0.5)
            powers = powers[mask]
            speeds = speeds[mask]
            grades = grades[mask]

        # Convert power to weight normalized power
        power_per_weight = powers / weight

        # Regress efficiency
        m = np.average(speeds / power_per_weight)
        std = np.std(speeds / power_per_weight)
        conf_interval = 95
        conf_interval = std * scipy.stats.norm.ppf(1 - (100 - conf_interval) / 100)
        X = np.linspace(0, np.max(power_per_weight), 1000)

        body = report_builder.body()
        body.add_title("Ken's Race Report: %dm" % race_distance)

        sec = body.add_section()
        sec.add_title("Efficiency", level=2)
        sec.add_paragraph(
            "To get efficiency, we divide speed by weight normalized power. "
            "Intuitively, this represents how efficiently you're converting energy into speed."
        )
        sns.kdeplot(speeds / power_per_weight)
        plt.ylabel("Density")
        plt.xlabel("Efficiency (m/s) / (W/kg)")
        sec.add_figure(plt.gcf())

        sec = body.add_section()
        sec.add_title("Pace versus Normalized Power", level=2)
        sec.add_paragraph(
            "Here is a scatter plot of pace versus normalized power. "
            "Each sample is a sample recorded by my Garmin + Stryd (usually one per second) over the past month. "
            "The color represents the grade (uphill being positive grade, downhill negative grade)."
        )
        sec.add_paragraph(
            "The orange dotted line represents the critical power. The red lines show the "
            "goal race powers recommended by Stryd."
        )
        sec.add_paragraph(
            "The blue line represents the average efficiency "
            "(pace = efficiency * weight normalized power). The dotted blue lines represent "
            "the 95 confidence interval for efficiency."
        )
        plt.scatter(
            power_per_weight,
            speeds,
            c=grades,
            s=0.2,
            marker="x",
            vmin=grade_color_range[0],
            cmap="plasma",
            vmax=grade_color_range[1],
        )
        plt.plot(
            X,
            m * X,
            c="b",
            label="speed = (%.3f +/- %.3f) * norm power" % (m, conf_interval),
        )
        plt.plot(X, (m + conf_interval) * X, c="b", ls="--")
        plt.plot(X, (m - conf_interval) * X, c="b", ls="--")
        plt.axvline(cp / weight, color="orange", ls="--", label="Critical Power")
        table_rows = []
        for goal_power in race_powers_from_stryd:
            goal_power_per_weight = goal_power / weight
            goal_speed = m * goal_power_per_weight
            goal_speed_std = conf_interval * goal_power_per_weight
            goal_time_seconds = int(race_distance / goal_speed)
            goal_time_seconds_lower = int(race_distance / (goal_speed + goal_speed_std))
            goal_time_seconds_upper = int(race_distance / (goal_speed - goal_speed_std))
            t2s = lambda time_seconds: "%d:%02d" % (
                time_seconds // 60,
                time_seconds % 60,
            )
            table_rows.append(
                (
                    goal_power,
                    "%.2f" % goal_power_per_weight,
                    t2s(goal_time_seconds_lower),
                    t2s(goal_time_seconds),
                    t2s(goal_time_seconds_upper),
                )
            )
            plt.hlines(
                y=goal_speed, xmin=0, xmax=goal_power_per_weight, color="red", zorder=1
            )
            plt.vlines(
                x=goal_power_per_weight, ymin=0, ymax=goal_speed, color="red", zorder=1
            )
        plt.legend()
        cbar = plt.colorbar()
        cbar.set_label("Grade (%)", rotation=270)
        plt.ylim([0, None])
        plt.xlim([0, None])
        plt.ylabel("Speed (m/s)")
        plt.xlabel("Weight Normalized Power (W / kg)")
        sec.add_figure(plt.gcf())

        sec.add_paragraph(
            "You can see three clear modes: aerobic runs, lactate threshold (tempo) runs, and intervals. "
            "Note that I have very little time spent in the top race power recommended by Stryd, "
            "which makes me doubtful that I could sustain that for 5k. The middle power range is more "
            "plausible."
        )

        sec = body.add_section()
        sec.add_title("Expected Race Times", level=2)

        sec.add_paragraph(
            "Using the expected and upper/lower bounds on efficiency, we can compute "
            "expected race times at each power recommended by Stryd:"
        )

        table = sec.add_table()
        table.add_row(
            [
                "Goal Power",
                "Goal Normalized Power",
                "Lower Bound Time",
                "Expected Time",
                "Upper Bound Time",
            ]
        )
        for row in table_rows:
            table.add_row(list(row))

        sec.add_paragraph(
            "Note that the upper and lower bound times are based on the 95% confidence interval."
        )

        sec.add_paragraph(
            "From this, it seems that the goal of sub-20 is feasible, but it may be a stretch. "
            "Therefore, we will set sub-21 as the ownership goal and sub-20 as the reach goal. "
        )

        sec = body.add_section()
        sec.add_title("Race Plan", level=2)
        sec.add_paragraph(
            "I am going to start aggressively and run 4 minutes for the first kilometer "
            "(on pace for a 20-minute 5K). If at 1K my heart rate is above 92.5% HRR, power "
            "is above 325W, or I'm not feeling like I'm able to sustain it, "
            "I will back off to 4:12 per KM for the next KM. At 2K, I'll start trying to sustain 320W. "
            "At 4K, if I have more in the tank, I will up the effort to 332W. "
            "At 4.6K, if I have more in the tank, I will kick all out."
        )
