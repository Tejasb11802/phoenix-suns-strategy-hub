-- Best performing campaign type
SELECT campaign_type,
       COUNT(*)                                             AS campaigns,
       SUM(impressions)                                     AS impressions,
       SUM(conversions)                                     AS conversions,
       ROUND(100.0 * SUM(conversions) / SUM(impressions), 2) AS conversion_rate_pct,
       ROUND(SUM(cost), 0)                                  AS cost,
       ROUND(SUM(revenue_generated), 0)                     AS revenue_generated,
       ROUND((SUM(revenue_generated) - SUM(cost)) / SUM(cost), 2) AS roi
FROM campaigns
GROUP BY campaign_type
ORDER BY roi DESC;
