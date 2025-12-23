# 🌍 Air Quality Monitoring & Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-blue.svg)](https://www.postgresql.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)

A comprehensive, end-to-end **data engineering project** that monitors air quality across 13+ major cities worldwide in near real-time. Built with industry-standard practices including star schema data warehousing, OLAP materialized views, and interactive web dashboards.

---

## ✅ Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.10 or higher** - [Download here](https://www.python.org/downloads/)
- **PostgreSQL 12 or higher** - [Download here](https://www.postgresql.org/download/)
- **Git** - [Download here](https://git-scm.com/downloads)
- **VS Code** (recommended) - [Download here](https://code.visualstudio.com/)
- **Power BI Desktop** (optional, for BI dashboards) - [Download here](https://powerbi.microsoft.com/desktop/)

---

## 🚀 Quick Start Guide

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/air-quality-monitoring.git
cd air-quality-monitoring
```

### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows (PowerShell):
.\.venv\Scripts\activate
# On Windows (CMD):
.venv\Scripts\activate.bat
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure PostgreSQL Database

1. **Create a new database:**
   ```sql
   CREATE DATABASE air_quality;
   ```

2. **Set environment variable for database connection:**
   
   **Windows (PowerShell):**
   ```powershell
   $env:PG_URL="postgresql://username:password@localhost:5432/air_quality"
   ```
   
   **Windows (CMD):**
   ```cmd
   setx PG_URL "postgresql://username:password@localhost:5432/air_quality"
   ```
   > **Note:** After using `setx`, close and reopen your terminal.
   
   **macOS/Linux:**
   ```bash
   export PG_URL="postgresql://username:password@localhost:5432/air_quality"
   ```

   **Replace:**
   - `username` with your PostgreSQL username (usually `postgres`)
   - `password` with your PostgreSQL password
   - If your password contains special characters like `@`, URL-encode them (e.g., `@` becomes `%40`)

### Step 4: Create Database Schema

**Option A: Using psql (Command Line)**

```bash
# Connect to PostgreSQL
psql -U username -d air_quality

# Run schema creation
\i sql/schema.sql

# Create OLAP views
\i sql/views.sql

# Exit psql
\q
```

**Option B: Using pgAdmin (GUI)**

1. Open pgAdmin
2. Connect to your PostgreSQL server
3. Right-click on `air_quality` database → **Query Tool**
4. Open `sql/schema.sql` and execute it
5. Open `sql/views.sql` and execute it

---

## 🎯 How to Run the Project

### 1. Run the ETL Pipeline

The ETL pipeline extracts air quality data from the API and loads it into your database.

```bash
# Make sure virtual environment is activated
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Run ETL
python etl/run_etl.py
```

**Expected Output:**
```
[2025-12-23 15:30:10] ETL started
Loaded city: Colombo, records: 336
Loaded city: Delhi, records: 336
...
[2025-12-23 15:30:15] ETL finished
```

**Schedule ETL (Optional - for near real-time updates):**

**Windows Task Scheduler:**
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Every 15 minutes
4. Action: Start a program
   - Program: `C:\path\to\your\project\.venv\Scripts\python.exe`
   - Arguments: `etl/run_etl.py`
   - Start in: `C:\path\to\your\project`

### 2. Refresh Materialized Views

After running ETL, refresh the OLAP views to update aggregated data:

**Using psql:**
```sql
REFRESH MATERIALIZED VIEW mv_daily_aqi;
REFRESH MATERIALIZED VIEW mv_monthly_pollution;
REFRESH MATERIALIZED VIEW mv_city_comparison;
```

**Using pgAdmin:**
1. Open Query Tool
2. Paste the above SQL commands
3. Execute

**Note:** If you get an error about `CONCURRENTLY`, first create unique indexes:
```sql
CREATE UNIQUE INDEX IF NOT EXISTS uq_mv_daily_aqi ON mv_daily_aqi(city, date);
CREATE UNIQUE INDEX IF NOT EXISTS uq_mv_monthly_pollution ON mv_monthly_pollution(city, year, month, pollutant);
CREATE UNIQUE INDEX IF NOT EXISTS uq_mv_city_comparison ON mv_city_comparison(city, pollutant);
```

Then use `REFRESH MATERIALIZED VIEW CONCURRENTLY ...` for non-blocking refreshes.

### 3. Start the Web Application

```bash
# Make sure virtual environment is activated
.\.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Make sure PG_URL is set
$env:PG_URL="postgresql://username:password@localhost:5432/air_quality"  # Windows PowerShell
# export PG_URL="postgresql://username:password@localhost:5432/air_quality"  # macOS/Linux

# Run Flask app
python webapp/app.py
```

**Expected Output:**
```
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```

**Open in Browser:**
Navigate to: `http://localhost:5000`

You should see the Air Quality Analytics Dashboard with:
- City selection dropdown
- Date range filters
- Daily AQI chart and table
- Monthly pollutant trends chart and table

### 4. Connect Power BI (Optional)

1. Open **Power BI Desktop**
2. Click **Get Data** → **More...**
3. Select **PostgreSQL database**
4. Enter connection details:
   - Server: `localhost`
   - Database: `air_quality`
   - Username/Password: Your PostgreSQL credentials
5. Select **DirectQuery** or **Import** mode
6. Choose only the materialized views:
   - `mv_daily_aqi`
   - `mv_monthly_pollution`
   - `mv_city_comparison`
7. Build your dashboards!

---

## 📁 Project Structure

```
air-quality-monitoring/
│
├── etl/
│   └── run_etl.py              # ETL pipeline: extracts, transforms, loads data
│
├── webapp/
│   └── app.py                  # Flask web application (analytics dashboard)
│
├── sql/
│   ├── schema.sql              # Database schema (star schema: fact + dimensions)
│   └── views.sql               # OLAP materialized views (pre-aggregated data)
│
├── docs/
│   └── LINKEDIN_POST.md        # LinkedIn post template
│
├── requirements.txt            # Python dependencies
├── README.md                    # This file
└── .gitignore                  # Git ignore rules
```

---

## 🛠️ Tech Stack

- **Python 3.10+** - ETL pipeline and web application
- **PostgreSQL** - Data warehouse with star schema
- **Flask** - Web framework
- **Bootstrap 5** - UI framework
- **Chart.js** - Data visualization
- **Open-Meteo API** - Air quality data source (free, no API key)

---

## 🏗️ Architecture

```
Open-Meteo API
     ↓
ETL Pipeline (Python)
     ↓
PostgreSQL Data Warehouse (Star Schema)
     ↓
OLAP Materialized Views
     ↓
    ├──→ Flask Web App
    └──→ Power BI Dashboards
```

**Data Flow:**
1. **Extract**: Fetch air quality data from Open-Meteo API
2. **Transform**: Clean, normalize timestamps (UTC), standardize units
3. **Load**: Insert into PostgreSQL star schema
4. **OLAP**: Pre-aggregate data in materialized views
5. **Visualize**: Web app and Power BI read from OLAP views

---

## 🔧 Troubleshooting

### Issue: "Module not found" error
**Solution:** Make sure virtual environment is activated and dependencies are installed:
```bash
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Issue: "Connection refused" or "password authentication failed"
**Solution:** 
- Check PostgreSQL is running
- Verify `PG_URL` environment variable is set correctly
- Ensure username/password are correct
- If password contains `@`, URL-encode it as `%40`

### Issue: "Table does not exist"
**Solution:** Make sure you've run `sql/schema.sql` and `sql/views.sql` in order

### Issue: Charts not showing in web app
**Solution:**
- Make sure you've run ETL and refreshed materialized views
- Check browser console for JavaScript errors
- Verify data exists for selected city and date range

### Issue: ETL returns "410 Gone" or API errors
**Solution:** The API endpoint may have changed. Check `etl/run_etl.py` and update the API URL if needed.

### Issue: Materialized view refresh fails
**Solution:** 
- For `CONCURRENTLY`, create unique indexes first (see Step 2 above)
- Or use regular refresh: `REFRESH MATERIALIZED VIEW mv_daily_aqi;` (without CONCURRENTLY)

---

## 📊 Cities Monitored

- **South Asia**: Colombo, Delhi, Mumbai, Dhaka
- **East Asia**: Beijing, Shanghai, Tokyo
- **Europe**: London, Paris, Berlin
- **North America**: New York, Los Angeles
- **Middle East**: Dubai

**To add more cities:** Edit `CITY_CONFIG` in `etl/run_etl.py`

---

## 📝 Notes

- **Units**: All pollutants are normalized to µg/m³ (micrograms per cubic meter)
- **Timezone**: All timestamps are normalized to UTC
- **Data Updates**: ETL should run every 10-15 minutes for near real-time monitoring
- **OLAP Views**: Always refresh materialized views after running ETL

---

## 📄 License

This project is licensed under the MIT License.

---

