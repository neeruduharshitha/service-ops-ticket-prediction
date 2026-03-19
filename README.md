# 🎫 Service Operations — Ticket Processing Time Prediction

> Predicting service ticket resolution time using machine learning on 500,000+ real-world style tickets — built with Python, SQL, and an interactive Power BI-style dashboard.

---

## 📌 Project Overview

Service operations teams handle thousands of tickets daily across multiple priority levels, categories, and workflow stages. Delays in resolution directly impact SLA compliance and customer satisfaction.

This project builds an end-to-end pipeline that:
- Analyzes **500,000+ service tickets** with timestamps, workflow stages, and priority levels
- Trains **regression models** to predict ticket processing time
- Improves prediction accuracy by **15% over baseline**
- Visualizes bottlenecks through an **interactive dashboard** to support operational optimization

---

## 🗂️ Repository Structure

```
service-ops-ticket-prediction/
├── ticket_pipeline.py       # Full ML pipeline (data gen, training, export)
├── schema.sql               # Star schema database design + analytical views
├── dashboard.html           # Interactive Power BI-style analytics dashboard
└── data/
    ├── monthly_trend.csv        # Monthly volume & avg processing hours
    ├── priority_summary.csv     # SLA breach rates by priority tier
    ├── category_bottleneck.csv  # Investigation vs resolution by category
    ├── team_performance.csv     # Team-level performance metrics
    ├── feature_importance.csv   # ML feature importance scores
    └── model_summary.json       # Model benchmarks and KPIs
```

---

## 🛠️ Tech Stack

| Layer | Tools |
|-------|-------|
| Data Processing | Python, Pandas, NumPy |
| Machine Learning | Scikit-learn (Ridge, Random Forest, Gradient Boosting) |
| Database | SQL (MySQL-compatible schema, analytical views) |
| Visualization | HTML, Chart.js (Power BI-style dashboard) |

---

## 🤖 ML Models & Results

Three regression models were trained and benchmarked on a 100K ticket test set:

| Model | MAE (hours) | R² Score |
|-------|-------------|----------|
| Ridge Regression | 6.15h | 0.116 |
| Random Forest | 4.34h | 0.533 |
| ✅ **Gradient Boosting** | **4.33h** | **0.535** |

**Best Model:** Gradient Boosting
- `n_estimators=200`, `learning_rate=0.08`, `max_depth=5`, `subsample=0.8`
- Log₁(y) transform applied to handle skewed target distribution
- **+15% accuracy improvement** over Ridge baseline

---

## 📊 Key Findings

- **Priority** and **Category** account for ~99.8% of predictive signal
- **Hardware** tickets take the longest on average (20.5h)
- **Security** tickets are resolved fastest (9.5h)
- **Critical** priority has the highest SLA breach rate (75.1%)
- Overall SLA compliance rate: **80.6%**
- Average processing time: **15.4 hours**

---

## 🚀 How to Run

### Option 1 — Google Colab (Recommended)
```python
# Upload ticket_pipeline.py to Colab, then run:
import os
os.makedirs("/content/outputs", exist_ok=True)
!python ticket_pipeline.py
```

### Option 2 — Local Environment
```bash
# Install dependencies
pip install scikit-learn pandas numpy

# Run the pipeline
python ticket_pipeline.py
```

### Option 3 — View the Dashboard
Simply open `dashboard.html` in any browser — no server required.

---

## 🗄️ Database Setup

The `schema.sql` file is MySQL-compatible and includes:
- `fact_tickets` — main ticket data with all features and predictions
- `dim_priority`, `dim_category`, `dim_team` — dimension tables
- `vw_bottleneck_analysis` — aggregated view for operational insights
- `vw_daily_volume` — daily ticket volume and SLA trends

```bash
# Run in MySQL
mysql -u root -p < schema.sql
```

---

## 📈 Dashboard Features

The `dashboard.html` includes:
- **5 KPI cards** — volume, avg time, SLA breach rate, model accuracy, CSAT
- **Monthly trend chart** — actual vs predicted hours with ticket volume
- **SLA compliance gauge** — breach rate broken down by priority
- **Category bottleneck chart** — investigation vs resolution time per category
- **Feature importance chart** — permutation importance from best model
- **Model comparison table** — all 3 models benchmarked
- **Team performance radar** — multi-metric team comparison

---

## 📁 Data Dictionary

| Column | Description |
|--------|-------------|
| `ticket_id` | Unique ticket identifier |
| `created_at` | Timestamp of ticket creation |
| `priority` | Critical / High / Medium / Low |
| `category` | Hardware / Software / Network / Security / Database / Cloud |
| `team` | Assigned support team |
| `total_hours` | Actual resolution time (target variable) |
| `predicted_hours` | Model-predicted resolution time |
| `sla_breach` | 1 if SLA was breached, 0 otherwise |
| `satisfaction` | Post-resolution CSAT score (1–5) |

---

## 👤 Author

**Harshitha Reddy**
- GitHub: [@neeruduharshitha](https://github.com/neeruduharshitha)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
