CREATE VIEW tableau_financials AS
SELECT
    fs.ticker,
    c.company_name,
    c.sector,
    fs.statement_type,
    fs.line_item,
    fs.period,
    fs.value,
    CASE
        WHEN cm.line_item IS NOT NULL THEN TRUE
        ELSE FALSE
    END AS is_core_metric,
    cm.metric_category
FROM financial_statements fs
JOIN companies c
    ON fs.ticker = c.ticker
LEFT JOIN core_metrics cm
    ON fs.line_item = cm.line_item;

SELECT * FROM tableau_financials LIMIT 20;

SELECT is_core_metric, COUNT(*) FROM tableau_financials GROUP BY is_core_metric;

SELECT * FROM tableau_financials WHERE is_core_metric = true LIMIT 10;