from flask import Flask, request, render_template_string
import psycopg2
import os

DB_URL = os.getenv("PG_URL", "postgresql://user:pass@localhost:5432/air_quality")
app = Flask(__name__)

TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Air Quality Analytics Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
      body { background: radial-gradient(circle at top left, #e0f2fe, #f9fafb 55%, #e5e7eb); color: #111827; font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
      .navbar { background: linear-gradient(120deg, #0ea5e9, #22c55e); box-shadow: 0 12px 30px rgba(15, 23, 42, 0.25); }
      .navbar-brand { font-weight: 650; letter-spacing: 0.03em; }
      .card { background: rgba(255, 255, 255, 0.9); backdrop-filter: blur(10px); border-color: rgba(209, 213, 219, 0.7); border-radius: 0.9rem; }
      .card-header { background-color: #f9fafb; border-bottom-color: #e5e7eb; }
      .form-control, .form-select { background-color: #ffffff; color: #111827; border-color: #d1d5db; }
      .form-control:focus, .form-select:focus { box-shadow: 0 0 0 0.15rem rgba(14,165,233,0.35); border-color: #0ea5e9; }
      .aqi-good { color: #16a34a; }
      .aqi-moderate { color: #ca8a04; }
      .aqi-poor { color: #dc2626; }
      .table-custom thead th { background-color: #f3f4f6; }
      .badge-aqi { font-size: 0.75rem; }
      .kpi-card { border-left: 4px solid #0ea5e9; transition: transform 0.12s ease, box-shadow 0.12s ease; }
      .kpi-card:hover { transform: translateY(-2px); box-shadow: 0 14px 35px rgba(15, 23, 42, 0.18); }
      .kpi-good { border-left-color: #16a34a !important; }
      .kpi-moderate { border-left-color: #ca8a04 !important; }
      .kpi-poor { border-left-color: #dc2626 !important; }
      .kpi-label { font-size: 0.8rem; color: #6b7280; text-transform: uppercase; letter-spacing: 0.08em; }
      .kpi-value { font-size: 1.4rem; font-weight: 600; }
      .footer-text { font-size: 0.8rem; color: #6b7280; }
      .legend-pill { font-size: 0.75rem; }
      @media (max-width: 767.98px) {
        .navbar-brand { font-size: 1.1rem; }
        .kpi-value { font-size: 1.2rem; }
        .card-body { padding: 0.85rem 0.95rem; }
        .container { padding-left: 0.95rem; padding-right: 0.95rem; }
      }
    </style>
  </head>
  <body>
    <nav class="navbar navbar-dark mb-4">
      <div class="container-fluid px-4">
        <span class="navbar-brand mb-0 h1">Air Quality Analytics</span>
      </div>
    </nav>

    <div class="container pb-4 pt-2">
      <div class="row mb-3">
        <div class="col-lg-12">
          <div class="card shadow-sm border-0">
            <div class="card-body">
              <div class="mb-3">
                <h4 class="mb-1">City overview</h4>
                <p class="text-muted mb-0">Filter by city and date to explore air quality levels and pollutant trends.</p>
              </div>
              <form class="row g-3 align-items-end" method="get">
                <div class="col-sm-4 col-md-3">
                  <label class="form-label">City</label>
                  <select class="form-select" name="city">
                    {% for opt in cities %}
                      <option value="{{ opt }}" {% if opt == city %}selected{% endif %}>{{ opt }}</option>
                    {% endfor %}
                  </select>
                </div>
                <div class="col-sm-4 col-md-3">
                  <label class="form-label">From</label>
                  <input class="form-control" type="date" name="start" value="{{start}}">
                </div>
                <div class="col-sm-4 col-md-3">
                  <label class="form-label">To</label>
                  <input class="form-control" type="date" name="end" value="{{end}}">
                </div>
                <div class="col-sm-12 col-md-3 d-grid">
                  <button type="submit" class="btn btn-info text-dark fw-semibold mt-3 mt-md-0">Update</button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>

      <div class="row mb-3">
        <div class="col-lg-12">
          <div class="card shadow-sm border-0">
            <div class="card-body d-flex flex-column flex-md-row justify-content-between align-items-md-center">
              <div>
                <div class="kpi-label mb-1">AQI legend</div>
                <p class="text-muted mb-0" style="font-size: 0.8rem;">
                  Air Quality Index bands help you quickly understand health risk levels for the selected city.
                </p>
              </div>
              <div class="mt-3 mt-md-0 d-flex flex-wrap gap-2">
                <span class="badge rounded-pill bg-success-subtle text-success legend-pill">0–50 Good</span>
                <span class="badge rounded-pill bg-warning-subtle text-warning legend-pill">51–100 Moderate</span>
                <span class="badge rounded-pill bg-orange-200 text-dark legend-pill" style="background-color:#fed7aa;">101–150 Unhealthy (sensitive)</span>
                <span class="badge rounded-pill bg-danger-subtle text-danger legend-pill">151+ Unhealthy / Hazardous</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="row g-3 mb-4">
        <div class="col-md-4">
          <div class="card shadow-sm border-0 kpi-card">
            <div class="card-body">
              <div class="kpi-label mb-1">Selected city</div>
              <div class="kpi-value">{{ city }}</div>
              <div class="text-muted" style="font-size: 0.8rem;">From {{ start }} to {{ end }}</div>
            </div>
          </div>
        </div>
        <div class="col-md-4">
          {% set kpi_cls = '' %}
          {% if daily %}
            {% set latest = daily[-1] %}
            {% set latest_aqi = latest[2] or 0 %}
            {% if latest_aqi <= 50 %}
              {% set kpi_cls = 'kpi-good' %}
            {% elif latest_aqi <= 100 %}
              {% set kpi_cls = 'kpi-moderate' %}
            {% else %}
              {% set kpi_cls = 'kpi-poor' %}
            {% endif %}
          {% endif %}
          <div class="card shadow-sm border-0 kpi-card {{ kpi_cls }}">
            <div class="card-body">
              <div class="kpi-label mb-1">Latest average AQI</div>
              {% if daily %}
                {% set latest = daily[-1] %}
                {% set latest_aqi = latest[2] or 0 %}
                <div class="kpi-value">{{ '%.1f'|format(latest_aqi) }}</div>
                <div class="text-muted" style="font-size: 0.8rem;">On {{ latest[1] }}</div>
              {% else %}
                <div class="kpi-value">–</div>
                <div class="text-muted" style="font-size: 0.8rem;">No data</div>
              {% endif %}
            </div>
          </div>
        </div>
        <div class="col-md-4">
          <div class="card shadow-sm border-0 kpi-card">
            <div class="card-body">
              <div class="kpi-label mb-1">Data source</div>
              <div class="kpi-value" style="font-size: 1.1rem;">Open‑Meteo Air Quality</div>
              <div class="text-muted" style="font-size: 0.8rem;">Hourly pollutants, derived European AQI</div>
            </div>
          </div>
        </div>
      </div>

      <div class="row g-4">
        <div class="col-md-6">
          <div class="card shadow-sm border-0 h-100">
            <div class="card-header border-0">
              <div class="d-flex flex-column flex-sm-row justify-content-between align-items-sm-center">
                <h5 class="mb-1 mb-sm-0">Daily AQI ({{ city }})</h5>
                <small class="text-muted">AQI = Air Quality Index (higher value means more polluted / higher health risk).</small>
              </div>
            </div>
            <div class="card-body">
              <div class="mb-3">
                <canvas id="dailyAqiChart" height="160"></canvas>
              </div>
              <div class="d-flex gap-2 mb-3">
                <span class="badge rounded-pill bg-success-subtle text-success legend-pill">Good</span>
                <span class="badge rounded-pill bg-warning-subtle text-warning legend-pill">Moderate</span>
                <span class="badge rounded-pill bg-danger-subtle text-danger legend-pill">Unhealthy +</span>
              </div>
              {% if daily %}
                <div class="table-responsive">
                  <table class="table table-sm align-middle table-custom">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th class="text-end">Average AQI</th>
                        <th class="text-center">Category</th>
                      </tr>
                    </thead>
                    <tbody>
                      {% for row in daily %}
                        {% set aqi = row[2] or 0 %}
                        {% set cls = 'aqi-good' if aqi <= 50 else ('aqi-moderate' if aqi <= 100 else 'aqi-poor') %}
                        {% if aqi <= 50 %}
                          {% set cat = 'Good (Low risk)' %}
                        {% elif aqi <= 100 %}
                          {% set cat = 'Moderate (Acceptable)' %}
                        {% elif aqi <= 150 %}
                          {% set cat = 'Unhealthy for sensitive groups' %}
                        {% elif aqi <= 200 %}
                          {% set cat = 'Unhealthy' %}
                        {% elif aqi <= 300 %}
                          {% set cat = 'Very unhealthy' %}
                        {% else %}
                          {% set cat = 'Hazardous' %}
                        {% endif %}
                        <tr>
                          <td>{{ row[1] }}</td>
                          <td class="text-end fw-semibold {{ cls }}">{{ '%.1f'|format(aqi) }}</td>
                          <td class="text-center">
                            <span class="badge rounded-pill bg-light text-dark border {{ cls }} badge-aqi">{{ cat }}</span>
                          </td>
                        </tr>
                      {% endfor %}
                    </tbody>
                  </table>
                </div>
              {% else %}
                <p class="text-muted mb-0">No AQI data found for this range.</p>
              {% endif %}
            </div>
          </div>
        </div>

        <div class="col-md-6">
          <div class="card shadow-sm border-0 h-100">
            <div class="card-header border-0">
              <h5 class="mb-0">Monthly Pollutant Trends ({{ city }})</h5>
              <small class="text-muted">PM2.5 = tiny particles (≤2.5µm) that can enter lungs. PM10 = larger particles (≤10µm). NO₂/SO₂/O₃/CO = harmful gases.</small>
            </div>
            <div class="card-body">
              <div class="mb-3">
                <canvas id="monthlyPmChart" height="160"></canvas>
              </div>
              {% if monthly %}
                <div class="table-responsive">
                  <table class="table table-sm align-middle table-custom">
                    <thead>
                      <tr>
                        <th>Year</th>
                        <th>Month</th>
                        <th>Pollutant</th>
                        <th class="text-end">Avg Value (µg/m³)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {% for row in monthly %}
                        <tr>
                          <td>{{ row[1] }}</td>
                          <td>{{ '%02d'|format(row[2]) }}</td>
                          <td>{{ row[4] }}</td>
                          <td class="text-end">{{ '%.2f'|format(row[3] or 0) }}</td>
                        </tr>
                      {% endfor %}
                    </tbody>
                  </table>
                </div>
              {% else %}
                <p class="text-muted mb-0">No monthly trend data for this range.</p>
              {% endif %}
            </div>
          </div>
        </div>
      </div>

      <div class="pt-4 text-center footer-text">
        Built for educational purposes – powered by PostgreSQL OLAP views, Open‑Meteo & Flask.
      </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <script>
      (function() {
        const dailyLabels = {{ daily_chart_labels|tojson }};
        const dailyValues = {{ daily_chart_values|tojson }};
        const ctxDaily = document.getElementById('dailyAqiChart');
        if (ctxDaily && dailyLabels.length) {
          new Chart(ctxDaily, {
            type: 'line',
            data: {
              labels: dailyLabels,
              datasets: [{
                label: 'Average AQI',
                data: dailyValues,
                borderColor: '#0ea5e9',
                backgroundColor: 'rgba(14,165,233,0.12)',
                tension: 0.3,
                fill: true,
                pointRadius: 2,
              }]
            },
            options: {
              plugins: { legend: { display: false } },
              scales: {
                x: { ticks: { maxTicksLimit: 6 } },
                y: { beginAtZero: true }
              }
            }
          });
        }

        const monthlyLabels = {{ monthly_pm_labels|tojson }};
        const monthlyValues = {{ monthly_pm_values|tojson }};
        const ctxMonthly = document.getElementById('monthlyPmChart');
        if (ctxMonthly && monthlyLabels.length) {
          new Chart(ctxMonthly, {
            type: 'bar',
            data: {
              labels: monthlyLabels,
              datasets: [{
                label: 'PM2.5 avg (µg/m³)',
                data: monthlyValues,
                backgroundColor: 'rgba(220,38,38,0.65)',
              }]
            },
            options: {
              plugins: { legend: { display: true } },
              scales: {
                x: { ticks: { maxTicksLimit: 6 } },
                y: { beginAtZero: true }
              }
            }
          });
        }
      })();
    </script>
  </body>
</html>
"""


def query(sql, params):
    with psycopg2.connect(DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def get_cities():
    rows = query("SELECT DISTINCT city FROM mv_daily_aqi ORDER BY city", ())
    cities = [r[0] for r in rows]
    if not cities:
        # Fallback in case views are empty on first run
        cities = ["Colombo", "Delhi", "Beijing", "London"]
    return cities


@app.route("/")
def index():
    city = request.args.get("city", "Colombo")
    start = request.args.get("start", "2025-01-01")
    end = request.args.get("end", "2025-12-31")

    daily = query(
        "SELECT city, date, avg_aqi FROM mv_daily_aqi WHERE city=%s AND date BETWEEN %s AND %s ORDER BY date",
        (city, start, end),
    )
    monthly = query(
        """
        SELECT city, year, month, avg_value, pollutant
        FROM mv_monthly_pollution
        WHERE city=%s AND (year || '-' || LPAD(month::text,2,'0')) BETWEEN %s AND %s
        ORDER BY year, month
        """,
        (city, start[:7], end[:7]),
    )
    cities = get_cities()
    if city not in cities:
        cities.insert(0, city)

    # Prepare chart data safely in Python
    daily_chart_labels = [str(r[1]) for r in daily]
    daily_chart_values = [float(r[2] or 0) for r in daily]
    monthly_pm_labels = []
    monthly_pm_values = []
    for r in monthly:
        if r[4] == "pm25":
            monthly_pm_labels.append(f"{r[1]}-{int(r[2]):02d}")
            monthly_pm_values.append(float(r[3] or 0))

    return render_template_string(
        TEMPLATE,
        city=city,
        start=start,
        end=end,
        daily=daily,
        monthly=monthly,
        cities=cities,
        daily_chart_labels=daily_chart_labels,
        daily_chart_values=daily_chart_values,
        monthly_pm_labels=monthly_pm_labels,
        monthly_pm_values=monthly_pm_values,
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)

