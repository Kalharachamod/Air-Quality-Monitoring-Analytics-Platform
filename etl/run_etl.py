"""
Near real-time ETL: pull latest air quality data from Open-Meteo Air Quality (no API key)
and load into PostgreSQL star schema. Single-file for simplicity.
"""
import os
import requests
import psycopg2
from datetime import datetime, timezone
from dateutil import parser, tz

# Config
API = "https://air-quality-api.open-meteo.com/v1/air-quality"
CITY_CONFIG = [
    # South Asia
    {"city": "Colombo", "latitude": 6.9271, "longitude": 79.8612, "country": "LK"},
    {"city": "Delhi", "latitude": 28.6139, "longitude": 77.2090, "country": "IN"},
    {"city": "Mumbai", "latitude": 19.0760, "longitude": 72.8777, "country": "IN"},
    {"city": "Dhaka", "latitude": 23.8103, "longitude": 90.4125, "country": "BD"},

    # East Asia
    {"city": "Beijing", "latitude": 39.9042, "longitude": 116.4074, "country": "CN"},
    {"city": "Shanghai", "latitude": 31.2304, "longitude": 121.4737, "country": "CN"},
    {"city": "Tokyo", "latitude": 35.6762, "longitude": 139.6503, "country": "JP"},

    # Europe
    {"city": "London", "latitude": 51.5074, "longitude": -0.1278, "country": "GB"},
    {"city": "Paris", "latitude": 48.8566, "longitude": 2.3522, "country": "FR"},
    {"city": "Berlin", "latitude": 52.5200, "longitude": 13.4050, "country": "DE"},

    # North America
    {"city": "New York", "latitude": 40.7128, "longitude": -74.0060, "country": "US"},
    {"city": "Los Angeles", "latitude": 34.0522, "longitude": -118.2437, "country": "US"},

    # Middle East
    {"city": "Dubai", "latitude": 25.2048, "longitude": 55.2708, "country": "AE"},
]
# Open-Meteo hourly pollutants -> (our code, unit)
POLLUTANT_FIELDS = {
    "pm2_5": ("pm25", "µg/m³"),
    "pm10": ("pm10", "µg/m³"),
    "carbon_monoxide": ("co", "µg/m³"),
    "nitrogen_dioxide": ("no2", "µg/m³"),
    "sulphur_dioxide": ("so2", "µg/m³"),
    "ozone": ("o3", "µg/m³"),
    "european_aqi": ("aqi", None),  # unitless AQI
}
DB_URL = os.getenv("PG_URL", "postgresql://postgres:postgres@localhost:5432/air_quality")


def to_utc(ts_str: str):
    dt = parser.isoparse(ts_str)
    return dt.astimezone(tz.UTC)


def get_conn():
    return psycopg2.connect(DB_URL)


def upsert(cursor, table, lookup_cols, data_cols, row):
    cols = lookup_cols + data_cols
    placeholders = ", ".join(["%s"] * len(cols))
    updates = ", ".join([f"{c}=EXCLUDED.{c}" for c in data_cols])
    cursor.execute(
        f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders}) "
        f"ON CONFLICT ({', '.join(lookup_cols)}) DO UPDATE SET {updates}",
        row,
    )


def get_or_create_dim_time(cur, ts_utc):
    cur.execute("SELECT time_id FROM dim_time WHERE ts_utc=%s", (ts_utc,))
    r = cur.fetchone()
    if r:
        return r[0]
    dt_date = ts_utc.date()
    cur.execute(
        """
        INSERT INTO dim_time (ts_utc, date, hour, day, month, year, dow)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING time_id
        """,
        (
            ts_utc,
            dt_date,
            ts_utc.hour,
            ts_utc.day,
            ts_utc.month,
            ts_utc.year,
            ts_utc.weekday(),  # Monday=0
        ),
    )
    return cur.fetchone()[0]


def get_or_create_dim_location(cur, city, location, lat, lon, country):
    cur.execute("SELECT location_id FROM dim_location WHERE city=%s AND location=%s", (city, location))
    r = cur.fetchone()
    if r:
        return r[0]
    cur.execute(
        """
        INSERT INTO dim_location (city, location, latitude, longitude, country)
        VALUES (%s, %s, %s, %s, %s) RETURNING location_id
        """,
        (city, location, lat, lon, country),
    )
    return cur.fetchone()[0]


def get_pollutant_id(cur, code):
    cur.execute("SELECT pollutant_id FROM dim_pollutant WHERE code=%s", (code,))
    r = cur.fetchone()
    if r:
        return r[0]
    cur.execute("INSERT INTO dim_pollutant (code, unit) VALUES (%s, %s) RETURNING pollutant_id", (code, "µg/m³"))
    return cur.fetchone()[0]


def fetch_city(cfg):
    params = {
        "latitude": cfg["latitude"],
        "longitude": cfg["longitude"],
        "hourly": ",".join(POLLUTANT_FIELDS.keys()),
        "timezone": "UTC",
        "forecast_days": 1,
        "past_days": 1,
    }
    resp = requests.get(API, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def process_city(cur, cfg):
    data = fetch_city(cfg)
    hourly = data.get("hourly", {})
    times = hourly.get("time") or []
    if not times:
        print(f"No data for {cfg['city']}")
        return 0

    loc_id = get_or_create_dim_location(
        cur,
        city=cfg["city"],
        location=f"{cfg['city']} (Open-Meteo)",
        lat=cfg["latitude"],
        lon=cfg["longitude"],
        country=cfg.get("country"),
    )

    inserted = 0
    for idx, ts_str in enumerate(times):
        ts_utc = to_utc(ts_str)
        time_id = get_or_create_dim_time(cur, ts_utc)
        for field, (code, unit) in POLLUTANT_FIELDS.items():
            values = hourly.get(field)
            if not values or idx >= len(values):
                continue
            raw_val = values[idx]
            if raw_val is None:
                continue
            val = float(raw_val)
            pollutant_id = get_pollutant_id(cur, code)
            aqi_val = val if code == "aqi" else None
            value_val = None if code == "aqi" else val
            upsert(
                cur,
                "fact_air_quality",
                ["location_id", "time_id", "pollutant_id"],
                ["value", "aqi", "source"],
                (loc_id, time_id, pollutant_id, value_val, aqi_val, "open-meteo"),
            )
            inserted += 1
    return inserted


def main():
    print(f"[{datetime.now(timezone.utc)}] ETL started")
    with get_conn() as conn:
        with conn.cursor() as cur:
            for cfg in CITY_CONFIG:
                try:
                    count = process_city(cur, cfg)
                    print(f"Loaded city: {cfg['city']}, records: {count}")
                except Exception as ex:
                    print(f"Error processing city {cfg['city']}: {ex}")
            conn.commit()
    print(f"[{datetime.now(timezone.utc)}] ETL finished")


if __name__ == "__main__":
    main()

