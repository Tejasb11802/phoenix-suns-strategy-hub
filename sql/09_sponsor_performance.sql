-- Partner performance: reach, engagement, and estimated value
SELECT sponsor_id, sponsor_name,
       COUNT(DISTINCT activation_name)                          AS activations,
       SUM(impressions)                                         AS impressions,
       SUM(engagements)                                         AS engagements,
       ROUND(100.0 * SUM(engagements) / SUM(impressions), 3)    AS engagement_rate_pct,
       ROUND(SUM(estimated_value), 0)                           AS estimated_value,
       RANK() OVER (ORDER BY SUM(engagements) DESC)             AS engagement_rank
FROM sponsorship
GROUP BY sponsor_id, sponsor_name
ORDER BY engagements DESC;
