"""
Step 3: Analysis.

Runs every query in sql/, exports the results, builds charts, and writes
outputs/key_numbers.json and outputs/executive_summary.md.
Every number is computed from the data at run time.
"""
import json
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "suns_hub.db"
OUT = ROOT / "outputs"
RES, CH = OUT / "sql_results", OUT / "charts"
RES.mkdir(parents=True, exist_ok=True)
CH.mkdir(parents=True, exist_ok=True)

PURPLE, ORANGE, GRAY, LILAC, YELLOW, DARK = "#1D1160", "#E56020", "#63727A", "#8C7BB8", "#F9AD1B", "#252423"
TIER_COLOR = {"Marquee": PURPLE, "Standard": LILAC, "Value": ORANGE}
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold", "axes.titlesize": 12, "axes.titlecolor": PURPLE, "figure.dpi": 130})


def money(x):
    return f"${x / 1e6:,.2f}M" if abs(x) >= 1e6 else f"${x:,.0f}"


def save(fig, name):
    fig.tight_layout()
    fig.savefig(CH / name, bbox_inches="tight")
    plt.close(fig)


def write_video_script(k):
    """Video walkthrough script with the current numbers filled in."""
    text = f"""# Video Walkthrough Script (about 4 minutes)

Record with Loom: screen plus camera bubble. Open the Power BI file before you start, slicers cleared.
Read it through twice, then say it in your own words.

## 1. Intro (20 seconds)
On screen: Executive Summary page.

"Hi, I'm Tejas Bhanushali. After our conversation, I wanted to build a short independent project inspired by the
type of work this Strategy and Analytics internship might support. So I created a Phoenix Suns Fan Revenue and
Strategy Intelligence Hub."

## 2. Business goal (25 seconds)
"The goal was to explore how the Suns could use ticketing, attendance, fan engagement, campaign, and sponsorship
data together to find commercial opportunities and support better business decisions."

## 3. Data and tools (35 seconds)
"To be clear up front: this uses a simulated dataset that I designed to reflect realistic sports business
scenarios. It is not Suns data, and the numbers do not describe the team's actual performance. I built seven
related tables covering fans, games, ticket sales, attendance, campaigns, and sponsorship. I used Python and SQL
for preparation, validation, and analysis, and Power BI for the reporting layer."

## 4. Dashboard walkthrough (2 minutes)

**Executive Summary (15 seconds)**
"This page is the one minute view: {money(k['ticket_revenue'])} in ticket revenue, {k['sell_through_pct']:.0f} percent
sell-through, an {k['attendance_rate_pct']:.0f} percent attendance rate, and a {k['retention_rate_pct']:.0f} percent fan
retention rate."

**Ticketing & Attendance (30 seconds)**
"Here I compare tickets sold with tickets actually scanned. About {k['no_show_pct']:.0f} percent of sold tickets never
showed up, and it is worse on weekdays. {k['best_tier_day']} games average {k['best_tier_day_pct']:.0f} percent
sell-through, while {k['worst_tier_day'].lower()} games average {k['worst_tier_day_pct']:.0f} percent. {k['soft_games']} games
account for {k['soft_unsold_share_pct']} percent of all unsold seats."

**Fan Segmentation (30 seconds)**
"I scored every fan on recency, frequency, and spend, plus an engagement score, and built six segments. Two stand
out. About {k['at_risk_fans']:,} repeat buyers went quiet in the last 60 days of the season. And about
{k['plan_candidates']:,} fans bought five or more separate games without a plan, which makes them natural upsell
candidates."

**Marketing & Campaign Performance (20 seconds)**
"On campaigns, email, SMS, and push had an ROI of about {k['owned_roi']:.0f}x, against {k['paid_roi']:.1f}x for paid media.
The {k['top_segment_conv']} segment converts at {k['top_segment_conv_pct']:.0f} percent. I used last-touch attribution,
so I treat this as a ranking, not proof of lift."

**Sponsorship & Partner Insights (15 seconds)**
"For partners, interactive activations win. {k['top_activation']} engages about {k['top_activation_rate']:.0f} percent of
the fans it reaches, while signage engages well under one percent."

**Recommendations (10 seconds)**
"The last page turns all of that into six actions, each with a rough size."

## 5. Key insights and recommendations (35 seconds)
"If I had to pick three: first, retarget those at-risk fans, which is worth roughly {money(k['at_risk_recover'])} if 15
percent come back. Second, bundle weekday games where demand is weakest. Third, upsell the frequent buyers into
plans or premium products."

## 6. Close (20 seconds)
"I really enjoyed building this because it confirmed how interested I am in sports business analytics, and
especially in the strategic work this role supports. The dashboard, report, and code are linked below. Thank you
again for your time."

## Recording checklist
- Slicers cleared so the numbers match this script.
- Collapse the Filters, Visualizations, and Data panes so the page fills the screen.
- Keep it under 5 minutes. If you run long, cut the sponsorship section first.
- Say "simulated dataset" clearly in section 3. Do not skip it.
"""
    (ROOT / "docs" / "video_script.md").write_text(text, encoding="utf-8")


def main():
    con = sqlite3.connect(DB)
    r = {}
    for path in sorted((ROOT / "sql").glob("*.sql")):
        if path.name.startswith("00_"):
            continue
        r[path.stem[:2]] = pd.read_sql(path.read_text(encoding="utf-8"), con)
        r[path.stem[:2]].to_csv(RES / f"{path.stem}.csv", index=False)
    seg_all = pd.read_sql("SELECT * FROM fan_segments", con)
    con.close()
    print(f"  {len(r)} SQL queries run, results in outputs/sql_results")

    kpi, games, tier_day, segval, ret = r["01"].iloc[0], r["02"], r["03"], r["04"], r["05"].iloc[0]
    camp, ctype, conv_seg, spon, act = r["06"], r["07"], r["08"], r["09"], r["10"]
    games["game_date"] = pd.to_datetime(games["game_date"])
    games["day_type"] = games["weekday"].isin(["Friday", "Saturday", "Sunday"]).map({True: "Weekend", False: "Weekday"})

    # ---------------- charts ----------------
    fig, ax = plt.subplots(figsize=(12, 4.2))
    x = range(len(games))
    ax.bar(x, games["tickets_sold"], color="#D9D3E8", label="Tickets sold")
    ax.bar(x, games["tickets_scanned"], color=PURPLE, label="Tickets scanned (attended)")
    ax.axhline(17000, color=ORANGE, ls="--", lw=1, label="Capacity")
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"{d:%b %d}\n{o.split()[-1]}" for d, o in zip(games["game_date"], games["opponent"])],
                       fontsize=6.5, rotation=90)
    ax.set_ylim(8000, 18200)
    ax.set_title("Tickets sold versus attendance by home game", pad=22)
    ax.legend(ncol=3, frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0))
    save(fig, "01_sold_vs_attendance.png")

    piv = games.pivot_table(index="opponent_tier", columns="day_type", values=["sell_through_pct", "no_show_pct"],
                            aggfunc="mean").reindex(["Marquee", "Standard", "Value"])
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    for ax, metric, title in zip(axes, ["sell_through_pct", "no_show_pct"], ["Average sell-through", "Average no-show rate"]):
        piv[metric].plot(kind="bar", ax=ax, color=["#B8B2D0", PURPLE], width=0.75)
        ax.set_title(title)
        ax.set_xlabel("")
        ax.yaxis.set_major_formatter(mtick.PercentFormatter())
        ax.tick_params(axis="x", rotation=0)
        ax.legend(frameon=False, title="")
        for c in ax.containers:
            ax.bar_label(c, fmt="%.0f%%", fontsize=8)
    save(fig, "02_opponent_and_weekday.png")

    s = segval[segval["total_revenue"] > 0].sort_values("total_revenue")
    fig, axes = plt.subplots(1, 2, figsize=(11, 3.8), sharey=True)
    axes[0].barh(s["segment"], s["fans"], color="#B8B2D0")
    axes[0].set_title("Fans in segment")
    axes[0].bar_label(axes[0].containers[0], fmt="{:,.0f}", fontsize=8, padding=2)
    axes[1].barh(s["segment"], s["total_revenue"] / 1e6, color=PURPLE)
    axes[1].set_title("Ticket revenue ($M)")
    axes[1].bar_label(axes[1].containers[0], fmt="%.1f", fontsize=8, padding=2)
    save(fig, "03_segment_size_vs_revenue.png")

    fig, ax = plt.subplots(figsize=(7.5, 4))
    colors = [ORANGE if n == "At-Risk Fan" else PURPLE for n in s["segment"]]
    ax.scatter(s["avg_engagement_score"], s["avg_spend_per_fan"], s=s["fans"] / 12, c=colors, alpha=0.8)
    for row in s.itertuples():
        ax.annotate(row.segment, (row.avg_engagement_score, row.avg_spend_per_fan), fontsize=8,
                    xytext=(6, 6), textcoords="offset points")
    ax.set_yscale("log")
    ax.set_xlabel("Average engagement score (0 to 100)")
    ax.set_ylabel("Average spend per fan ($, log scale)")
    ax.set_title("Spend versus engagement by segment (bubble = fans)")
    save(fig, "04_spend_vs_engagement.png")

    c = camp.sort_values("roi")
    ch_color = c["channel"].map({"Email": PURPLE, "SMS": LILAC, "Push": GRAY, "Paid Social": ORANGE, "Paid Search": YELLOW})
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
    axes[0].barh(c["campaign_name"], c["conversion_rate_pct"], color=ch_color)
    axes[0].set_title("Conversion rate (%)")
    axes[0].bar_label(axes[0].containers[0], fmt="%.1f", fontsize=8, padding=2)
    axes[1].barh(c["campaign_name"], c["roi"], color=ch_color)
    axes[1].set_title("ROI (revenue minus cost, divided by cost)")
    axes[1].bar_label(axes[1].containers[0], fmt="%.1fx", fontsize=8, padding=2)
    save(fig, "05_campaign_performance.png")

    cs = conv_seg[conv_seg["conversions"] > 0].sort_values("conversion_rate_pct")
    fig, ax = plt.subplots(figsize=(7, 3.4))
    ax.barh(cs["segment"], cs["conversion_rate_pct"], color=PURPLE)
    ax.set_title("Campaign conversion rate by fan segment (%)")
    ax.bar_label(ax.containers[0], fmt="%.1f%%", fontsize=8, padding=2)
    save(fig, "06_conversion_by_segment.png")

    a = act.sort_values("engagement_rate_pct")
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    ax.barh(a["activation_name"], a["engagement_rate_pct"], color=PURPLE)
    ax.set_title("Engagement rate by sponsor activation (%)")
    ax.bar_label(ax.containers[0], fmt="%.2f%%", fontsize=8, padding=2)
    save(fig, "07_activation_engagement.png")

    sp = spon.sort_values("engagements")
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    ax.barh(sp["sponsor_name"], sp["engagements"] / 1e3,
            color=[ORANGE if v < sp["engagements"].median() / 5 else PURPLE for v in sp["engagements"]])
    ax.set_title("Fan engagements by partner (thousands)")
    ax.bar_label(ax.containers[0], fmt="{:,.0f}", fontsize=8, padding=2)
    save(fig, "08_partner_engagement.png")
    print("  8 charts written to outputs/charts")

    # ---------------- findings ----------------
    avg_st = games["sell_through_pct"].mean()
    soft = games[games["sell_through_pct"] < avg_st - 5].sort_values("sell_through_pct")
    soft_unsold, unsold_total = int(soft["unsold_seats"].sum()), int(games["unsold_seats"].sum())
    soft_weekday = (soft["day_type"] == "Weekday").mean()
    soft_price = soft["ticket_revenue"].sum() / soft["tickets_sold"].sum()
    soft_gain = 0.25 * soft_unsold * soft_price * 0.80
    td = tier_day.set_index(["opponent_tier", "day_type"])
    best, worst = td["avg_sell_through_pct"].idxmax(), td["avg_sell_through_pct"].idxmin()
    wk = games.groupby("day_type")["no_show_pct"].mean()

    sv = segval.set_index("segment")
    at_risk = seg_all[seg_all["segment"] == "At-Risk Fan"]
    first_time = seg_all[seg_all["segment"] == "First-Time Buyer"]
    plan = seg_all[seg_all["plan_candidate"] == 1]
    seats = plan["tickets_purchased"].sum() / plan["games_purchased"].sum()
    price = plan["total_spend"].sum() / plan["tickets_purchased"].sum()
    plan_gain = 0.10 * len(plan) * 3 * seats * price
    ar_recover = 0.15 * at_risk["total_spend"].sum()
    members = seg_all[seg_all["segment"] == "Season Ticket Member"]
    low_use = members[members["attendance_rate"] < 0.75]

    owned = camp[camp["channel"].isin(["Email", "SMS", "Push"])]
    paid = camp[~camp["channel"].isin(["Email", "SMS", "Push"])]
    owned_roi = (owned["revenue_generated"].sum() - owned["cost"].sum()) / owned["cost"].sum()
    paid_roi = (paid["revenue_generated"].sum() - paid["cost"].sum()) / paid["cost"].sum()
    best_c, worst_c, best_type = camp.iloc[0], camp.iloc[-1], ctype.iloc[0]
    top_seg = conv_seg.iloc[0]
    top_act, low_act = act.iloc[0], act.iloc[-1]
    top_sp = spon.iloc[0]
    weak = spon.sort_values("engagements").head(2)["sponsor_name"].tolist()

    insights = [
        f"Sell-through averaged {kpi['sell_through_pct']:.1f}% but ranged from {games['sell_through_pct'].min():.0f}% to "
        f"{games['sell_through_pct'].max():.0f}%. {len(soft)} soft games hold {soft_unsold / unsold_total:.0%} of all unsold "
        f"seats, and {soft_weekday:.0%} of them are weekday games.",
        f"{kpi['no_show_pct']:.1f}% of tickets sold were never scanned. No-shows run {wk['Weekday']:.1f}% on weekdays "
        f"against {wk['Weekend']:.1f}% on weekends.",
        f"{len(at_risk):,} repeat buyers went quiet in the final 60 days. They average ${at_risk['total_spend'].mean():,.0f} "
        f"per fan, more than active repeat attendees (${sv.loc['Repeat Attendee', 'avg_spend_per_fan']:,.0f}).",
        f"{len(plan):,} non members bought five or more separate games at single game prices, averaging "
        f"{seats:.1f} seats at ${price:,.0f} per seat.",
        f"Email, SMS, and push returned {owned_roi:.1f}x on cost against {paid_roi:.1f}x for paid media. "
        f"{best_type['campaign_type']} was the best campaign type at {best_type['roi']:.1f}x ROI.",
    ]
    recs = [
        {"action": "Retarget at-risk and first-time buyers with post-game offers",
         "detail": f"Win-back offers to {len(at_risk):,} at-risk fans, highest spenders first, and a second game offer "
                   f"within 14 days for {len(first_time):,} first-time buyers.",
         "sizing": f"Recovering 15% of at-risk value is worth about {money(ar_recover)}. A repeat attendee averages "
                   f"${sv.loc['Repeat Attendee', 'avg_spend_per_fan']:,.0f} against "
                   f"${sv.loc['First-Time Buyer', 'avg_spend_per_fan']:,.0f} for a first-time buyer."},
        {"action": "Bundle weekday games to lift sell-through",
         "detail": f"Weeknight bundles, group offers, and theme nights on the {len(soft)} games with the weakest demand.",
         "sizing": f"Selling 25% of {soft_unsold:,} unsold seats at a 20% discount is worth about {money(soft_gain)}."},
        {"action": "Upsell high-frequency fans into plans and premium products",
         "detail": f"Mini plan and premium seating offers to {len(plan):,} non members who already buy five or more games.",
         "sizing": f"10% take-up adding 3 games each is worth about {money(plan_gain)}."},
        {"action": "Focus campaigns on high-conversion segments and owned channels",
         "detail": f"Prioritize the {top_seg['segment']} segment, which converts at {top_seg['conversion_rate_pct']:.1f}%, and move "
                   f"part of the {money(paid['cost'].sum())} paid media budget into email, SMS, and push.",
         "sizing": f"Owned channels returned {owned_roi:.1f}x against {paid_roi:.1f}x for paid media. Best campaign: "
                   f"{best_c['campaign_name']} at {best_c['roi']:.1f}x."},
        {"action": "Strengthen sponsor activations tied to high-engagement environments",
         "detail": f"Add interactive activations for {weak[0]} and {weak[1]}, the two partners with the lowest engagement. "
                   f"Both rely on signage and displays only.",
         "sizing": f"{top_act['activation_name']} engages {top_act['engagement_rate_pct']:.1f}% of the fans it reaches "
                   f"against {low_act['engagement_rate_pct']:.2f}% for {low_act['activation_name']}."},
        {"action": "Monitor sold versus scanned gaps to reduce no-shows",
         "detail": f"Weekly sold versus scanned report by game, plus ticket exchange and outreach for {len(low_use):,} "
                   f"season ticket accounts using under 75% of their tickets.",
         "sizing": f"Those accounts hold {money(low_use['total_spend'].sum())} of ticket revenue. Weekday no-shows run "
                   f"{wk['Weekday']:.1f}% against {wk['Weekend']:.1f}% on weekends."},
    ]
    key = {
        "home_games": int(kpi["home_games"]), "ticket_revenue": float(kpi["ticket_revenue"]),
        "revenue_per_game": float(kpi["revenue_per_game"]), "tickets_sold": int(kpi["tickets_sold"]),
        "tickets_scanned": int(kpi["tickets_scanned"]), "avg_ticket_price": float(kpi["avg_ticket_price"]),
        "sell_through_pct": float(kpi["sell_through_pct"]), "attendance_rate_pct": float(kpi["attendance_rate_pct"]),
        "no_show_pct": float(kpi["no_show_pct"]), "unique_buyers": int(kpi["unique_buyers"]),
        "avg_spend_per_fan": float(kpi["avg_spend_per_fan"]),
        "repeat_purchase_rate_pct": float(ret["repeat_purchase_rate_pct"]),
        "retention_rate_pct": float(ret["retention_rate_pct"]),
        "campaign_conversion_pct": float(kpi["campaign_conversion_pct"]),
        "campaign_revenue": float(kpi["campaign_revenue"]),
        "sponsor_engagements": int(kpi["sponsor_engagements"]), "partner_value": float(kpi["partner_value"]),
        "best_tier_day": f"{best[0]} {best[1].lower()}", "best_tier_day_pct": float(td.loc[best, "avg_sell_through_pct"]),
        "worst_tier_day": f"{worst[0]} {worst[1].lower()}", "worst_tier_day_pct": float(td.loc[worst, "avg_sell_through_pct"]),
        "weekday_no_show_pct": round(float(wk["Weekday"]), 1), "weekend_no_show_pct": round(float(wk["Weekend"]), 1),
        "soft_games": int(len(soft)), "soft_unsold_share_pct": round(100 * soft_unsold / unsold_total),
        "at_risk_fans": int(len(at_risk)), "at_risk_revenue": float(at_risk["total_spend"].sum()),
        "at_risk_recover": float(ar_recover), "plan_candidates": int(len(plan)),
        "member_revenue_share_pct": float(sv.loc["Season Ticket Member", "pct_of_revenue"]),
        "owned_roi": round(float(owned_roi), 1), "paid_roi": round(float(paid_roi), 1),
        "best_campaign": best_c["campaign_name"], "best_campaign_roi": float(best_c["roi"]),
        "best_campaign_conv": float(best_c["conversion_rate_pct"]),
        "worst_campaign": worst_c["campaign_name"], "worst_campaign_roi": float(worst_c["roi"]),
        "worst_campaign_conv": float(worst_c["conversion_rate_pct"]),
        "worst_campaign_cpa": float(worst_c["cost_per_conversion"]),
        "best_campaign_type": best_type["campaign_type"], "best_campaign_type_roi": float(best_type["roi"]),
        "top_segment_conv": top_seg["segment"], "top_segment_conv_pct": float(top_seg["conversion_rate_pct"]),
        "top_activation": top_act["activation_name"], "top_activation_rate": float(top_act["engagement_rate_pct"]),
        "low_activation": low_act["activation_name"], "low_activation_rate": float(low_act["engagement_rate_pct"]),
        "top_sponsor": top_sp["sponsor_name"], "top_sponsor_engagements": int(top_sp["engagements"]),
        "weak_sponsors": weak, "insights": insights, "recommendations": recs,
    }
    (OUT / "key_numbers.json").write_text(json.dumps(key, indent=2), encoding="utf-8")

    seg_rows = "\n".join(
        f"| {x.segment} | {int(x.fans):,} | {money(x.total_revenue)} | {x.pct_of_revenue:.1f}% | ${x.avg_spend_per_fan:,.0f} | {x.avg_games:.1f} | {x.avg_engagement_score:.0f} |"
        for x in segval[segval["total_revenue"] > 0].itertuples())
    md = f"""# Executive Summary: Phoenix Suns Fan Revenue & Strategy Intelligence Hub

Independent demonstration project by Tejas Bhanushali. Not affiliated with or endorsed by the Phoenix Suns.
This project uses a simulated dataset designed to reflect realistic sports business scenarios and to demonstrate
an analytical approach. No number here describes actual Suns performance.

## Season snapshot (simulated, {int(kpi['home_games'])} home games)

| KPI | Value |
|---|---:|
| Ticket revenue | {money(kpi['ticket_revenue'])} |
| Revenue per game | {money(kpi['revenue_per_game'])} |
| Average ticket price | ${kpi['avg_ticket_price']:.2f} |
| Sell-through rate | {kpi['sell_through_pct']:.1f}% |
| Attendance rate (scanned / sold) | {kpi['attendance_rate_pct']:.1f}% |
| No-show rate | {kpi['no_show_pct']:.1f}% |
| Repeat purchase rate | {ret['repeat_purchase_rate_pct']:.1f}% |
| Fan retention rate (first half buyers who returned) | {ret['retention_rate_pct']:.1f}% |
| Campaign conversion rate | {kpi['campaign_conversion_pct']:.2f}% |
| Sponsor engagements | {int(kpi['sponsor_engagements']):,} |

## Key insights

""" + "\n".join(f"{i}. {t}" for i, t in enumerate(insights, 1)) + """

## Recommended actions

| # | Action | What to do | Sizing (scenario, not a forecast) |
|---|---|---|---|
""" + "\n".join(f"| {i} | {x['action']} | {x['detail']} | {x['sizing']} |" for i, x in enumerate(recs, 1)) + f"""

## Segment value

| Segment | Fans | Revenue | Share | Avg spend | Avg games | Engagement score |
|---|---:|---:|---:|---:|---:|---:|
{seg_rows}

## Method notes

- Segments use recency, frequency, and monetary scores plus rules documented in `docs/metric_definitions.md`.
- Campaign revenue uses last-touch attribution. It ranks campaigns and does not prove incremental lift.
- Sizing figures are scenarios built from observed averages and stated assumptions.
"""
    (OUT / "executive_summary.md").write_text(md, encoding="utf-8")
    write_video_script(key)
    print("  key numbers, executive summary, and video script written")


if __name__ == "__main__":
    print("Step 3: SQL analysis, charts, findings")
    main()
