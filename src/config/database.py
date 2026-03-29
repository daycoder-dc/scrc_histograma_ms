from src.config.settings import Settings

sttg = Settings()

db_uri = f"postgresql://{sttg.database_user}:{sttg.database_pass}@{sttg.database_host}:{sttg.database_port}/{sttg.database_name}"
