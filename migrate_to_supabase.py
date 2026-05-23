import sqlite3
import pandas as pd
from sqlalchemy import create_engine

DATABASE_URL = "postgresql://postgres.dqzlpzlylcpinfldzjja:netatmo2026@aws-1-eu-central-1.pooler.supabase.com:6543/postgres"
print(DATABASE_URL)

engine = create_engine(DATABASE_URL)

print("Connexion Supabase OK")

sqlite_conn = sqlite3.connect("weather.db")

df = pd.read_sql_query(
    "SELECT * FROM temperatures",
    sqlite_conn
)

sqlite_conn.close()

print(f"{len(df)} mesures lues depuis SQLite")

df.to_sql(
    "temperatures",
    engine,
    if_exists="append",
    index=False
)

print("Migration terminée")