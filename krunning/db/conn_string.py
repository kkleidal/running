import os
from typing import Dict, Any


def conn_dict_from_env(env=os.environ) -> Dict[str, Any]:
    return dict(
        host=env.get("PG_HOST", "127.0.0.1"),
        port=int(env.get("PG_PORT", 5432)),
        dbname=env.get("PG_DB", "postgres"),
        user=env.get("PG_USER", "postgres"),
        password=env["PG_PASSWORD"],
    )
