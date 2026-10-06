-- Headline KPIs for the executive summary
WITH s AS (
    SELECT SUM(quantity) AS tickets_sold, SUM(ticket_revenue) AS ticket_revenue, COUNT(DISTINCT fan_id) AS unique_buyers
    FROM ticket_sales
),
a AS (SELECT SUM(tickets_scanned) AS tickets_scanned FROM attendance),
g AS (SELECT COUNT(*) AS home_games, SUM(capacity) AS capacity FROM games),
c AS (SELECT SUM(impressions) AS sent, SUM(conversions) AS conversions, SUM(revenue_generated) AS campaign_revenue FROM campaigns),
p AS (SELECT SUM(engagements) AS sponsor_engagements, SUM(estimated_value) AS partner_value FROM sponsorship)
SELECT g.home_games, s.tickets_sold, a.tickets_scanned,
       ROUND(s.ticket_revenue, 0)                                   AS ticket_revenue,
       ROUND(s.ticket_revenue / g.home_games, 0)                    AS revenue_per_game,
       ROUND(s.ticket_revenue / s.tickets_sold, 2)                  AS avg_ticket_price,
       ROUND(100.0 * s.tickets_sold / g.capacity, 1)                AS sell_through_pct,
       ROUND(100.0 * a.tickets_scanned / s.tickets_sold, 1)         AS attendance_rate_pct,
       ROUND(100.0 * (1 - 1.0 * a.tickets_scanned / s.tickets_sold), 1) AS no_show_pct,
       s.unique_buyers,
       ROUND(s.ticket_revenue / s.unique_buyers, 0)                 AS avg_spend_per_fan,
       ROUND(100.0 * c.conversions / c.sent, 2)                     AS campaign_conversion_pct,
       ROUND(c.campaign_revenue, 0)                                 AS campaign_revenue,
       p.sponsor_engagements,
       ROUND(p.partner_value, 0)                                    AS partner_value
FROM s, a, g, c, p;
