from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from api.config import DATABASE_URL

# pool_pre_ping checks each pooled connection before using it, so connections
# that Supabase closed while the server sat idle get replaced instead of erroring.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
