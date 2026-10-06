# Executive Summary: Phoenix Suns Fan Revenue & Strategy Intelligence Hub

Independent demonstration project by Tejas Bhanushali. Not affiliated with or endorsed by the Phoenix Suns.
This project uses a simulated dataset designed to reflect realistic sports business scenarios and to demonstrate
an analytical approach. No number here describes actual Suns performance.

## Season snapshot (simulated, 41 home games)

| KPI | Value |
|---|---:|
| Ticket revenue | $64.08M |
| Revenue per game | $1.56M |
| Average ticket price | $106.98 |
| Sell-through rate | 85.9% |
| Attendance rate (scanned / sold) | 83.3% |
| No-show rate | 16.7% |
| Repeat purchase rate | 56.0% |
| Fan retention rate (first half buyers who returned) | 50.4% |
| Campaign conversion rate | 3.87% |
| Sponsor engagements | 6,746,926 |

## Key insights

1. Sell-through averaged 85.9% but ranged from 73% to 100%. 8 soft games hold 32% of all unsold seats, and 100% of them are weekday games.
2. 16.7% of tickets sold were never scanned. No-shows run 18.6% on weekdays against 13.9% on weekends.
3. 6,471 repeat buyers went quiet in the final 60 days. They average $860 per fan, more than active repeat attendees ($684).
4. 5,799 non members bought five or more separate games at single game prices, averaging 2.6 seats at $118 per seat.
5. Email, SMS, and push returned 12.9x on cost against 0.7x for paid media. Upsell was the best campaign type at 15.0x ROI.

## Recommended actions

| # | Action | What to do | Sizing (scenario, not a forecast) |
|---|---|---|---|
| 1 | Retarget at-risk and first-time buyers with post-game offers | Win-back offers to 6,471 at-risk fans, highest spenders first, and a second game offer within 14 days for 5,706 first-time buyers. | Recovering 15% of at-risk value is worth about $834,876. A repeat attendee averages $684 against $280 for a first-time buyer. |
| 2 | Bundle weekday games to lift sell-through | Weeknight bundles, group offers, and theme nights on the 8 games with the weakest demand. | Selling 25% of 31,155 unsold seats at a 20% discount is worth about $589,278. |
| 3 | Upsell high-frequency fans into plans and premium products | Mini plan and premium seating offers to 5,799 non members who already buy five or more games. | 10% take-up adding 3 games each is worth about $536,092. |
| 4 | Focus campaigns on high-conversion segments and owned channels | Prioritize the High-Value Fan segment, which converts at 23.4%, and move part of the $88,000 paid media budget into email, SMS, and push. | Owned channels returned 12.9x against 0.7x for paid media. Best campaign: App Flash Sale at 21.7x. |
| 5 | Strengthen sponsor activations tied to high-engagement environments | Add interactive activations for Saguaro Auto Group and Valley Sun Energy, the two partners with the lowest engagement. Both rely on signage and displays only. | Fan Zone Sampling engages 11.1% of the fans it reaches against 0.04% for Courtside LED Signage. |
| 6 | Monitor sold versus scanned gaps to reduce no-shows | Weekly sold versus scanned report by game, plus ticket exchange and outreach for 1,192 season ticket accounts using under 75% of their tickets. | Those accounts hold $13.87M of ticket revenue. Weekday no-shows run 18.6% against 13.9% on weekends. |

## Segment value

| Segment | Fans | Revenue | Share | Avg spend | Avg games | Engagement score |
|---|---:|---:|---:|---:|---:|---:|
| Season Ticket Member | 2,900 | $33.83M | 52.8% | $11,667 | 41.0 | 45 |
| High-Value Fan | 4,030 | $13.54M | 21.1% | $3,360 | 8.6 | 75 |
| Repeat Attendee | 9,763 | $6.68M | 10.4% | $684 | 3.3 | 72 |
| At-Risk Fan | 6,471 | $5.57M | 8.7% | $860 | 3.0 | 74 |
| Lapsed One-Time Buyer | 10,248 | $2.87M | 4.5% | $280 | 1.0 | 72 |
| First-Time Buyer | 5,706 | $1.60M | 2.5% | $280 | 1.0 | 66 |

## Method notes

- Segments use recency, frequency, and monetary scores plus rules documented in `docs/metric_definitions.md`.
- Campaign revenue uses last-touch attribution. It ranks campaigns and does not prove incremental lift.
- Sizing figures are scenarios built from observed averages and stated assumptions.
