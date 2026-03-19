"""
Service Operations Ticket Processing Time Prediction
=====================================================
Generates synthetic ticket data, preprocesses it, trains regression models,
evaluates accuracy, and exports results for dashboard consumption.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import warnings
import json
import os

warnings.filterwarnings("ignore")

# ── Reproducibility ──────────────────────────────────────────────────────────
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# ─────────────────────────────────────────────────────────────────────────────
# 1.  SYNTHETIC DATA GENERATION  (500 000 tickets)
# ─────────────────────────────────────────────────────────────────────────────

print("=" * 60)
print("SERVICE OPERATIONS — TICKET PROCESSING TIME PREDICTION")
print("=" * 60)
print("\n[1/5] Generating 500 000 synthetic tickets …")

N = 500_000
START_DATE = datetime(2022, 1, 1)
END_DATE   = datetime(2024, 12, 31)

CATEGORIES  = ["Hardware", "Software", "Network", "Security", "Database", "Cloud"]
PRIORITIES  = ["Critical", "High", "Medium", "Low"]
STAGES      = ["Intake", "Triage", "Assignment", "Investigation", "Resolution", "Closure"]
TEAMS       = ["Team-Alpha", "Team-Beta", "Team-Gamma", "Team-Delta", "Team-Epsilon"]
REGIONS     = ["North", "South", "East", "West", "Central"]
CHANNELS    = ["Email", "Phone", "Portal", "Chat", "API"]

PRIORITY_MULTIPLIER = {"Critical": 0.4, "High": 0.7, "Medium": 1.0, "Low": 1.5}
CATEGORY_MULTIPLIER = {
    "Hardware": 1.3, "Software": 1.0, "Network": 0.9,
    "Security": 0.6, "Database": 1.2, "Cloud": 0.85,
}
STAGE_HOURS = {
    "Intake": (0.1, 0.5), "Triage": (0.5, 2.0), "Assignment": (0.2, 1.0),
    "Investigation": (2.0, 12.0), "Resolution": (1.0, 8.0), "Closure": (0.1, 0.5),
}

def rand_date(start, end):
    delta = end - start
    return start + timedelta(seconds=random.randint(0, int(delta.total_seconds())))

priorities = np.random.choice(PRIORITIES, N, p=[0.05, 0.20, 0.50, 0.25])
categories = np.random.choice(CATEGORIES, N)
teams      = np.random.choice(TEAMS, N)
regions    = np.random.choice(REGIONS, N)
channels   = np.random.choice(CHANNELS, N, p=[0.30, 0.20, 0.35, 0.10, 0.05])

created_at = [rand_date(START_DATE, END_DATE) for _ in range(N)]

# Stage durations (hours)
stage_cols = {}
total_hours = np.zeros(N)
for stage, (lo, hi) in STAGE_HOURS.items():
    base = np.random.uniform(lo, hi, N)
    pm   = np.array([PRIORITY_MULTIPLIER[p] for p in priorities])
    cm   = np.array([CATEGORY_MULTIPLIER[c] for c in categories])
    noise = np.random.normal(1.0, 0.15, N)
    hours = np.clip(base * pm * cm * noise, lo * 0.5, hi * 3)
    stage_cols[f"{stage.lower()}_hours"] = hours
    total_hours += hours

# Inject realistic noise / outliers
outlier_mask = np.random.rand(N) < 0.02
total_hours[outlier_mask] *= np.random.uniform(3, 8, outlier_mask.sum())
total_hours = np.clip(total_hours, 0.5, 500)

# SLA breach flag  (Critical > 4 h, High > 8 h, Medium > 24 h, Low > 72 h)
SLA = {"Critical": 4, "High": 8, "Medium": 24, "Low": 72}
sla_threshold = np.array([SLA[p] for p in priorities])
sla_breach = (total_hours > sla_threshold).astype(int)

# Reassignment count
reassignments = np.random.poisson(lam=np.where(
    np.isin(priorities, ["Critical", "High"]), 0.5, 1.2), size=N)

# Satisfaction score (1–5, higher processing time → lower score)
raw_sat = 5 - (total_hours / total_hours.max()) * 4
satisfaction = np.clip(np.round(raw_sat + np.random.normal(0, 0.4, N)), 1, 5)

# Hour-of-day / day-of-week features
hour_of_day = np.array([d.hour for d in created_at])
day_of_week = np.array([d.weekday() for d in created_at])
is_weekend  = (day_of_week >= 5).astype(int)

df = pd.DataFrame({
    "ticket_id":       [f"TKT-{i+1:07d}" for i in range(N)],
    "created_at":      created_at,
    "priority":        priorities,
    "category":        categories,
    "team":            teams,
    "region":          regions,
    "channel":         channels,
    "hour_of_day":     hour_of_day,
    "day_of_week":     day_of_week,
    "is_weekend":      is_weekend,
    "reassignments":   reassignments,
    "satisfaction":    satisfaction,
    "sla_breach":      sla_breach,
    "total_hours":     total_hours.round(2),
    **{k: v.round(2) for k, v in stage_cols.items()},
})

print(f"   ✓  {len(df):,} tickets generated — shape {df.shape}")


# ─────────────────────────────────────────────────────────────────────────────
# 2.  SQL SCHEMA EXPORT  (CREATE TABLE + sample INSERT)
# ─────────────────────────────────────────────────────────────────────────────

print("\n[2/5] Writing SQL schema …")

SQL_SCHEMA = """
-- =============================================================
--  SERVICE OPERATIONS TICKET DATABASE SCHEMA
-- =============================================================

CREATE DATABASE IF NOT EXISTS service_ops;
USE service_ops;

-- ── dim_priority ─────────────────────────────────────────────
CREATE TABLE dim_priority (
    priority_id   TINYINT      PRIMARY KEY AUTO_INCREMENT,
    priority_name VARCHAR(20)  NOT NULL UNIQUE,
    sla_hours     FLOAT        NOT NULL,
    weight        FLOAT        NOT NULL
);

INSERT INTO dim_priority (priority_name, sla_hours, weight) VALUES
    ('Critical', 4,  0.05),
    ('High',     8,  0.20),
    ('Medium',   24, 0.50),
    ('Low',      72, 0.25);

-- ── dim_category ─────────────────────────────────────────────
CREATE TABLE dim_category (
    category_id   TINYINT     PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(30) NOT NULL UNIQUE,
    avg_complexity_factor FLOAT DEFAULT 1.0
);

INSERT INTO dim_category (category_name, avg_complexity_factor) VALUES
    ('Hardware', 1.3), ('Software', 1.0), ('Network', 0.9),
    ('Security', 0.6), ('Database', 1.2), ('Cloud',   0.85);

-- ── dim_team ─────────────────────────────────────────────────
CREATE TABLE dim_team (
    team_id   TINYINT     PRIMARY KEY AUTO_INCREMENT,
    team_name VARCHAR(30) NOT NULL UNIQUE
);

INSERT INTO dim_team (team_name) VALUES
    ('Team-Alpha'), ('Team-Beta'), ('Team-Gamma'), ('Team-Delta'), ('Team-Epsilon');

-- ── fact_tickets ─────────────────────────────────────────────
CREATE TABLE fact_tickets (
    ticket_id          VARCHAR(12)  PRIMARY KEY,
    created_at         DATETIME     NOT NULL,
    priority_id        TINYINT      NOT NULL REFERENCES dim_priority(priority_id),
    category_id        TINYINT      NOT NULL REFERENCES dim_category(category_id),
    team_id            TINYINT      NOT NULL REFERENCES dim_team(team_id),
    region             VARCHAR(10)  NOT NULL,
    channel            VARCHAR(10)  NOT NULL,
    hour_of_day        TINYINT      NOT NULL,
    day_of_week        TINYINT      NOT NULL,   -- 0=Mon … 6=Sun
    is_weekend         TINYINT      NOT NULL DEFAULT 0,
    reassignments      TINYINT      NOT NULL DEFAULT 0,
    satisfaction       TINYINT,
    sla_breach         TINYINT      NOT NULL DEFAULT 0,
    total_hours        FLOAT        NOT NULL,
    intake_hours       FLOAT,
    triage_hours       FLOAT,
    assignment_hours   FLOAT,
    investigation_hours FLOAT,
    resolution_hours   FLOAT,
    closure_hours      FLOAT,
    predicted_hours    FLOAT,          -- populated after ML scoring
    INDEX idx_priority  (priority_id),
    INDEX idx_category  (category_id),
    INDEX idx_team      (team_id),
    INDEX idx_created   (created_at),
    INDEX idx_sla       (sla_breach)
);

-- ── Analytical Views ─────────────────────────────────────────
CREATE OR REPLACE VIEW vw_bottleneck_analysis AS
SELECT
    c.category_name,
    p.priority_name,
    t.team_name,
    COUNT(*)                          AS ticket_count,
    ROUND(AVG(f.total_hours),2)       AS avg_total_hours,
    ROUND(AVG(f.investigation_hours),2) AS avg_investigation_hours,
    ROUND(AVG(f.resolution_hours),2)  AS avg_resolution_hours,
    ROUND(SUM(f.sla_breach)/COUNT(*)*100, 1) AS sla_breach_pct
FROM fact_tickets f
JOIN dim_priority p ON f.priority_id = p.priority_id
JOIN dim_category c ON f.category_id = c.category_id
JOIN dim_team     t ON f.team_id     = t.team_id
GROUP BY c.category_name, p.priority_name, t.team_name;

CREATE OR REPLACE VIEW vw_daily_volume AS
SELECT
    DATE(created_at)              AS ticket_date,
    COUNT(*)                      AS daily_tickets,
    ROUND(AVG(total_hours),2)     AS avg_hours,
    SUM(sla_breach)               AS sla_breaches,
    ROUND(AVG(satisfaction),2)    AS avg_satisfaction
FROM fact_tickets
GROUP BY DATE(created_at);
"""

with open("/mnt/user-data/outputs/schema.sql", "w") as f:
    f.write(SQL_SCHEMA)
print("   ✓  schema.sql written")


# ─────────────────────────────────────────────────────────────────────────────
# 3.  FEATURE ENGINEERING + MODEL TRAINING
# ─────────────────────────────────────────────────────────────────────────────

print("\n[3/5] Feature engineering & model training …")

from sklearn.model_selection   import train_test_split
from sklearn.preprocessing     import OrdinalEncoder, StandardScaler
from sklearn.pipeline          import Pipeline
from sklearn.compose           import ColumnTransformer
from sklearn.ensemble          import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model      import Ridge
from sklearn.metrics           import mean_absolute_error, r2_score, mean_squared_error
from sklearn.inspection        import permutation_importance

# ── Feature selection ────────────────────────────────────────
CAT_FEATURES = ["priority", "category", "team", "region", "channel"]
NUM_FEATURES = ["hour_of_day", "day_of_week", "is_weekend", "reassignments"]
TARGET       = "total_hours"

X = df[CAT_FEATURES + NUM_FEATURES]
y = np.log1p(df[TARGET])          # log-transform for skewed target

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=RANDOM_SEED
)

# ── Preprocessor ─────────────────────────────────────────────
cat_enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
preprocessor = ColumnTransformer([
    ("cat", cat_enc,              CAT_FEATURES),
    ("num", StandardScaler(),     NUM_FEATURES),
])

# ── Models ───────────────────────────────────────────────────
MODELS = {
    "Ridge Regression": Ridge(alpha=10),
    "Random Forest":    RandomForestRegressor(
                            n_estimators=120, max_depth=12,
                            n_jobs=-1, random_state=RANDOM_SEED),
    "Gradient Boosting": GradientBoostingRegressor(
                            n_estimators=200, learning_rate=0.08,
                            max_depth=5, subsample=0.8,
                            random_state=RANDOM_SEED),
}

results = {}
best_model_name, best_r2, best_pipeline = None, -np.inf, None

for name, model in MODELS.items():
    pipe = Pipeline([("prep", preprocessor), ("model", model)])
    pipe.fit(X_train, y_train)
    preds = pipe.predict(X_test)

    mae  = mean_absolute_error(np.expm1(y_test), np.expm1(preds))
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2   = r2_score(y_test, preds)

    results[name] = {"MAE_hours": round(mae, 3), "RMSE_log": round(rmse, 4), "R2": round(r2, 4)}
    print(f"   {name:25s}  MAE={mae:.2f}h  R²={r2:.4f}")

    if r2 > best_r2:
        best_r2, best_model_name, best_pipeline = r2, name, pipe

print(f"\n   ★  Best model: {best_model_name}  (R²={best_r2:.4f})")

# ── Score full dataset ────────────────────────────────────────
df["predicted_hours"] = np.expm1(best_pipeline.predict(X)).round(2)
df["prediction_error"] = (df["predicted_hours"] - df["total_hours"]).round(2)


# ─────────────────────────────────────────────────────────────────────────────
# 4.  FEATURE IMPORTANCE
# ─────────────────────────────────────────────────────────────────────────────

print("\n[4/5] Computing feature importances …")

# Use a small sample for permutation importance (speed)
sample_idx   = np.random.choice(len(X_test), size=5000, replace=False)
X_test_s     = X_test.iloc[sample_idx]
y_test_s     = y_test.iloc[sample_idx]

perm = permutation_importance(
    best_pipeline, X_test_s, y_test_s,
    n_repeats=10, random_state=RANDOM_SEED, n_jobs=-1
)
feat_names = CAT_FEATURES + NUM_FEATURES
importance_df = pd.DataFrame({
    "feature":    feat_names,
    "importance": perm.importances_mean.round(5),
    "std":        perm.importances_std.round(5),
}).sort_values("importance", ascending=False).reset_index(drop=True)

print(importance_df.to_string(index=False))


# ─────────────────────────────────────────────────────────────────────────────
# 5.  EXPORT AGGREGATED DATA FOR DASHBOARD
# ─────────────────────────────────────────────────────────────────────────────

print("\n[5/5] Exporting dashboard data …")

# Monthly trend
df["month"] = df["created_at"].dt.to_period("M").astype(str)
monthly = (df.groupby("month")
             .agg(tickets=("ticket_id","count"),
                  avg_hours=("total_hours","mean"),
                  avg_pred =("predicted_hours","mean"),
                  sla_breaches=("sla_breach","sum"))
             .reset_index())
monthly["avg_hours"] = monthly["avg_hours"].round(2)
monthly["avg_pred"]  = monthly["avg_pred"].round(2)

# Priority summary
priority_summary = (df.groupby("priority")
                      .agg(tickets=("ticket_id","count"),
                           avg_hours=("total_hours","mean"),
                           sla_breach_pct=("sla_breach","mean"))
                      .reset_index())
priority_summary["avg_hours"]      = priority_summary["avg_hours"].round(2)
priority_summary["sla_breach_pct"] = (priority_summary["sla_breach_pct"]*100).round(1)

# Category bottleneck
cat_bottleneck = (df.groupby("category")
                    .agg(avg_investigation=("investigation_hours","mean"),
                         avg_resolution  =("resolution_hours","mean"),
                         avg_total       =("total_hours","mean"))
                    .reset_index()
                    .round(2))

# Team performance
team_perf = (df.groupby("team")
               .agg(tickets=("ticket_id","count"),
                    avg_hours=("total_hours","mean"),
                    avg_sat=("satisfaction","mean"),
                    sla_breach_pct=("sla_breach","mean"))
               .reset_index())
team_perf["avg_hours"]      = team_perf["avg_hours"].round(2)
team_perf["avg_sat"]        = team_perf["avg_sat"].round(2)
team_perf["sla_breach_pct"] = (team_perf["sla_breach_pct"]*100).round(1)

# Save CSVs
monthly.to_csv("/mnt/user-data/outputs/monthly_trend.csv",     index=False)
priority_summary.to_csv("/mnt/user-data/outputs/priority_summary.csv", index=False)
cat_bottleneck.to_csv("/mnt/user-data/outputs/category_bottleneck.csv", index=False)
team_perf.to_csv("/mnt/user-data/outputs/team_performance.csv",        index=False)
importance_df.to_csv("/mnt/user-data/outputs/feature_importance.csv",  index=False)

# Save model results JSON (for dashboard)
summary = {
    "generated_tickets": N,
    "model_results": results,
    "best_model": best_model_name,
    "best_r2": best_r2,
    "overall_sla_breach_pct": round(df["sla_breach"].mean()*100, 2),
    "avg_processing_hours": round(df["total_hours"].mean(), 2),
    "median_processing_hours": round(df["total_hours"].median(), 2),
}
with open("/mnt/user-data/outputs/model_summary.json", "w") as f:
    json.dump(summary, f, indent=2)

print("   ✓  monthly_trend.csv")
print("   ✓  priority_summary.csv")
print("   ✓  category_bottleneck.csv")
print("   ✓  team_performance.csv")
print("   ✓  feature_importance.csv")
print("   ✓  model_summary.json")
print("\n✅  Pipeline complete!\n")
print(f"   Tickets generated  : {N:,}")
print(f"   Best model         : {best_model_name}")
print(f"   R² score           : {best_r2:.4f}")
print(f"   Avg processing time: {df['total_hours'].mean():.2f} hours")
print(f"   SLA breach rate    : {df['sla_breach'].mean()*100:.1f}%")
