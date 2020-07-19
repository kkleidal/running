import argparse
from typing import List
import numpy as np
import scipy
import scipy.stats
import matplotlib.pyplot as plt
import psycopg2
from collections import deque
from typing import NamedTuple, List, Union
import datetime
import matplotlib.pyplot as plt
import numpy as np
import scipy.interpolate
import logging

from krunning.db import conn_dict_from_env

from ..constants import KG_PER_LB
from ..data_provider import SpeedPowerFitFilesDataProvider
from ..db.utils import get_conn
from ..reports_gen import reports, ReportGenerator, ReportBuilder


class TimerEvent(NamedTuple):
    message_id: int
    created: datetime.datetime
    event_type: str


class PowerEvent(NamedTuple):
    message_id: int
    created: datetime.datetime
    power: int


@reports.register("power_curve")
class PowerCurveGenerator(ReportGenerator):
    def build_parser(self, parser: argparse.ArgumentParser):
        pass

    def generate_report(self, args, report_builder: ReportBuilder):
        with get_conn(1) as cur:
            # Get activities within 90 days
            cur.execute(
                "SELECT id FROM activities WHERE (NOW() - created) < '90 days'::interval;"
            )

            power_curve_buckets = {}
            for (activity_id,) in list(cur):
                logging.info("ACTIVITY %d", activity_id)
                # Get places the watch was started and stopped
                cur.execute(
                    """
                    SELECT message_id, created, event_type FROM timer_events
                    WHERE activity_id = %s;
                    """,
                    [activity_id],
                )
                timer_events = [TimerEvent(*row) for row in list(cur)]

                # Get samples with power
                cur.execute(
                    """
                    SELECT s.message_id, s.sampled_at, sv_power.int_value as power FROM samples s
                    INNER JOIN sample_values sv_power on s.id = sv_power.sample_id AND sv_power.field_id = (
                        SELECT id FROM fields
                        WHERE field_name = 'Power'
                    )
                    WHERE activity_id = %s;
                    """,
                    [activity_id],
                )
                power_events = [PowerEvent(*row) for row in list(cur)]
                events = sorted(timer_events + power_events)
                started = False

                powers = None
                times = None
                start_time = None

                # Extract spans of running between starting and pausing watch
                spans = []
                for i, event in enumerate(events):
                    if isinstance(event, PowerEvent):
                        if started:
                            powers.append(event.power)
                            if start_time is None:
                                start_time = event.created
                            times.append((event.created - start_time).total_seconds())
                    elif isinstance(event, TimerEvent):
                        if event.event_type == "start":
                            powers = []
                            times = []
                            start_time = None
                            started = True
                        elif event.event_type == "stop_all":
                            spans.append((np.array(times), np.array(powers)))
                            powers = None
                            times = None
                            start_time = None
                        else:
                            raise NotImplementedError(event)
                    else:
                        raise NotImplementedError(event)

                # For every span of contiguous running...
                for times, powers in spans:
                    # Interpolate the power samples, 1 every second:
                    if len(times) == 0:
                        continue
                    X = np.arange(0, np.floor(np.max(times) + 1))
                    interpolator = scipy.interpolate.interp1d(times, powers)
                    Y = interpolator(X)

                    # Cumulative sum the powers and find the average power sliding window
                    # for every possible duration:
                    Ysum = np.concatenate([[0], np.cumsum(Y)])
                    for duration in range(1, Ysum.shape[0]):
                        # The power curve is defined as the max average power for the duration
                        average_power_at_duration = np.max(
                            (Ysum[duration:] - Ysum[:-duration]) / duration
                        )
                        value = (average_power_at_duration, activity_id)
                        if (
                            duration not in power_curve_buckets
                            or power_curve_buckets[duration] < value
                        ):
                            power_curve_buckets[duration] = value

        # Plot
        durations = np.array(sorted(power_curve_buckets.keys()))
        powers = np.array([power_curve_buckets[duration][0] for duration in durations])

        body = report_builder.body()
        body.add_title("Power Curve")
        body.add_paragraph(
            "The power curve is the max average power for windows of the duration length. "
            "So for 20 minutes, we take every 20 minute (sliding) window in every run and find "
            "the window with the maximum (average) power."
        )
        body.add_paragraph("We use data from the past 90 days.")

        plt.title("Power Curve")
        plt.plot(durations / 60, powers)
        plt.ylabel("Power (W)")
        plt.xlabel("Duration (min)")
        body.add_figure(plt.gcf())
