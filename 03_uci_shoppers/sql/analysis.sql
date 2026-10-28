-- Load online_shoppers_intention.csv into a table named shopper_sessions.

-- 1. Overall conversion funnel
SELECT
    COUNT(*) AS sessions,
    SUM(CASE WHEN Revenue = TRUE THEN 1 ELSE 0 END) AS buyers,
    AVG(CASE WHEN Revenue = TRUE THEN 1.0 ELSE 0.0 END) AS conversion_rate
FROM shopper_sessions;

-- 2. Conversion by visitor type and weekend
SELECT
    VisitorType,
    Weekend,
    COUNT(*) AS sessions,
    SUM(CASE WHEN Revenue = TRUE THEN 1 ELSE 0 END) AS buyers,
    AVG(CASE WHEN Revenue = TRUE THEN 1.0 ELSE 0.0 END) AS conversion_rate,
    AVG(PageValues) AS avg_page_values,
    AVG(ExitRates) AS avg_exit_rate
FROM shopper_sessions
GROUP BY VisitorType, Weekend
ORDER BY conversion_rate DESC;

-- 3. Monthly operating view
SELECT
    Month,
    COUNT(*) AS sessions,
    SUM(CASE WHEN Revenue = TRUE THEN 1 ELSE 0 END) AS buyers,
    AVG(CASE WHEN Revenue = TRUE THEN 1.0 ELSE 0.0 END) AS conversion_rate,
    AVG(ProductRelated) AS avg_product_pages,
    AVG(ProductRelated_Duration) AS avg_product_duration
FROM shopper_sessions
GROUP BY Month
ORDER BY Month;

-- 4. High-intent sessions for remarketing candidates
SELECT
    VisitorType,
    Month,
    COUNT(*) AS sessions,
    AVG(PageValues) AS avg_page_values,
    AVG(ExitRates) AS avg_exit_rate,
    AVG(CASE WHEN Revenue = TRUE THEN 1.0 ELSE 0.0 END) AS conversion_rate
FROM shopper_sessions
WHERE PageValues > 0 AND ExitRates < 0.08
GROUP BY VisitorType, Month
ORDER BY conversion_rate DESC;
