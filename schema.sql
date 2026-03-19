
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
