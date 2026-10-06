-- Tickets sold versus attendance for every home game, ranked by revenue
SELECT game_id, game_date, opponent, opponent_tier, weekday, game_type,
       tickets_sold, tickets_scanned, unsold_seats,
       ROUND(100.0 * sell_through, 1)    AS sell_through_pct,
       ROUND(100.0 * no_show_rate, 1)    AS no_show_pct,
       avg_ticket_price, ticket_revenue,
       RANK() OVER (ORDER BY ticket_revenue DESC)                     AS revenue_rank,
       ROUND(100.0 * (sell_through - AVG(sell_through) OVER ()), 1)   AS sell_through_vs_avg_pts
FROM v_game_summary
ORDER BY game_date;
