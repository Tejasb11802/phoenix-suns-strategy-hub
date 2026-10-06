-- Campaign response and conversion by fan segment
SELECT s.segment,
       COUNT(*)                                          AS messages,
       ROUND(100.0 * SUM(r.clicked) / COUNT(*), 1)       AS response_rate_pct,
       SUM(r.converted)                                  AS conversions,
       ROUND(100.0 * SUM(r.converted) / COUNT(*), 2)     AS conversion_rate_pct
FROM campaign_responses r
JOIN fan_segments s ON s.fan_id = r.fan_id
GROUP BY s.segment
ORDER BY conversion_rate_pct DESC;
