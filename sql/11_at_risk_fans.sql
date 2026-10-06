-- Retention campaign target list: repeat buyers who went quiet, highest value first
SELECT s.fan_id, f.city, f.age_group, s.games_purchased,
       ROUND(s.total_spend, 0) AS total_spend, s.recency_days, s.engagement_score, s.rfm_score
FROM fan_segments s
JOIN fans f ON f.fan_id = s.fan_id
WHERE s.segment = 'At-Risk Fan'
ORDER BY s.total_spend DESC;
