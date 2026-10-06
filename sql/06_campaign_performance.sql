-- Campaign response, conversion, revenue, and ROI
SELECT campaign_id, campaign_name, campaign_type, channel, target_segment, cost, impressions, clicks, conversions,
       ROUND(100.0 * clicks / impressions, 1)             AS response_rate_pct,
       ROUND(100.0 * conversions / impressions, 2)        AS conversion_rate_pct,
       ROUND(revenue_generated, 0)                        AS revenue_generated,
       ROUND(cost / NULLIF(conversions, 0), 2)            AS cost_per_conversion,
       ROUND((revenue_generated - cost) / cost, 2)        AS roi,
       RANK() OVER (ORDER BY (revenue_generated - cost) / cost DESC) AS roi_rank
FROM campaigns
ORDER BY roi DESC;
