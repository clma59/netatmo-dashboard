import requests
import psycopg2
from datetime import datetime

# ======================================
# NETATMO
# ======================================

CLIENT_ID = "6a1083ceb8160ecfb10279b8"
CLIENT_SECRET = "p44ViX4EHXLUxu0HMIYoKvXioOlr7gxZAVt2Ak"
REFRESH_TOKEN = "694c868be1aee6d1700a3655|99f3541b626d040fecb94a2239fb3893"

# ======================================
# SUPABASE
# ======================================

DATABASE_URL = "postgresql://postgres.dqzlpzlylcpinfldzjja:netatmo2026@aws-1-eu-central-1.pooler.supabase.com:6543/postgres"

# ======================================
# TOKEN
# ======================================

token_url = "https://api.netatmo.com/oauth2/token"

payload = {
    "grant_type": "refresh_token",
    "refresh_token": REFRESH_TOKEN,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET
}

response = requests.post(token_url, data=payload)

tokens = response.json()

access_token = tokens["access_token"]

print("Token OK")

# ======================================
# RÉCUP DONNÉES
# ======================================

headers = {
    "Authorization": f"Bearer {access_token}"
}

data_response = requests.get(
    "https://api.netatmo.com/api/getstationsdata",
    headers=headers
)

data = data_response.json()

device = data["body"]["devices"][0]
module = device["modules"][0]

temperature = module["dashboard_data"]["Temperature"]
humidity = module["dashboard_data"]["Humidity"]

print(f"Température : {temperature} °C")
print(f"Humidité : {humidity} %")

# ======================================
# INSERT POSTGRESQL
# ======================================

conn = psycopg2.connect(DATABASE_URL)

cursor = conn.cursor()

cursor.execute(
    """
    INSERT INTO temperatures
    (timestamp, temperature, humidity)
    VALUES (%s, %s, %s)
    """,
    (
        datetime.now(),
        temperature,
        humidity
    )
)

conn.commit()

cursor.close()
conn.close()

print("Données enregistrées dans Supabase")