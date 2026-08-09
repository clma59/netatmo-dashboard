import os
import requests
import psycopg2
from datetime import datetime, timedelta

# ======================================
# VARIABLES ENVIRONNEMENT
# (lues depuis les secrets, comme collect.py — aucun identifiant en clair)
# ======================================

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Références matérielles de la station (non secrètes : inutilisables sans les clés)
DEVICE_ID = "70:ee:50:c3:c8:2e"
MODULE_ID = "02:00:00:c5:4d:92"

# ======================================
# TOKEN NETATMO
# ======================================

token_url = "https://api.netatmo.com/oauth2/token"

token_payload = {
    "grant_type": "refresh_token",
    "refresh_token": REFRESH_TOKEN,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET
}

token_response = requests.post(token_url, data=token_payload)

token_data = token_response.json()

access_token = token_data["access_token"]

print("Token OK")

# ======================================
# CONNEXION SUPABASE
# ======================================

conn = psycopg2.connect(DATABASE_URL)

cursor = conn.cursor()

print("Connexion Supabase OK")

# ======================================
# BOUCLE PAR PÉRIODE
# ======================================

# Début = début du trou de données. Fin = maintenant.
start_date = datetime(2025, 7, 22)
end_date = datetime.now()

current_start = start_date

total_count = 0

while current_start < end_date:

    current_end = current_start + timedelta(days=30)

    if current_end > end_date:
        current_end = end_date

    print(f"\nImport : {current_start.date()} -> {current_end.date()}")

    measure_url = "https://api.netatmo.com/api/getmeasure"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params = {
        "device_id": DEVICE_ID,
        "module_id": MODULE_ID,
        "scale": "1hour",
        "type": "Temperature,Humidity",
        "date_begin": int(current_start.timestamp()),
        "date_end": int(current_end.timestamp())
    }

    response = requests.get(
        measure_url,
        headers=headers,
        params=params
    )

    data = response.json()

    if "body" not in data or len(data["body"]) == 0:
        print("Aucune donnée sur cette période")
        current_start = current_end
        continue

    count = 0

    # getmeasure renvoie une liste de blocs, chacun avec beg_time, step_time, value
    for body in data["body"]:

        timestamps = body["beg_time"]
        step = body.get("step_time", 3600)
        values = body["value"]

        for i, row in enumerate(values):

            timestamp = timestamps + (i * step)

            dt = datetime.fromtimestamp(timestamp)

            temperature = row[0]
            humidity = row[1]

            # On ignore les mesures incomplètes éventuelles
            if temperature is None or humidity is None:
                continue

            cursor.execute(
                """
                INSERT INTO temperatures (timestamp, temperature, humidity)
                VALUES (%s, %s, %s)
                """,
                (
                    dt,
                    temperature,
                    humidity
                )
            )

            count += 1

    conn.commit()

    print(f"{count} mesures importées")

    total_count += count

    current_start = current_end

cursor.close()
conn.close()

print(f"\nTOTAL : {total_count} mesures importées")
