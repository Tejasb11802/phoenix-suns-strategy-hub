-- Repeat purchase rate and in-season retention for non member buyers
SELECT COUNT(*)                                                                          AS non_member_buyers,
       SUM(CASE WHEN games_purchased >= 2 THEN 1 ELSE 0 END)                             AS repeat_buyers,
       ROUND(100.0 * SUM(CASE WHEN games_purchased >= 2 THEN 1 ELSE 0 END) / COUNT(*), 1) AS repeat_purchase_rate_pct,
       SUM(bought_first_half)                                                            AS first_half_buyers,
       SUM(CASE WHEN bought_first_half = 1 AND bought_second_half = 1 THEN 1 ELSE 0 END)  AS retained,
       ROUND(100.0 * SUM(CASE WHEN bought_first_half = 1 AND bought_second_half = 1 THEN 1 ELSE 0 END)
             / SUM(bought_first_half), 1)                                                AS retention_rate_pct
FROM fan_segments
WHERE games_purchased > 0 AND segment <> 'Season Ticket Member';
