-- Size, value, and engagement of each fan segment
SELECT segment,
       COUNT(*)                                             AS fans,
       ROUND(SUM(total_spend), 0)                           AS total_revenue,
       ROUND(100.0 * SUM(total_spend) / SUM(SUM(total_spend)) OVER (), 1) AS pct_of_revenue,
       ROUND(AVG(total_spend), 0)                           AS avg_spend_per_fan,
       ROUND(AVG(games_purchased), 1)                       AS avg_games,
       ROUND(100.0 * SUM(tickets_scanned) / NULLIF(SUM(tickets_purchased), 0), 1) AS attendance_rate_pct,
       ROUND(AVG(engagement_score), 0)                      AS avg_engagement_score,
       ROUND(AVG(rfm_score), 1)                             AS avg_rfm_score
FROM fan_segments
GROUP BY segment
ORDER BY total_revenue DESC;
