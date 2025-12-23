-- Star schema for air quality warehouse

CREATE TABLE IF NOT EXISTS dim_location (
  location_id SERIAL PRIMARY KEY,
  city        TEXT NOT NULL,
  location    TEXT NOT NULL,
  latitude    NUMERIC(9,6),
  longitude   NUMERIC(9,6),
  country     TEXT
);

CREATE TABLE IF NOT EXISTS dim_time (
  time_id     SERIAL PRIMARY KEY,
  ts_utc      TIMESTAMPTZ NOT NULL UNIQUE,
  date        DATE NOT NULL,
  hour        INT,
  day         INT,
  month       INT,
  year        INT,
  dow         INT
);

CREATE TABLE IF NOT EXISTS dim_pollutant (
  pollutant_id SERIAL PRIMARY KEY,
  code         TEXT UNIQUE NOT NULL,   -- pm25, pm10, no2, so2, o3, co, aqi
  name         TEXT,
  unit         TEXT,                   -- unified unit (e.g., µg/m³)
  category_cutoffs JSONB
);

CREATE TABLE IF NOT EXISTS fact_air_quality (
  fact_id      BIGSERIAL PRIMARY KEY,
  location_id  INT REFERENCES dim_location(location_id),
  time_id      INT REFERENCES dim_time(time_id),
  pollutant_id INT REFERENCES dim_pollutant(pollutant_id),
  value        NUMERIC(10,2),          -- pollutant concentration
  aqi          NUMERIC(6,2),           -- AQI if provided/derived
  source       TEXT,
  UNIQUE(location_id, time_id, pollutant_id)
);

