# Metric Definitions

All data is simulated. These definitions are used in the SQL, the Power BI measures, and the report.

## Ticketing and attendance

| Metric | Definition |
|---|---|
| Ticket Revenue | Sum of `ticket_sales[ticket_revenue]` |
| Tickets Sold | Sum of `ticket_sales[quantity]` |
| Average Ticket Price | Ticket Revenue / Tickets Sold |
| Revenue per Game | Ticket Revenue / number of games |
| Sell-Through Rate | Tickets Sold / Capacity (17,000 per game) |
| Tickets Scanned | Sum of `attendance[tickets_scanned]` |
| Attendance Rate | Tickets Scanned / Tickets Sold |
| No-Show Rate | 1 minus Attendance Rate |

## Fan behavior

| Metric | Definition |
|---|---|
| Unique Buyers | Distinct fans with at least one ticket purchase |
| Average Spend per Fan | Ticket revenue / buyers |
| Recency | Days between a fan's last purchased game and the final home game |
| Frequency | Distinct games purchased |
| Monetary | Total ticket spend |
| R, F, M scores | Quintile from 1 to 5 among buyers. 5 is best |
| Engagement Score | 0 to 100. 60% attendance rate plus 40% campaign open rate |
| Repeat Purchase Rate | Non member buyers with 2 or more games / all non member buyers |
| Fan Retention Rate | Non member buyers from the first half of the season who bought again in the second half / first half buyers |

### Segment rules (applied in order, one segment per fan)

| Segment | Rule |
|---|---|
| Season Ticket Member | `membership_status` is Season Ticket Member |
| Prospect | In the database with no purchase |
| At-Risk Fan | 2 or more games and no game in the final 60 days |
| High-Value Fan | 4 or more games, spend in the top 20% of non member buyers, active in the final 60 days |
| Repeat Attendee | 2 or more games, active in the final 60 days |
| First-Time Buyer | Exactly 1 game, inside the final 60 days |
| Lapsed One-Time Buyer | Exactly 1 game, more than 60 days before season end |

`plan_candidate` flags non members who bought 5 or more games.

## Marketing

| Metric | Definition |
|---|---|
| Messages Sent (impressions) | Count of campaign responses |
| Response Rate | Clicked / Sent |
| Conversion Rate | Converted / Sent |
| Revenue Generated | Ticket revenue on sales tagged to the campaign (last-touch attribution) |
| Cost per Conversion | Cost / Conversions |
| ROI | (Revenue Generated minus Cost) / Cost |

## Sponsorship

| Metric | Definition |
|---|---|
| Impressions | Estimated exposures of the activation at the game |
| Engagements | Fan interactions with the activation |
| Engagement Rate | Engagements / Impressions |
| Estimated Value | Impressions / 1,000 x activation CPM, plus $0.35 per engagement |
