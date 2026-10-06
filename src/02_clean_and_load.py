"""
Step 2: Clean and validate the raw data, write clean CSVs, load SQLite, and segment fans.

Outputs: data/clean/*.csv, data/suns_hub.db, outputs/data_quality_report.md
"""
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW, CLEAN, OUT = ROOT / "data" / "raw", ROOT / "data" / "clean", ROOT / "outputs"
DB = ROOT / "data" / "suns_hub.db"
CLEAN.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
CHANNELS = {"mobile app": "Mobile App", "web": "Website", "website": "Website"}
RECENCY_DAYS = 60
log, checks = [], []


def note(table, issue, rows, action):
    log.append((table, issue, int(rows), action))


def check(name, ok, detail=""):
    checks.append((name, "PASS" if ok else "FAIL", detail))


def quintile(series, ascending=True):
    return pd.qcut(series.rank(method="first", ascending=ascending), 5, labels=[1, 2, 3, 4, 5]).astype(int)


def segment_fans(con):
    f = pd.read_sql("SELECT * FROM v_fan_summary", con)
    season_end = pd.to_datetime(pd.read_sql("SELECT MAX(game_date) d FROM games", con)["d"].iloc[0])
    f["recency_days"] = (season_end - pd.to_datetime(f["last_game_date"])).dt.days
    buyers = f["games_purchased"] > 0
    f["attendance_rate"] = np.where(buyers, f["tickets_scanned"] / f["tickets_purchased"].replace(0, np.nan), np.nan)
    f["open_rate"] = np.where(f["messages_received"] > 0, f["messages_opened"] / f["messages_received"].replace(0, np.nan), 0.0)
    f["engagement_score"] = np.where(buyers, (100 * (0.6 * f["attendance_rate"].fillna(0) + 0.4 * f["open_rate"])).round(0), 0)
    for col in ("r_score", "f_score", "m_score"):
        f[col] = 0
    f.loc[buyers, "r_score"] = quintile(f.loc[buyers, "recency_days"], ascending=False)
    f.loc[buyers, "f_score"] = quintile(f.loc[buyers, "games_purchased"])
    f.loc[buyers, "m_score"] = quintile(f.loc[buyers, "total_spend"])
    f["rfm_score"] = f["r_score"] + f["f_score"] + f["m_score"]

    member = f["membership_status"] == "Season Ticket Member"
    p80 = f.loc[buyers & ~member, "total_spend"].quantile(0.80)
    lapsed = f["recency_days"] > RECENCY_DAYS
    high_value = buyers & ~member & (f["games_purchased"] >= 4) & (f["total_spend"] >= p80)
    f["segment"] = np.select(
        [member, ~buyers, (f["games_purchased"] >= 2) & lapsed, high_value, f["games_purchased"] >= 2,
         (f["games_purchased"] == 1) & ~lapsed],
        ["Season Ticket Member", "Prospect", "At-Risk Fan", "High-Value Fan", "Repeat Attendee", "First-Time Buyer"],
        default="Lapsed One-Time Buyer")
    f["plan_candidate"] = ((~member) & (f["games_purchased"] >= 5)).astype(int)

    halves = pd.read_sql("""
        WITH o AS (SELECT game_id, ROW_NUMBER() OVER (ORDER BY game_date) AS n, COUNT(*) OVER () AS total FROM games)
        SELECT t.fan_id,
               MAX(CASE WHEN o.n <= o.total / 2 THEN 1 ELSE 0 END) AS bought_first_half,
               MAX(CASE WHEN o.n >  o.total / 2 THEN 1 ELSE 0 END) AS bought_second_half
        FROM ticket_sales t JOIN o ON o.game_id = t.game_id
        WHERE t.ticket_type <> 'Season Ticket'
        GROUP BY t.fan_id""", con)
    f = f.merge(halves, on="fan_id", how="left")
    f[["bought_first_half", "bought_second_half"]] = f[["bought_first_half", "bought_second_half"]].fillna(0).astype(int)

    out = f[["fan_id", "segment", "plan_candidate", "games_purchased", "games_attended", "tickets_purchased",
             "tickets_scanned", "attendance_rate", "total_spend", "recency_days", "r_score", "f_score", "m_score",
             "rfm_score", "messages_received", "messages_opened", "campaign_conversions", "engagement_score",
             "bought_first_half", "bought_second_half"]].copy()
    out["attendance_rate"] = out["attendance_rate"].round(4)
    out["recency_days"] = out["recency_days"].astype("Int64")
    out["engagement_score"] = out["engagement_score"].astype(int)
    out.to_csv(CLEAN / "fan_segments.csv", index=False)
    con.execute("DROP TABLE IF EXISTS fan_segments")
    out.to_sql("fan_segments", con, index=False)
    con.execute("CREATE UNIQUE INDEX ix_seg ON fan_segments(fan_id)")
    return out


def main():
    t = {n: pd.read_csv(RAW / f"{n}.csv") for n in ["fans", "games", "ticket_sales", "attendance", "campaigns",
                                                     "campaign_responses", "sponsorship"]}
    raw_rows = {n: len(d) for n, d in t.items()}

    fans = t["fans"]
    n = len(fans)
    fans = fans.drop_duplicates("fan_id")
    note("fans", "Duplicate fan_id rows", n - len(fans), "Kept first occurrence")
    fixed = fans["city"].str.strip().str.title().str.replace("Of", "of")
    note("fans", "City labels in inconsistent case", (fixed != fans["city"]).sum(), "Standardized to title case")
    fans = fans.assign(city=fixed)

    games = t["games"]
    games["day_type"] = np.where(games["weekday"].isin(["Friday", "Saturday", "Sunday"]), "Weekend", "Weekday")
    games = games[["game_id", "opponent", "game_date", "weekday", "day_type", "game_type", "home_away",
                   "opponent_tier", "capacity"]]

    sales = t["ticket_sales"]
    n = len(sales)
    sales = sales.drop_duplicates("transaction_id")
    note("ticket_sales", "Duplicate transaction_id rows", n - len(sales), "Kept first occurrence")
    bad = sales["quantity"] <= 0
    note("ticket_sales", "Zero or negative quantity", bad.sum(), "Removed as invalid records")
    sales = sales[~bad].copy()
    norm = sales["purchase_channel"].str.strip().str.replace(r"\s+", " ", regex=True)
    fixed = norm.str.lower().map(CHANNELS).fillna(norm)
    note("ticket_sales", "Inconsistent purchase_channel labels", (fixed != sales["purchase_channel"]).sum(),
         "Mapped to standard labels")
    sales["purchase_channel"] = fixed
    missing = sales["ticket_revenue"].isna()
    unit = sales["ticket_revenue"] / sales["quantity"]
    med = unit.groupby([sales["game_id"], sales["seat_section"], sales["ticket_type"]]).transform("median")
    med = med.fillna(unit.groupby(sales["seat_section"]).transform("median"))
    sales.loc[missing, "ticket_revenue"] = (med[missing] * sales.loc[missing, "quantity"]).round(2)
    note("ticket_sales", "Missing ticket_revenue", missing.sum(),
         "Imputed from median unit price for same game, section, and ticket type")
    sales = sales.sort_values("transaction_id").reset_index(drop=True)

    att = t["attendance"]
    orphan = ~att["transaction_id"].isin(sales["transaction_id"])
    note("attendance", "Attendance row with no matching sale", orphan.sum(), "Removed")
    att = att[~orphan].reset_index(drop=True)

    clean = {"fans": fans, "games": games, "campaigns": t["campaigns"], "ticket_sales": sales, "attendance": att,
             "campaign_responses": t["campaign_responses"], "sponsorship": t["sponsorship"]}
    pk = {"fans": "fan_id", "games": "game_id", "campaigns": "campaign_id", "ticket_sales": "transaction_id",
          "attendance": "attendance_id", "campaign_responses": "response_id", "sponsorship": "sponsorship_id"}
    for name, col in pk.items():
        check(f"Primary key unique: {name}.{col}", clean[name][col].is_unique)
    check("Every sale has a known fan and game",
          sales["fan_id"].isin(fans["fan_id"]).all() and sales["game_id"].isin(games["game_id"]).all())
    check("Every attendance row has a sale", att["transaction_id"].isin(sales["transaction_id"]).all())
    check("One attendance row per sale", len(att) == len(sales))
    sold = sales.groupby("game_id")["quantity"].sum()
    cap = games.set_index("game_id")["capacity"]
    check("Tickets sold never exceed capacity", (sold <= cap.reindex(sold.index)).all(),
          f"max sell-through {(sold / cap.reindex(sold.index)).max():.1%}")
    scanned = att.groupby("game_id")["tickets_scanned"].sum()
    check("Tickets scanned never exceed tickets sold", (scanned <= sold.reindex(scanned.index)).all())
    check("No missing or non positive revenue", bool((sales["ticket_revenue"] > 0).all()))
    check("Campaign conversions match response rows",
          (t["campaign_responses"].groupby("campaign_id")["converted"].sum()
           == t["campaigns"].set_index("campaign_id")["conversions"]).all())
    check("Campaign revenue matches tagged sales",
          abs(sales.dropna(subset=["campaign_id"])["ticket_revenue"].sum() - t["campaigns"]["revenue_generated"].sum())
          / t["campaigns"]["revenue_generated"].sum() < 0.01)

    for name, df in clean.items():
        df.to_csv(CLEAN / f"{name}.csv", index=False)
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript((ROOT / "sql" / "00_schema.sql").read_text(encoding="utf-8"))
    for name in ["fans", "games", "campaigns", "ticket_sales", "attendance", "campaign_responses", "sponsorship"]:
        clean[name].to_sql(name, con, if_exists="append", index=False, chunksize=50000)
    seg = segment_fans(con)
    con.commit()
    con.close()
    check("One segment per fan", len(seg) == len(fans) and seg["fan_id"].is_unique)

    lines = ["# Data Quality Report", "", "All data in this project is simulated. Raw files are never modified.", "",
             "## Row counts", "", "| Table | Raw rows | Clean rows |", "|---|---:|---:|"]
    lines += [f"| {n} | {raw_rows[n]:,} | {len(d):,} |" for n, d in clean.items()]
    lines += ["", "## Issues found and actions taken", "", "| Table | Issue | Rows | Action |", "|---|---|---:|---|"]
    lines += [f"| {a} | {b} | {c:,} | {d} |" for a, b, c, d in log]
    lines += ["", "## Validation checks", "", "| Check | Result | Detail |", "|---|---|---|"]
    lines += [f"| {a} | {b} | {c} |" for a, b, c in checks]
    (OUT / "data_quality_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    failed = [c for c in checks if c[1] == "FAIL"]
    print(f"  cleaning rules applied: {len(log)}")
    print(f"  validation checks: {len(checks) - len(failed)} passed, {len(failed)} failed")
    for s, grp in seg.groupby("segment"):
        print(f"  {s:<24}{len(grp):>8,} fans   ${grp['total_spend'].sum():>13,.0f}")
    if failed:
        raise SystemExit("Validation failed: " + "; ".join(c[0] for c in failed))


if __name__ == "__main__":
    print("Step 2: cleaning, validating, loading SQLite, segmenting fans")
    main()
