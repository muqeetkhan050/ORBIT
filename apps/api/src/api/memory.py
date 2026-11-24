import atexit

from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
from api.config import DATABASE_URL


pool = ConnectionPool(
    
    conninfo=DATABASE_URL,
    max_size=5,
    kwargs={"autocommit": True, "prepare_threshold": 0},
    open=True,
    # Supabase closes connections that sit idle. Before handing out a connection,
    # test it and replace it if it's dead (same idea as pool_pre_ping in database.py).
    check=ConnectionPool.check_connection,
    # Also retire connections idle for 5 minutes, before Supabase drops them.
    max_idle=300,
)
# Close the pool cleanly when the program exits, so its background threads stop
# and the database connections are released (otherwise psycopg warns at exit).
atexit.register(pool.close)


checkpointer = PostgresSaver(pool)
checkpointer.setup()