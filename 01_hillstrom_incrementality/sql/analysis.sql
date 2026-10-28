-- Load hillstrom.csv into a table named hillstrom before running.

-- 1. Treatment summary
SELECT
    segment,
    COUNT(*) AS customers,
    AVG(visit) AS visit_rate,
    AVG(conversion) AS conversion_rate,
    AVG(spend) AS avg_spend,
    SUM(spend) AS total_spend
FROM hillstrom
GROUP BY segment
ORDER BY segment;

-- 2. Treatment effect vs no-email control
WITH control AS (
    SELECT
        AVG(visit) AS control_visit_rate,
        AVG(conversion) AS control_conversion_rate,
        AVG(spend) AS control_avg_spend
    FROM hillstrom
    WHERE segment = 'No E-Mail'
)
SELECT
    segment,
    AVG(visit) - control_visit_rate AS visit_lift,
    AVG(conversion) - control_conversion_rate AS conversion_lift,
    AVG(spend) - control_avg_spend AS spend_lift_per_customer
FROM hillstrom CROSS JOIN control
WHERE segment <> 'No E-Mail'
GROUP BY segment, control_visit_rate, control_conversion_rate, control_avg_spend;

-- 3. Heterogeneous treatment effect by historical value segment
WITH segmented AS (
    SELECT
        history_segment,
        segment,
        AVG(conversion) AS conversion_rate,
        AVG(spend) AS avg_spend
    FROM hillstrom
    GROUP BY history_segment, segment
)
SELECT
    history_segment,
    segment,
    conversion_rate,
    avg_spend
FROM segmented
ORDER BY history_segment, segment;
