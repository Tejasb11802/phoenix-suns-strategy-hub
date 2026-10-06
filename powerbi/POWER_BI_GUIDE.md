# Power BI Guide

`Phoenix_Suns_Strategy_Hub.pbip` is a Power BI Project created by `python run_pipeline.py`. It already contains the
data model, relationships, 42 DAX measures, and 6 report pages.

## Open it

1. Install or update Power BI Desktop (free, Microsoft Store).
2. Run the pipeline once (see the README), then:
   ```
   start "" "powerbi\Phoenix_Suns_Strategy_Hub.pbip"
   ```
3. Visuals are empty at first because a project file stores no data. Click **Home > Refresh**.
4. Apply the Suns colors: **View > Themes > Browse for themes**, pick `powerbi\theme.json`.
5. **File > Save as**, type **Power BI file (.pbix)**. Use the .pbix from now on.
6. Screenshot each page (Win+Shift+S) into `docs\screenshots`.

## If something does not work

| Problem | Fix |
|---|---|
| Desktop says the project format is not supported | Update Power BI Desktop. On older versions turn on the Power BI Project, TMDL, and PBIR options under File > Options and settings > Options > Preview features, then restart |
| Refresh cannot find a file | You moved the folder. Run `python src\04_build_powerbi.py --force` |
| Refresh asks about privacy levels | Choose Ignore for the local folder |
| One visual shows an error | The other pages still work. Note the field in "See details" and fix or remove that visual |

Running the pipeline again does not overwrite the project. `python src\04_build_powerbi.py --force` rebuilds it and
discards saved edits.

## Pages

| Page | Contents |
|---|---|
| Executive Summary | Ticket revenue, attendance rate, average ticket price, sell-through, repeat purchase rate, fan retention rate, campaign conversion, sponsor engagements, revenue by game, revenue by segment |
| Ticketing & Attendance | Tickets sold versus attendance by game, sell-through by opponent tier and weekday, no-show rate, revenue by ticket type, games needing promotional support |
| Fan Segmentation | Segment size and revenue, spend versus engagement, RFM grid, segment profile, at-risk target list |
| Marketing & Campaign Performance | Conversion by campaign and by fan segment, ROI by campaign type, revenue from promotions, campaign detail |
| Sponsorship & Partner Insights | Engagement by partner and by activation, partner by activation matrix, engagement versus attendance |
| Recommendations | Six business actions with sizing |

## Data model

| One side | Many side |
|---|---|
| fans[fan_id] | ticket_sales, attendance, campaign_responses |
| games[game_id] | ticket_sales, attendance, sponsorship |
| campaigns[campaign_id] | campaign_responses, ticket_sales |
| fans[fan_id] | fan_segments[fan_id] (one to one) |

All measures are in the `_Measures` table. The DAX is listed in `measures.dax`.
