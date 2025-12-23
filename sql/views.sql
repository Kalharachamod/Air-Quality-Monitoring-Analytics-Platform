-- OLAP materialized views for fast analytics

-- Daily average AQI by city
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_aqi AS
SELECT dl.city, dt.date, AVG(f.aqi) AS avg_aqi
FROM fact_air_quality f
JOIN dim_location dl ON f.location_id = dl.location_id
JOIN dim_time dt ON f.time_id = dt.time_id
GROUP BY dl.city, dt.date;

CREATE INDEX IF NOT EXISTS idx_mv_daily_aqi_city_date ON mv_daily_aqi(city, date);

-- Monthly pollution trends per pollutant
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_monthly_pollution AS
SELECT dl.city, dt.year, dt.month, dp.code AS pollutant, AVG(f.value) AS avg_value
FROM fact_air_quality f
JOIN dim_location dl ON f.location_id = dl.location_id
JOIN dim_time dt ON f.time_id = dt.time_id
JOIN dim_pollutant dp ON f.pollutant_id = dp.pollutant_id
GROUP BY dl.city, dt.year, dt.month, dp.code;

CREATE INDEX IF NOT EXISTS idx_mv_monthly_pollution_city_date ON mv_monthly_pollution(city, year, month);

-- City-wise comparison for latest day across pollutants
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_city_comparison AS
WITH latest_day AS (
  SELECT MAX(date) AS max_date FROM dim_time
)
SELECT dl.city, dp.code AS pollutant, AVG(f.value) AS avg_value
FROM fact_air_quality f
JOIN dim_location dl ON f.location_id = dl.location_id
JOIN dim_time dt ON f.time_id = dt.time_id
JOIN dim_pollutant dp ON f.pollutant_id = dp.pollutant_id
JOIN latest_day ld ON dt.date = ld.max_date
GROUP BY dl.city, dp.code;

CREATE INDEX IF NOT EXISTS idx_mv_city_comparison_city_pollutant ON mv_city_comparison(city, pollutant);

-- Helper: refresh all materialized views
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_aqi;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_monthly_pollution;
-- REFRESH MATERIALIZED VIEW CONCURRENTLY mv_city_comparison;

