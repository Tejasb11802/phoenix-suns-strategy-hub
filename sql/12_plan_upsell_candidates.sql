-- Non members who already buy five or more games: premium and plan upsell list
SELECT s.fan_id, f.city, f.age_group, s.segment, s.games_purchased, s.tickets_purchased,
       ROUND(s.total_spend, 0)                        AS total_spend,
       ROUND(s.total_spend / s.tickets_purchased, 2)  AS avg_price_paid,
       s.engagement_score,
       NTILE(10) OVER (ORDER BY s.total_spend DESC)   AS spend_decile
FROM fan_segments s
JOIN fans f ON f.fan_id = s.fan_id
WHERE s.plan_candidate = 1
ORDER BY s.total_spend DESC;
