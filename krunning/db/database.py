from contextlib import ExitStack, contextmanager
import datetime
from typing import ContextManager, Any, Union, Dict

import psycopg2
from abc import ABC, abstractmethod


class ConnectionPool(ABC):
    @abstractmethod
    def get_connection(self) -> ContextManager[Any]:
        pass


class NoConnectionAvailable(IOError):
    pass


class PGConnectionPool(ConnectionPool):
    def __init__(self, connection_dict: Dict[str, Any], size: int):
        self.__pool = []
        for _ in range(size):
            self.__pool.append(psycopg2.connect(**connection_dict))

    @contextmanager
    def get_connection(self) -> ContextManager[Any]:
        if len(self.__pool) == 0:
            raise NoConnectionAvailable
        conn = self.__pool.pop()
        try:
            yield conn
        finally:
            self.__pool.append(conn)


class ActivityBuilder(ABC):
    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def commit(self):
        pass

    @abstractmethod
    def rollback(self):
        pass


class Field(object):
    def __init__(self, name: str, type):
        self.name = name
        self.type = type

    def __get__(self, instance, owner):
        cur = instance.cursor
        cur.execute(
            f"SELECT {self.name} FROM {instance.table} WHERE id = %s LIMIT 1;",
            [instance.id],
        )
        (value,) = cur.fetchone()
        return value

    def __set__(self, instance, value):
        if not isinstance(value, self.type):
            raise TypeError(
                "Expected %s for %s, received %r" % (self.type, self.name, value)
            )
        cur = instance.cursor
        cur.execute(
            f"UPDATE {instance.table} SET {self.name} = %s WHERE id = %s;",
            [value, instance.id],
        )


class Sample:
    def __init__(self, cursor, id):
        self.__cursor = cursor
        self.__id = id

    def add_value(
        self, field_name: str, field_units: str, field_value: Union[float, int]
    ):
        self.__cursor.execute(
            """
            INSERT INTO fields (field_name, field_units)
            VALUES (%s, %s)
            ON CONFLICT (field_name, field_units) DO NOTHING;
        """,
            [field_name, field_units],
        )
        self.__cursor.execute(
            """
            SELECT id FROM fields WHERE field_name = %s AND field_units = %s LIMIT 1;
        """,
            [field_name, field_units],
        )
        (field_id,) = self.__cursor.fetchone()
        self.__cursor.execute(
            """
            INSERT INTO sample_values (sample_id, field_id, int_value, float_value) 
            VALUES (%(sample_id)s, %(field_id)s, %(int_value)s, %(float_value)s)
            ON CONFLICT (sample_id, field_id) DO UPDATE SET int_value = %(int_value)s, float_value = %(float_value)s;
            """,
            dict(
                sample_id=self.__id,
                field_id=field_id,
                int_value=field_value if isinstance(field_value, int) else None,
                float_value=field_value if isinstance(field_value, float) else None,
            ),
        )


class ActivityAlreadyExistsError(ValueError):
    pass


class DatabaseActivityBuilder(ActivityBuilder):
    table = "activities"

    def __init__(
        self, connection_pool: ConnectionPool, fitfile_name: str, replace: bool
    ):
        self.__exit_stack = ExitStack()
        self.__connection_pool = connection_pool
        self.__connection = None
        self.__replace = replace
        self.cursor = None
        self.id = None
        self.__fitfile_name = fitfile_name

    f_fitfile_name = Field("fitfile_name", str)
    f_created = Field("created", datetime.datetime)

    f_user_gender = Field("user_gender", str)
    f_user_height_meters = Field("user_height_meters", float)
    f_user_resting_heart_rate = Field("user_resting_heart_rate", int)
    f_user_max_heart_rate = Field("user_max_heart_rate", int)
    f_user_sleep_time = Field("user_sleep_time", datetime.time)
    f_user_wake_time = Field("user_wake_time", datetime.time)
    f_user_running_step_length_meters = Field("user_running_step_length_meters", float)
    f_user_walking_step_length_meters = Field("user_walking_step_length_meters", float)
    f_user_weight_kg = Field("user_weight_kg", float)

    f_device_manufacturer = Field("device_manufacturer", str)
    f_device_product_number = Field("device_product_number", str)
    f_device_serial_number = Field("device_serial_number", str)

    f_sport = Field("sport", str)
    f_sub_sport = Field("sub_sport", str)

    def add_timer_event(
        self,
        message_id: int,
        event_type: str,
        timer_trigger: str,
        timestamp: datetime.datetime,
    ):
        self.cursor.execute(
            """
            INSERT INTO timer_events (activity_id, message_id, event_type, timer_trigger, created) 
            VALUES (%(activity_id)s, %(message_id)s, %(event_type)s, %(timer_trigger)s, %(created)s)
            ON CONFLICT (activity_id, message_id)
            DO UPDATE SET event_type = %(event_type)s, timer_trigger = %(timer_trigger)s, created = %(created)s
        """,
            dict(
                activity_id=self.id,
                message_id=message_id,
                event_type=event_type,
                timer_trigger=timer_trigger,
                created=timestamp,
            ),
        )

    def add_sample(self, message_id: int, timestamp: datetime.datetime) -> Sample:
        self.cursor.execute(
            """
            INSERT INTO samples (activity_id, message_id, sampled_at) 
            VALUES (%(activity_id)s, %(message_id)s, %(sampled_at)s)
            ON CONFLICT (activity_id, message_id) DO UPDATE SET sampled_at = %(sampled_at)s
            RETURNING id;
        """,
            dict(activity_id=self.id, message_id=message_id, sampled_at=timestamp),
        )
        (sample_id,) = self.cursor.fetchone()
        return Sample(self.cursor, sample_id)

    def start(self):
        self.__connection = self.__exit_stack.enter_context(
            self.__connection_pool.get_connection()
        )
        self.cursor = self.__connection.cursor()

        self.cursor.execute(
            """
            SELECT COUNT(*) > 0 as exists FROM activities
            WHERE fitfile_name = %s;
        """,
            [self.__fitfile_name],
        )
        (exists,) = self.cursor.fetchone()
        if exists and not self.__replace:
            raise ActivityAlreadyExistsError

        self.cursor.execute(
            """
            INSERT INTO activities (fitfile_name)
            VALUES (%s)
            ON CONFLICT (fitfile_name) DO NOTHING;
            """,
            [self.__fitfile_name],
        )
        self.cursor.execute(
            """SELECT id FROM activities WHERE fitfile_name = %s LIMIT 1;""",
            [self.__fitfile_name],
        )
        (self.id,) = self.cursor.fetchone()

    def commit(self):
        self.__connection.commit()
        self.__exit_stack.close()

    def rollback(self):
        self.__connection.rollback()
        self.__connection.close()


class Database:
    EXPECTED_MIGRATION = "0001"

    def __init__(self, psycopg2_connection_pool: ConnectionPool):
        self.__connection_pool = psycopg2_connection_pool
        self.__check_migration()

    def __check_migration(self):
        with self.__connection_pool.get_connection() as conn:
            with conn:
                cur = conn.cursor()
                cur.execute("SELECT version FROM migration LIMIT 1;")
                (version,) = cur.fetchone()
                if version != self.EXPECTED_MIGRATION:
                    raise IOError(
                        "Expected database to be at migration %s, was %s"
                        % (self.EXPECTED_MIGRATION, version)
                    )

    def activity_builder(
        self, fitfile_name: str, replace: bool
    ) -> DatabaseActivityBuilder:
        return DatabaseActivityBuilder(self.__connection_pool, fitfile_name, replace)
