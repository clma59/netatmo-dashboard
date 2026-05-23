import requests
import sqlite3
from datetime import datetime, timedelta

# ======================================
# IDENTIFIANTS
# ======================================

CLIENT_ID = "6a1083ceb8160ecfb10279b8"
CLIENT_SECRET = "p44ViX4EHXLUxu0HMIYoKvXioOlr7gxZAVt2Ak"
REFRESH_TOKEN = "694c868be1aee6d1700a3655|99f3541b626d040fecb94a2239fb3893"

DEVICE_ID = "70:ee:50:c3:c8:2e"
MODULE_ID = "02:00:00:c5:4d:92"

# ======================================
# NOUVEAU TOKEN
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
# SQLITE
# ======================================

conn = sqlite3.connect("weather.db")

cursor = conn.cursor()

# ======================================
# BOUCLE PAR PÉRIODE
# ======================================

start_date = datetime(2025, 12, 25)
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
        print("Aucune donnée")
        current_start = current_end
        continue

    body = data["body"][0]

    timestamps = body["beg_time"]
    step = body["step_time"]
    values = body["value"]

    count = 0

    for i, row in enumerate(values):

        timestamp = timestamps + (i * step)

        dt = datetime.fromtimestamp(timestamp).isoformat()

        temperature = row[0]
        humidity = row[1]

        cursor.execute("""
        INSERT INTO temperatures (timestamp, temperature, humidity)
        VALUES (?, ?, ?)
        """, (
            dt,
            temperature,
            humidity
        ))

        count += 1

    conn.commit()

    print(f"{count} mesures importées")

    total_count += count

    current_start = current_end

conn.close()

print(f"\nTOTAL : {total_count} mesures importées")