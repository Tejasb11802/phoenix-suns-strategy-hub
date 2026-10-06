"""
Step 1: Generate the simulated dataset for the Phoenix Suns Fan Revenue & Strategy Intelligence Hub.

Everything in this project is SIMULATED. It is a demonstration dataset designed to reflect realistic
sports business scenarios. It is not Phoenix Suns data, and the schedule is illustrative
(real NBA opponents, simulated dates), not the team's actual schedule.

Tables written to data/raw:
  fans, games, ticket_sales, attendance, campaigns, campaign_responses, sponsorship

A few data quality problems are injected on purpose so Step 2 has real cleaning work to do.
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 2026
rng = np.random.default_rng(SEED)
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

N_GAMES = 41
CAPACITY = 17000
N_MEMBERS = 2900          # season ticket member accounts
N_POOL = 70000            # everyone else in the fan database
SECTIONS = ["Courtside & Premium", "Lower Level", "Club Level", "Upper Level"]
SECTION_CAP = {"Courtside & Premium": 900, "Lower Level": 6100, "Club Level": 2200, "Upper Level": 7800}
SECTION_PRICE = {"Courtside & Premium": 395.0, "Lower Level": 138.0, "Club Level": 176.0, "Upper Level": 44.0}

OPPONENTS = {
    "Marquee": ["Los Angeles Lakers", "Golden State Warriors", "Boston Celtics", "New York Knicks",
                "Oklahoma City Thunder", "San Antonio Spurs", "Denver Nuggets"],
    "Standard": ["LA Clippers", "Minnesota Timberwolves", "Houston Rockets", "Dallas Mavericks",
                 "Cleveland Cavaliers", "Milwaukee Bucks", "Miami Heat", "Philadelphia 76ers", "Orlando Magic",
                 "Atlanta Hawks", "Detroit Pistons", "Indiana Pacers", "Memphis Grizzlies", "Sacramento Kings"],
    "Value": ["Utah Jazz", "Portland Trail Blazers", "New Orleans Pelicans", "Charlotte Hornets",
              "Washington Wizards", "Brooklyn Nets", "Toronto Raptors", "Chicago Bulls"],
}
WEST_TWICE = ["Los Angeles Lakers", "Golden State Warriors", "LA Clippers", "Sacramento Kings", "Denver Nuggets",
              "Minnesota Timberwolves", "Oklahoma City Thunder", "Utah Jazz", "Dallas Mavericks", "Houston Rockets",
              "Memphis Grizzlies", "San Antonio Spurs"]
TIER_OF = {team: tier for tier, teams in OPPONENTS.items() for team in teams}
TIER_DEMAND = {"Marquee": 1.24, "Standard": 1.00, "Value": 0.80}
TIER_PRICE = {"Marquee": 1.45, "Standard": 1.00, "Value": 0.80}
DOW_DEMAND = {0: 0.86, 1: 0.86, 2: 0.90, 3: 0.92, 4: 1.10, 5: 1.16, 6: 1.03}
THEMES = ["Opening Night", "Fan Appreciation Night", "City Edition Night", "Family Night", "College Night",
          "Military Appreciation Night", "Throwback Night", "Kids Day"]
CITIES = ["Phoenix", "Scottsdale", "Tempe", "Mesa", "Chandler", "Glendale", "Gilbert", "Peoria", "Tucson",
          "Out of State"]
CITY_P = [0.31, 0.12, 0.09, 0.10, 0.08, 0.07, 0.07, 0.05, 0.04, 0.07]


def build_games():
    teams = [t for t in TIER_OF]
    opponents = np.array(WEST_TWICE + teams)           # 12 conference opponents twice, everyone once = 41
    assert len(opponents) == N_GAMES
    rng.shuffle(opponents)
    start = pd.Timestamp("2025-10-23")
    offsets = np.round(np.linspace(0, 170, N_GAMES) + rng.uniform(-1, 1, N_GAMES)).astype(int)
    g = pd.DataFrame({"game_id": [f"G{i:02d}" for i in range(1, N_GAMES + 1)],
                      "opponent": opponents,
                      "game_date": [start + pd.Timedelta(days=int(o)) for o in np.clip(offsets, 0, 170)]})
    g["game_date"] = pd.to_datetime(g["game_date"])
    g["weekday"] = g["game_date"].dt.day_name()
    g["dow"] = g["game_date"].dt.dayofweek
    g["opponent_tier"] = g["opponent"].map(TIER_OF)
    g["game_type"] = "Regular Season"
    w = np.where(g["opponent_tier"] == "Value", 3.0, np.where(g["opponent_tier"] == "Standard", 1.5, 0.5))
    w[[0, N_GAMES - 1]] = 0
    idx = rng.choice(N_GAMES, size=len(THEMES) - 2, replace=False, p=w / w.sum())
    g.loc[0, "game_type"] = THEMES[0]
    g.loc[N_GAMES - 1, "game_type"] = THEMES[1]
    for i, name in zip(sorted(idx), THEMES[2:]):
        g.loc[i, "game_type"] = name
    g["home_away"] = "Home"
    g["capacity"] = CAPACITY
    theme = np.where(g["game_type"] != "Regular Season", 1.08, 1.0)
    g["demand_index"] = (g["opponent_tier"].map(TIER_DEMAND) * g["dow"].map(DOW_DEMAND) * theme
                         * rng.normal(1.0, 0.04, N_GAMES))
    return g


def build_fans():
    n = N_MEMBERS + N_POOL
    member = np.arange(n) < N_MEMBERS
    age = np.clip(np.round(np.where(member, rng.normal(45, 12, n), rng.normal(35, 13, n))), 18, 80)
    age_group = pd.cut(age, [0, 24, 34, 44, 54, 64, 200], labels=["18-24", "25-34", "35-44", "45-54", "55-64", "65+"])
    fans = pd.DataFrame({
        "fan_id": [f"F{i:06d}" for i in range(1, n + 1)],
        "age_group": age_group.astype(str),
        "city": rng.choice(CITIES, n, p=CITY_P),
        "acquisition_channel": rng.choice(["Organic", "Paid Social", "Referral", "Partner Offer", "Box Office",
                                           "Email Signup"], n, p=[0.28, 0.20, 0.14, 0.10, 0.08, 0.20]),
        "membership_status": np.where(member, "Season Ticket Member", "Non-Member"),
    })
    return fans


def build_sales(games, fans):
    fan_ids = fans["fan_id"].to_numpy()
    blocks = []
    seats = rng.choice([2, 3, 4, 6], N_MEMBERS, p=[0.58, 0.12, 0.25, 0.05])
    section = rng.choice(SECTIONS, N_MEMBERS, p=[0.06, 0.44, 0.16, 0.34])
    member_price = np.array([SECTION_PRICE[s] for s in section]) * 0.80
    member_buy = pd.Timestamp("2025-06-20") + pd.to_timedelta(rng.integers(0, 100, N_MEMBERS), unit="D")
    for gi in range(N_GAMES):
        blocks.append(pd.DataFrame({"fan_idx": np.arange(N_MEMBERS), "game_idx": gi, "purchase_date": member_buy,
                                    "ticket_type": "Season Ticket", "seat_section": section, "quantity": seats,
                                    "unit_price": member_price, "purchase_channel": "Account Manager"}))
    held = {s: int(seats[section == s].sum()) for s in SECTIONS}

    weight = rng.lognormal(0.0, 1.25, N_POOL)
    kind = rng.choice(3, N_POOL, p=[0.38, 0.37, 0.25])          # steady, lapsing, late joiner
    g0, g1 = rng.integers(4, 30, N_POOL), rng.integers(8, 34, N_POOL)
    idx = np.arange(N_GAMES)[None, :]
    active = np.ones((N_POOL, N_GAMES))
    active = np.where((kind[:, None] == 1) & (idx > g0[:, None]), 0.05, active)
    active = np.where((kind[:, None] == 2) & (idx < g1[:, None]), 0.03, active)
    pref = rng.choice(SECTIONS, N_POOL, p=[0.04, 0.27, 0.09, 0.60])
    pools = {s: np.where(pref == s)[0] for s in SECTIONS}
    on_sale = pd.Timestamp("2025-09-15")

    for gi, g in enumerate(games.itertuples(index=False)):
        weekend = g.dow in (4, 5, 6)
        for s in SECTIONS:
            open_seats = SECTION_CAP[s] - held[s]
            fill = float(np.clip(0.74 * g.demand_index * rng.normal(1, 0.025), 0.30, 1.0))
            target = int(open_seats * fill)
            qty = rng.choice([1, 2, 3, 4, 5, 6], int(target / 2.0) + 60, p=[0.15, 0.50, 0.10, 0.19, 0.03, 0.03])
            group = np.zeros(len(qty), dtype=bool)
            if s in ("Lower Level", "Upper Level"):
                group = rng.random(len(qty)) < 0.004
                qty[group] = rng.integers(10, 36, int(group.sum()))
            k = int(np.searchsorted(np.cumsum(qty), target, side="right"))
            qty, group = qty[:k], group[:k]
            p = weight[pools[s]] * active[pools[s], gi]
            chosen = rng.choice(pools[s], size=k, replace=False, p=p / p.sum())
            lead = np.clip(rng.gamma(1.3, 9.0, k), 0, 75).astype(int)
            pdate = pd.Series(pd.Timestamp(g.game_date) - pd.to_timedelta(lead, unit="D"))
            pdate = pdate.where(pdate >= on_sale, on_sale)
            price = SECTION_PRICE[s] * TIER_PRICE[g.opponent_tier] * (1.08 if weekend else 0.96) * rng.lognormal(0, 0.08, k)
            price = np.where(group, price * 0.85, price)
            channel = rng.choice(["Mobile App", "Website", "Box Office", "Phone Sales"], k, p=[0.50, 0.36, 0.06, 0.08])
            blocks.append(pd.DataFrame({"fan_idx": chosen + N_MEMBERS, "game_idx": gi, "purchase_date": pdate.to_numpy(),
                                        "ticket_type": np.where(group, "Group", "Single Game"), "seat_section": s,
                                        "quantity": qty, "unit_price": price,
                                        "purchase_channel": np.where(group, "Group Sales", channel)}))

    tx = pd.concat(blocks, ignore_index=True)
    tx["purchase_date"] = pd.to_datetime(tx["purchase_date"])
    tx = tx.sort_values(["purchase_date", "game_idx", "fan_idx"], kind="stable").reset_index(drop=True)
    tx.insert(0, "transaction_id", [f"T{i:07d}" for i in range(1, len(tx) + 1)])
    tx["fan_id"] = fan_ids[tx["fan_idx"].to_numpy()]
    tx["game_id"] = games["game_id"].to_numpy()[tx["game_idx"].to_numpy()]
    tx["ticket_revenue"] = (tx["quantity"] * tx["unit_price"]).round(2)
    return tx


def build_attendance(tx, games):
    n = len(tx)
    gi = tx["game_idx"].to_numpy()
    member = (tx["ticket_type"] == "Season Ticket").to_numpy()
    usage = rng.beta(7, 1.7, N_MEMBERS)
    opp = games["opponent_tier"].map({"Marquee": 0.07, "Standard": 0.0, "Value": -0.09}).to_numpy()
    dow = np.where(games["dow"].isin([4, 5, 6]), 0.02, -0.05)
    p = np.full(n, 0.95)
    p[(tx["ticket_type"] == "Group").to_numpy()] = 0.92
    p[member] = np.clip(usage[tx["fan_idx"].to_numpy()[member]] + opp[gi[member]] + dow[gi[member]], 0.10, 0.99)
    came = rng.random(n) < p
    qty = tx["quantity"].to_numpy()
    scanned = np.where(came, qty, 0)
    scanned = np.where(came & (qty > 1) & (rng.random(n) < 0.06), scanned - 1, scanned)
    att = pd.DataFrame({"attendance_id": [f"A{i:07d}" for i in range(1, n + 1)],
                        "transaction_id": tx["transaction_id"].to_numpy(), "fan_id": tx["fan_id"].to_numpy(),
                        "game_id": tx["game_id"].to_numpy(), "tickets_scanned": scanned,
                        "scanned_flag": (scanned > 0).astype(int)})
    return att


CAMPAIGNS = [
    # id, name, type, channel, target segment, start, end, audience, cost, conversion, open, click given open
    ("C01", "Opening Night Launch", "Acquisition", "Email", "Prospects", "2025-10-01", "2025-10-22", 14000, 8500, 0.034, 0.33, 0.20),
    ("C02", "New Fan Social Offer", "Acquisition", "Paid Social", "Prospects", "2025-11-03", "2025-11-23", 18000, 40000, 0.011, 0.11, 0.24),
    ("C03", "Holiday Family Pack", "Promotion", "Email", "Past Buyers", "2025-12-01", "2025-12-21", 12000, 13000, 0.058, 0.38, 0.24),
    ("C04", "Weeknight Value Bundle", "Promotion", "SMS", "Past Buyers", "2026-01-05", "2026-01-26", 8000, 15000, 0.078, 0.83, 0.16),
    ("C05", "We Miss You Email", "Win-Back", "Email", "Lapsed Buyers", "2026-01-14", "2026-02-09", 8500, 9000, 0.030, 0.23, 0.17),
    ("C06", "Mini Plan Invitation", "Upsell", "Email", "Frequent Buyers", "2026-01-20", "2026-02-15", 2800, 7000, 0.115, 0.53, 0.30),
    ("C07", "College Night Social", "Acquisition", "Paid Social", "Prospects", "2026-02-02", "2026-02-21", 14000, 28000, 0.010, 0.10, 0.22),
    ("C08", "Second Game Offer", "Retention", "Email", "Past Buyers", "2026-02-16", "2026-03-08", 10000, 11000, 0.052, 0.37, 0.22),
    ("C09", "App Flash Sale", "Promotion", "Push", "Past Buyers", "2026-03-01", "2026-03-10", 13000, 6000, 0.042, 0.47, 0.14),
    ("C10", "Come Back SMS", "Win-Back", "SMS", "Lapsed Buyers", "2026-03-05", "2026-03-25", 4500, 10000, 0.046, 0.81, 0.12),
    ("C11", "Fan Appreciation Finale", "Retention", "Email", "Past Buyers", "2026-03-22", "2026-04-11", 15000, 14000, 0.054, 0.36, 0.23),
    ("C12", "Search Retargeting", "Acquisition", "Paid Search", "Prospects", "2026-03-01", "2026-03-31", 9000, 20000, 0.021, 0.15, 0.30),
]


def build_campaigns(tx, fans):
    single = tx[tx["ticket_type"] == "Single Game"]
    pool_ids = pd.Index(fans.loc[fans["membership_status"] == "Non-Member", "fan_id"])
    tagged, tag_ids, tag_campaign, resp, rows = set(), [], [], [], []
    for cid, name, ctype, channel, target, start, end, audience, cost, conv_rate, open_rate, click_rate in CAMPAIGNS:
        start, end = pd.Timestamp(start), pd.Timestamp(end)
        before = single[single["purchase_date"] < start]
        count = before.groupby("fan_id").size()
        last = before.groupby("fan_id")["purchase_date"].max()
        if target == "Prospects":
            eligible = pool_ids.difference(count.index)
        elif target == "Past Buyers":
            eligible = pd.Index(count.index)
        elif target == "Lapsed Buyers":
            eligible = pd.Index(last[last < start - pd.Timedelta(days=45)].index)
        else:
            eligible = pd.Index(count[count >= 3].index)
        eligible = eligible.sort_values()
        window = single[(single["purchase_date"] >= start) & (single["purchase_date"] <= end)]
        free = window[~window["transaction_id"].isin(tagged)]
        first = free.sort_values(["purchase_date", "transaction_id"]).drop_duplicates("fan_id").set_index("fan_id")
        buyers = eligible.intersection(first.index).sort_values()
        n_conv = min(len(buyers), int(audience * conv_rate))
        conv = rng.choice(buyers.to_numpy(), n_conv, replace=False)
        others = eligible.difference(pd.Index(window["fan_id"].unique())).sort_values()
        n_non = min(len(others), audience - n_conv)
        non = rng.choice(others.to_numpy(), n_non, replace=False)
        conv_tx = first.loc[conv, "transaction_id"].to_numpy()
        tagged.update(conv_tx.tolist())
        tag_ids.extend(conv_tx.tolist())
        tag_campaign.extend([cid] * n_conv)
        opened = (rng.random(n_non) < open_rate).astype(int)
        clicked = ((rng.random(n_non) < click_rate) & (opened == 1)).astype(int)
        resp.append(pd.DataFrame({"campaign_id": cid, "fan_id": np.concatenate([conv, non]),
                                  "opened": np.concatenate([np.ones(n_conv, dtype=int), opened]),
                                  "clicked": np.concatenate([np.ones(n_conv, dtype=int), clicked]),
                                  "converted": np.concatenate([np.ones(n_conv, dtype=int), np.zeros(n_non, dtype=int)])}))
        rows.append((cid, name, ctype, channel, target, start.strftime("%Y-%m-%d"), cost))
    responses = pd.concat(resp, ignore_index=True)
    responses.insert(0, "response_id", [f"R{i:07d}" for i in range(1, len(responses) + 1)])
    tx = tx.copy()
    tx["campaign_id"] = tx["transaction_id"].map(dict(zip(tag_ids, tag_campaign)))
    campaigns = pd.DataFrame(rows, columns=["campaign_id", "campaign_name", "campaign_type", "channel",
                                            "target_segment", "send_date", "cost"])
    agg = responses.groupby("campaign_id").agg(impressions=("fan_id", "count"), clicks=("clicked", "sum"),
                                               conversions=("converted", "sum"))
    revenue = tx.dropna(subset=["campaign_id"]).groupby("campaign_id")["ticket_revenue"].sum().round(2)
    campaigns = campaigns.join(agg, on="campaign_id").join(revenue.rename("revenue_generated"), on="campaign_id")
    campaigns["revenue_generated"] = campaigns["revenue_generated"].fillna(0)
    return campaigns, responses, tx


SPONSORS = [
    # id, name, quality, activations
    ("S01", "Copper State Bank", 1.10, ["Courtside LED Signage", "Halftime Contest", "Social Content Series"]),
    ("S02", "Saguaro Auto Group", 0.65, ["Courtside LED Signage", "Concourse Display"]),
    ("S03", "Sonoran Health", 1.00, ["Courtside LED Signage", "Halftime Contest", "Mobile App Banner"]),
    ("S04", "Valley Sun Energy", 0.90, ["Courtside LED Signage", "Concourse Display"]),
    ("S05", "Cactus Cola", 1.30, ["Courtside LED Signage", "Fan Zone Sampling", "Social Content Series"]),
    ("S06", "Mesa Mobile", 1.20, ["Social Content Series", "Mobile App Banner", "Fan Zone Sampling"]),
    ("S07", "Red Rock Insurance", 0.80, ["Courtside LED Signage", "Social Content Series"]),
    ("S08", "Camelback Air", 1.25, ["Social Content Series", "Halftime Contest"]),
]
ACT_RATE = {"Courtside LED Signage": 0.0004, "Halftime Contest": 0.070, "Social Content Series": 0.033,
            "Mobile App Banner": 0.012, "Concourse Display": 0.007, "Fan Zone Sampling": 0.090}
ACT_CPM = {"Courtside LED Signage": 12.0, "Halftime Contest": 38.0, "Social Content Series": 9.0,
           "Mobile App Banner": 7.0, "Concourse Display": 6.0, "Fan Zone Sampling": 45.0}
ENGAGEMENT_VALUE = 0.35      # estimated dollar value of one fan engagement


def build_sponsorship(games, scanned_by_game):
    rows = []
    for sid, name, quality, activations in SPONSORS:
        for act in activations:
            for gi, g in enumerate(games.itertuples(index=False)):
                att = scanned_by_game[gi]
                base = {"Courtside LED Signage": att * 8 + 1_400_000 * TIER_DEMAND[g.opponent_tier],
                        "Halftime Contest": att * 0.45, "Social Content Series": 850_000 * g.demand_index,
                        "Mobile App Banner": 140_000 * g.demand_index, "Concourse Display": att * 0.8,
                        "Fan Zone Sampling": att * 0.22}[act]
                impressions = max(base * rng.normal(1, 0.08), 0)
                engagements = max(impressions * ACT_RATE[act] * quality * rng.normal(1, 0.12), 0)
                value = impressions / 1000 * ACT_CPM[act] + engagements * ENGAGEMENT_VALUE
                rows.append((sid, name, act, g.game_id, int(impressions), int(engagements), round(value, 2)))
    sp = pd.DataFrame(rows, columns=["sponsor_id", "sponsor_name", "activation_name", "game_id", "impressions",
                                     "engagements", "estimated_value"])
    sp.insert(0, "sponsorship_id", [f"SP{i:05d}" for i in range(1, len(sp) + 1)])
    return sp


def main():
    games = build_games()
    fans = build_fans()
    tx = build_sales(games, fans)
    att = build_attendance(tx, games)
    campaigns, responses, tx = build_campaigns(tx, fans)

    first_buy = tx.groupby("fan_id")["purchase_date"].min()
    n = len(fans)
    fallback = pd.Series(pd.Timestamp("2024-10-01") + pd.to_timedelta(rng.integers(0, 340, n), unit="D"))
    anchor = pd.concat([fans["fan_id"].map(first_buy), fallback], axis=1).min(axis=1)
    back = np.where(fans["membership_status"] == "Season Ticket Member", rng.integers(30, 2400, n),
                    rng.exponential(70, n).astype(int))
    fans["join_date"] = (anchor - pd.to_timedelta(back, unit="D")).dt.strftime("%Y-%m-%d")

    scanned = att.groupby(tx["game_idx"].to_numpy())["tickets_scanned"].sum().reindex(range(N_GAMES)).to_numpy()
    sponsorship = build_sponsorship(games, scanned)

    sales = tx[["transaction_id", "fan_id", "game_id", "ticket_type", "seat_section", "quantity", "ticket_revenue",
                "purchase_date", "purchase_channel", "campaign_id"]].copy()
    sales["purchase_date"] = sales["purchase_date"].dt.strftime("%Y-%m-%d")
    games_out = games[["game_id", "opponent", "game_date", "weekday", "game_type", "home_away", "opponent_tier",
                       "capacity"]].copy()
    games_out["game_date"] = games_out["game_date"].dt.strftime("%Y-%m-%d")

    # ---- injected data quality problems ----
    i = rng.choice(len(sales), int(len(sales) * 0.0015), replace=False)
    sales.loc[i, "ticket_revenue"] = np.nan
    for base, alts in {"Mobile App": ["mobile app", "MOBILE APP", "Mobile  App"], "Website": ["WEB", "website "]}.items():
        pos = np.where(sales["purchase_channel"].to_numpy() == base)[0]
        pick = rng.choice(pos, int(len(pos) * 0.03), replace=False)
        sales.loc[pick, "purchase_channel"] = rng.choice(alts, len(pick))
    bad = sales.sample(int(len(sales) * 0.0005), random_state=SEED).copy()
    bad["transaction_id"] = [f"TX{i:06d}" for i in range(1, len(bad) + 1)]
    bad["quantity"] = -bad["quantity"]
    sales = pd.concat([sales, sales.sample(int(len(sales) * 0.004), random_state=SEED + 1), bad], ignore_index=True)
    sales = sales.sample(frac=1.0, random_state=SEED).reset_index(drop=True)
    i = rng.choice(len(fans), int(len(fans) * 0.02), replace=False)
    fans.loc[i, "city"] = fans.loc[i, "city"].str.upper()
    fans_out = pd.concat([fans, fans.sample(int(len(fans) * 0.002), random_state=SEED)], ignore_index=True)
    orphan = att.sample(int(len(att) * 0.002), random_state=SEED).copy()
    orphan["attendance_id"] = [f"AX{i:06d}" for i in range(1, len(orphan) + 1)]
    orphan["transaction_id"] = [f"T9{i:06d}" for i in range(1, len(orphan) + 1)]
    att_out = pd.concat([att, orphan], ignore_index=True)

    out = {"fans": fans_out[["fan_id", "age_group", "city", "acquisition_channel", "membership_status", "join_date"]],
           "games": games_out, "ticket_sales": sales, "attendance": att_out, "campaigns": campaigns,
           "campaign_responses": responses, "sponsorship": sponsorship}
    for name, df in out.items():
        df.to_csv(RAW / f"{name}.csv", index=False)
        print(f"  raw/{name}.csv  {len(df):>9,} rows")


if __name__ == "__main__":
    print("Step 1: generating simulated data")
    main()
