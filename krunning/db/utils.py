from contextlib import contextmanager
from typing import Union

import psycopg2

from krunning.db import conn_dict_from_env


@contextmanager
def get_conn(expected_schema: Union[int, str]):
    conn = psycopg2.connect(**conn_dict_from_env())
    with conn:
        cur = conn.cursor()

        # Make sure the DB schema is at the expected migration
        cur.execute("SELECT version FROM migration LIMIT 1;")
        (version,) = cur.fetchone()
        if isinstance(expected_schema, int):
            expected_schema = "%04d" % expected_schema
        assert version == expected_schema

        yield cur
