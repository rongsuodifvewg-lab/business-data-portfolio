-- Load criteo_sample_5000.csv into a table named criteo_uplift.

-- 1. Treatment sanity check
SELECT
    treatment,
    COUNT(*) AS rows,
    AVG(visit) AS visit_rate,
    AVG(conversion) AS conversion_rate,
    AVG(exposure) AS exposure_rate
FROM criteo_uplift
GROUP BY treatment;

-- 2. Average treatment effect for binary outcomes
WITH treatment_summary AS (
    SELECT
        AVG(CASE WHEN treatment = 1 THEN visit END) AS treated_visit_rate,
        AVG(CASE WHEN treatment = 0 THEN visit END) AS control_visit_rate,
        AVG(CASE WHEN treatment = 1 THEN conversion END) AS treated_conversion_rate,
        AVG(CASE WHEN treatment = 0 THEN conversion END) AS control_conversion_rate
    FROM criteo_uplift
)
SELECT
    treated_visit_rate - control_visit_rate AS visit_lift,
    treated_conversion_rate - control_conversion_rate AS conversion_lift
FROM treatment_summary;

-- 3. Feature-bin heterogeneity check. Replace f0 with other anonymized features as needed.
WITH binned AS (
    SELECT
        treatment,
        visit,
        NTILE(5) OVER (ORDER BY f0) AS f0_quintile
    FROM criteo_uplift
)
SELECT
    f0_quintile,
    AVG(CASE WHEN treatment = 1 THEN visit END) - AVG(CASE WHEN treatment = 0 THEN visit END) AS visit_lift
FROM binned
GROUP BY f0_quintile
ORDER BY f0_quintile;
