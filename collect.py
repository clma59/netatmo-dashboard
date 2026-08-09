import os
import requests
import psycopg2
from datetime import datetime

# ======================================
# VARIABLES ENVIRONNEMENT
# ======================================

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# ======================================
# TOKEN NETATMO
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
print("REPONSE API :", data)

device = data["body"]["devices"][0]
module = device["modules"][0]

temperature = module["dashboard_data"]["Temperature"]
humidity = module["dashboard_data"]["Humidity"]

print(f"Température : {temperature} °C")
print(f"Humidité : {humidity} %")

# ======================================
# INSERT SUPABASE
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
