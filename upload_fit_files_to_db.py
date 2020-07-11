import fitparse
import os
import logging
import argparse
import multiprocessing
from typing import Dict, Any

from krunning.db import conn_dict_from_env
from krunning.db.database import Database, PGConnectionPool, ActivityAlreadyExistsError


def process_fitfile(db: Database, fitfile_path: str, replace: bool):
    fitfile_name = os.path.basename(fitfile_path)
    try:
        with db.activity_builder(fitfile_name, replace) as activity_builder:
            logging.info("Processing %s", fitfile_name)
            with fitparse.FitFile(fitfile_path) as fitfile:
                N = len(fitfile.messages)
                for message_id, message in enumerate(fitfile.messages):
                    if (message_id + 1) % 1000 == 0:
                        logging.info(
                            "Processing %s: %d / %d (%.2f%%)",
                            fitfile_name,
                            message_id + 1,
                            N,
                            (message_id / N * 100),
                        )
                    d = {record_data.name: record_data.value for record_data in message}
                    if message.name == "file_id":
                        activity_builder.f_device_manufacturer = d["manufacturer"]
                        activity_builder.f_device_product_number = str(
                            d["garmin_product"]
                        )
                        activity_builder.f_device_serial_number = str(
                            d["serial_number"]
                        )
                        activity_builder.f_created = d["time_created"]
                    elif message.name.startswith("unknown_"):
                        continue
                    elif message.name in {
                        "file_creator",
                        "device_info",
                        "device_settings",
                        "training_file",
                        "developer_data_id",
                        "field_description",
                        "gps_metadata",
                        "activity",
                    }:
                        continue
                    elif message.name == "event":
                        if d["event"] == "timer":
                            activity_builder.add_timer_event(
                                message_id=message_id,
                                event_type=d["event_type"],
                                timer_trigger=d["timer_trigger"],
                                timestamp=d["timestamp"],
                            )
                        elif d["event"] in {"course_point", "off_course"}:
                            continue
                        elif isinstance(d["event"], int):
                            continue
                        else:
                            logging.warning(
                                "Unknown event %s with properties %s", d["event"], d
                            )
                    elif message.name == "record":
                        sample = activity_builder.add_sample(message_id, d["timestamp"])
                        for record_data in message:
                            if (
                                (not record_data.name.startswith("unknown_"))
                                and (record_data.value is not None)
                                and (record_data.name not in ("timestamp"))
                            ):
                                sample.add_value(
                                    record_data.name,
                                    record_data.units,
                                    record_data.value,
                                )
                    elif message.name == "user_profile":
                        activity_builder.f_user_gender = d["gender"]
                        activity_builder.f_user_height_meters = d["height"]
                        activity_builder.f_user_resting_heart_rate = d[
                            "resting_heart_rate"
                        ]
                        activity_builder.f_user_sleep_time = d["sleep_time"]
                        activity_builder.f_user_running_step_length_meters = d[
                            "user_running_step_length"
                        ]
                        activity_builder.f_user_walking_step_length_meters = d[
                            "user_walking_step_length"
                        ]
                        activity_builder.f_user_wake_time = d["wake_time"]
                        activity_builder.f_user_weight_kg = d["weight"]
                    elif message.name == "sport":
                        activity_builder.f_sport = d["sport"]
                        activity_builder.f_sub_sport = d["sub_sport"]
                    elif message.name == "zones_target":
                        activity_builder.f_user_max_heart_rate = d["max_heart_rate"]
                    elif message.name in {"lap", "session"}:
                        continue
                    else:
                        logging.warning(
                            "Unknown message %s with properties %s", message.name, d
                        )
        logging.info("Finished processing %s", fitfile_name)
    except ActivityAlreadyExistsError:
        logging.info("Skipping %s: activity already exists", fitfile_name)


class PGConnectionPoolFactory:
    def __init__(self, conn_dict: Dict[str, Any], n_connections: int):
        self.conn_dict = conn_dict
        self.n_connection = n_connections

    def make_connection_pool(self) -> PGConnectionPool:
        return PGConnectionPool(self.conn_dict, self.n_connection)


_subprocess_factory: PGConnectionPoolFactory = None


def initialize_subprocess(factory: PGConnectionPoolFactory):
    global _subprocess_factory
    _subprocess_factory = factory


def do_process_file(args):
    filepath, replace = args
    conn_pool = _subprocess_factory.make_connection_pool()
    db = Database(conn_pool)
    process_fitfile(db, filepath, replace)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--nproc",
        default=multiprocessing.cpu_count(),
        type=int,
        help="Number of processes",
    )
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Replace activities in DB which we have fit files for.",
    )
    parser.add_argument(
        "--directory", default="data", help="Directory to search for fit files."
    )

    args = parser.parse_args()

    files = []
    for filename in sorted(os.listdir(args.directory)):
        if filename.endswith(".fit"):
            filepath = os.path.join(args.directory, filename)
            files.append(filepath)

    factory = PGConnectionPoolFactory(conn_dict_from_env(), 1)
    with multiprocessing.Pool(
        args.nproc, initializer=initialize_subprocess, initargs=(factory,)
    ) as pool:
        pool.map(
            do_process_file,
            [(filename, args.replace) for filename in files],
            chunksize=1,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
