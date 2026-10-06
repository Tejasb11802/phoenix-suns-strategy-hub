-- Which sponsor activations generate the strongest engagement
SELECT activation_name,
       COUNT(DISTINCT sponsor_id)                               AS sponsors_using,
       SUM(impressions)                                         AS impressions,
       SUM(engagements)                                         AS engagements,
       ROUND(100.0 * SUM(engagements) / SUM(impressions), 3)    AS engagement_rate_pct,
       ROUND(SUM(estimated_value), 0)                           AS estimated_value,
       ROUND(1.0 * SUM(engagements) / COUNT(DISTINCT sponsor_id), 0) AS engagements_per_sponsor
FROM sponsorship
GROUP BY activation_name
ORDER BY engagement_rate_pct DESC;
