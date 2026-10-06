-- Game day and opponent analysis
SELECT opponent_tier, day_type,
       COUNT(*)                                AS games,
       ROUND(100.0 * AVG(sell_through), 1)     AS avg_sell_through_pct,
       ROUND(100.0 * AVG(no_show_rate), 1)     AS avg_no_show_pct,
       ROUND(AVG(avg_ticket_price), 2)         AS avg_ticket_price,
       ROUND(AVG(ticket_revenue), 0)           AS avg_ticket_revenue,
       ROUND(AVG(unsold_seats), 0)             AS avg_unsold_seats
FROM v_game_summary
GROUP BY opponent_tier, day_type
ORDER BY CASE opponent_tier WHEN 'Marquee' THEN 1 WHEN 'Standard' THEN 2 ELSE 3 END, day_type;
