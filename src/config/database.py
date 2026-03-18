from src.config.settings import Settings
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sttg = Settings()

db_uri = f"postgresql://{sttg.database_user}:{sttg.database_pass}@{sttg.database_host}:{sttg.database_port}/{sttg.database_name}"

__engine__ = create_engine(db_uri)

def get_session():
    with Session(__engine__) as session:
        yield session
