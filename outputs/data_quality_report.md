# Data Quality Report

All data in this project is simulated. Raw files are never modified.

## Row counts

| Table | Raw rows | Clean rows |
|---|---:|---:|
| fans | 73,045 | 72,900 |
| games | 41 | 41 |
| campaigns | 12 | 12 |
| ticket_sales | 221,865 | 220,872 |
| attendance | 221,313 | 220,872 |
| campaign_responses | 128,800 | 128,800 |
| sponsorship | 820 | 820 |

## Issues found and actions taken

| Table | Issue | Rows | Action |
|---|---|---:|---|
| fans | Duplicate fan_id rows | 145 | Kept first occurrence |
| fans | City labels in inconsistent case | 1,458 | Standardized to title case |
| ticket_sales | Duplicate transaction_id rows | 883 | Kept first occurrence |
| ticket_sales | Zero or negative quantity | 110 | Removed as invalid records |
| ticket_sales | Inconsistent purchase_channel labels | 2,623 | Mapped to standard labels |
| ticket_sales | Missing ticket_revenue | 331 | Imputed from median unit price for same game, section, and ticket type |
| attendance | Attendance row with no matching sale | 441 | Removed |

## Validation checks

| Check | Result | Detail |
|---|---|---|
| Primary key unique: fans.fan_id | PASS |  |
| Primary key unique: games.game_id | PASS |  |
| Primary key unique: campaigns.campaign_id | PASS |  |
| Primary key unique: ticket_sales.transaction_id | PASS |  |
| Primary key unique: attendance.attendance_id | PASS |  |
| Primary key unique: campaign_responses.response_id | PASS |  |
| Primary key unique: sponsorship.sponsorship_id | PASS |  |
| Every sale has a known fan and game | PASS |  |
| Every attendance row has a sale | PASS |  |
| One attendance row per sale | PASS |  |
| Tickets sold never exceed capacity | PASS | max sell-through 100.0% |
| Tickets scanned never exceed tickets sold | PASS |  |
| No missing or non positive revenue | PASS |  |
| Campaign conversions match response rows | PASS |  |
| Campaign revenue matches tagged sales | PASS |  |
| One segment per fan | PASS |  |
