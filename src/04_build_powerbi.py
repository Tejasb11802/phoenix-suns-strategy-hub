"""
Step 4: Build the Power BI dashboard as a Power BI Project (PBIP).

Writes powerbi/Phoenix_Suns_Strategy_Hub.pbip plus its .SemanticModel and .Report folders:
  - semantic model in TMDL: 8 tables loaded from data/clean, relationships, all DAX measures
  - report in PBIR format: 6 pages (Executive Summary, Ticketing & Attendance, Fan Segmentation,
    Marketing & Campaign Performance, Sponsorship & Partner Insights, Recommendations)

Open the .pbip file in Power BI Desktop, click Refresh, apply powerbi/theme.json, then save as .pbix.
The absolute path of data/clean on this computer is written into the model's DataFolder parameter,
so run this script on the computer where you will open the report.

Usage:
    python src/04_build_powerbi.py            builds the project if it does not exist yet
    python src/04_build_powerbi.py --force    rebuilds it and overwrites any edits you saved
"""
import json
import shutil
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
PBI = ROOT / "powerbi"
NAME = "Phoenix_Suns_Strategy_Hub"
MODEL_DIR = PBI / f"{NAME}.SemanticModel"
REPORT_DIR = PBI / f"{NAME}.Report"
BASE_THEME = PBI / "assets" / "CY24SU10.json"

SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"
M = "_Measures"


def guid():
    return str(uuid.uuid4())


def hexid():
    return uuid.uuid4().hex[:20]


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, obj):
    write(path, json.dumps(obj, indent=2))


# =============================================================================
# Semantic model
# =============================================================================
T, I, D, DT = "string", "int64", "double", "date"

TABLES = {
    "fans": [("fan_id", T), ("age_group", T), ("city", T), ("acquisition_channel", T), ("membership_status", T),
             ("join_date", DT)],
    "games": [("game_id", T), ("opponent", T), ("game_date", DT), ("weekday", T), ("day_type", T), ("game_type", T),
              ("home_away", T), ("opponent_tier", T), ("capacity", I)],
    "campaigns": [("campaign_id", T), ("campaign_name", T), ("campaign_type", T), ("channel", T),
                  ("target_segment", T), ("send_date", DT), ("cost", D), ("impressions", I), ("clicks", I),
                  ("conversions", I), ("revenue_generated", D)],
    "ticket_sales": [("transaction_id", T), ("fan_id", T), ("game_id", T), ("ticket_type", T), ("seat_section", T),
                     ("quantity", I), ("ticket_revenue", D), ("purchase_date", DT), ("purchase_channel", T),
                     ("campaign_id", T)],
    "attendance": [("attendance_id", T), ("transaction_id", T), ("fan_id", T), ("game_id", T),
                   ("tickets_scanned", I), ("scanned_flag", I)],
    "campaign_responses": [("response_id", T), ("campaign_id", T), ("fan_id", T), ("opened", I), ("clicked", I),
                           ("converted", I)],
    "sponsorship": [("sponsorship_id", T), ("sponsor_id", T), ("sponsor_name", T), ("activation_name", T),
                    ("game_id", T), ("impressions", I), ("engagements", I), ("estimated_value", D)],
    "fan_segments": [("fan_id", T), ("segment", T), ("plan_candidate", I), ("games_purchased", I),
                     ("games_attended", I), ("tickets_purchased", I), ("tickets_scanned", I), ("attendance_rate", D),
                     ("total_spend", D), ("recency_days", I), ("r_score", I), ("f_score", I), ("m_score", I),
                     ("rfm_score", I), ("messages_received", I), ("messages_opened", I), ("campaign_conversions", I),
                     ("engagement_score", I), ("bought_first_half", I), ("bought_second_half", I)],
}

# Text columns where an empty CSV cell must become a true blank
NULL_IF_EMPTY = {"ticket_sales": ["campaign_id"]}

# DAX calculated columns: table -> [(name, expression, sort_by_column or None)]
CALC_COLUMNS = {
    "games": [
        ("Game Label", 'FORMAT ( games[game_date], "MMM DD" ) & " " & games[opponent]', "game_date"),
        ("Month", 'FORMAT ( games[game_date], "MMM YYYY" )', "Month Sort"),
        ("Month Sort", "YEAR ( games[game_date] ) * 100 + MONTH ( games[game_date] )", None),
        ("Day Sort", "WEEKDAY ( games[game_date], 2 )", None),
    ],
}
SORT_BY = {("games", "weekday"): "Day Sort"}

# (many side, one side)
RELATIONSHIPS = [
    ("ticket_sales.fan_id", "fans.fan_id"),
    ("attendance.fan_id", "fans.fan_id"),
    ("campaign_responses.fan_id", "fans.fan_id"),
    ("ticket_sales.game_id", "games.game_id"),
    ("attendance.game_id", "games.game_id"),
    ("sponsorship.game_id", "games.game_id"),
    ("campaign_responses.campaign_id", "campaigns.campaign_id"),
    ("ticket_sales.campaign_id", "campaigns.campaign_id"),
]

CUR0, CUR2, NUM, PCT, PCT2, MULT = "$#,##0", "$#,##0.00", "#,##0", "0.0%", "0.00%", '0.0"x"'

# (section, name, DAX expression on one line, format string or None)
MEASURES = [
    ("Ticketing & Attendance", "Ticket Revenue", "SUM ( ticket_sales[ticket_revenue] )", CUR0),
    ("Ticketing & Attendance", "Tickets Sold", "SUM ( ticket_sales[quantity] )", NUM),
    ("Ticketing & Attendance", "Avg Ticket Price", "DIVIDE ( [Ticket Revenue], [Tickets Sold] )", CUR2),
    ("Ticketing & Attendance", "Capacity", "SUM ( games[capacity] )", NUM),
    ("Ticketing & Attendance", "Sell-Through %", "DIVIDE ( [Tickets Sold], [Capacity] )", PCT),
    ("Ticketing & Attendance", "Unsold Seats", "[Capacity] - [Tickets Sold]", NUM),
    ("Ticketing & Attendance", "Tickets Scanned", "SUM ( attendance[tickets_scanned] )", NUM),
    ("Ticketing & Attendance", "Attendance Rate %", "DIVIDE ( [Tickets Scanned], [Tickets Sold] )", PCT),
    ("Ticketing & Attendance", "No-Show Rate %", "1 - [Attendance Rate %]", PCT),
    ("Ticketing & Attendance", "No-Show Tickets", "[Tickets Sold] - [Tickets Scanned]", NUM),
    ("Ticketing & Attendance", "Games Played", "COUNTROWS ( games )", NUM),
    ("Ticketing & Attendance", "Revenue per Game", "DIVIDE ( [Ticket Revenue], [Games Played] )", CUR0),

    ("Fan Segmentation", "Unique Buyers", "DISTINCTCOUNT ( ticket_sales[fan_id] )", NUM),
    ("Fan Segmentation", "Buyers in Segment",
     "CALCULATE ( COUNTROWS ( fan_segments ), KEEPFILTERS ( fan_segments[games_purchased] > 0 ) )", NUM),
    ("Fan Segmentation", "Segment Revenue", "VAR r = SUM ( fan_segments[total_spend] ) RETURN IF ( r > 0, r )", CUR0),
    ("Fan Segmentation", "Avg Spend per Fan", "DIVIDE ( [Segment Revenue], [Buyers in Segment] )", CUR0),
    ("Fan Segmentation", "Avg Games per Fan",
     "CALCULATE ( AVERAGE ( fan_segments[games_purchased] ), KEEPFILTERS ( fan_segments[games_purchased] > 0 ) )", "0.0"),
    ("Fan Segmentation", "Avg Engagement Score",
     "CALCULATE ( AVERAGE ( fan_segments[engagement_score] ), KEEPFILTERS ( fan_segments[games_purchased] > 0 ) )", "0"),
    ("Fan Segmentation", "Non-Member Buyers",
     'CALCULATE ( COUNTROWS ( fan_segments ), KEEPFILTERS ( fan_segments[games_purchased] > 0 ), KEEPFILTERS ( fan_segments[segment] <> "Season Ticket Member" ) )', NUM),
    ("Fan Segmentation", "Repeat Buyers",
     'CALCULATE ( COUNTROWS ( fan_segments ), KEEPFILTERS ( fan_segments[games_purchased] >= 2 ), KEEPFILTERS ( fan_segments[segment] <> "Season Ticket Member" ) )', NUM),
    ("Fan Segmentation", "Repeat Purchase Rate %", "DIVIDE ( [Repeat Buyers], [Non-Member Buyers] )", PCT),
    ("Fan Segmentation", "First Half Buyers",
     "CALCULATE ( COUNTROWS ( fan_segments ), KEEPFILTERS ( fan_segments[bought_first_half] = 1 ) )", NUM),
    ("Fan Segmentation", "Retained Buyers",
     "CALCULATE ( COUNTROWS ( fan_segments ), KEEPFILTERS ( fan_segments[bought_first_half] = 1 ), KEEPFILTERS ( fan_segments[bought_second_half] = 1 ) )", NUM),
    ("Fan Segmentation", "Fan Retention Rate %", "DIVIDE ( [Retained Buyers], [First Half Buyers] )", PCT),
    ("Fan Segmentation", "High-Value Fans",
     'CALCULATE ( COUNTROWS ( fan_segments ), KEEPFILTERS ( fan_segments[segment] = "High-Value Fan" ) )', NUM),
    ("Fan Segmentation", "At-Risk Fans",
     'CALCULATE ( COUNTROWS ( fan_segments ), KEEPFILTERS ( fan_segments[segment] = "At-Risk Fan" ) )', NUM),
    ("Fan Segmentation", "First-Time Buyers",
     'CALCULATE ( COUNTROWS ( fan_segments ), KEEPFILTERS ( fan_segments[segment] = "First-Time Buyer" ) )', NUM),
    ("Fan Segmentation", "Plan Candidates",
     "CALCULATE ( COUNTROWS ( fan_segments ), KEEPFILTERS ( fan_segments[plan_candidate] = 1 ) )", NUM),

    ("Marketing", "Messages Sent", "COUNTROWS ( campaign_responses )", NUM),
    ("Marketing", "Clicks", "SUM ( campaign_responses[clicked] )", NUM),
    ("Marketing", "Conversions", "SUM ( campaign_responses[converted] )", NUM),
    ("Marketing", "Response Rate %", "DIVIDE ( [Clicks], [Messages Sent] )", PCT),
    ("Marketing", "Conversion Rate %", "DIVIDE ( [Conversions], [Messages Sent] )", PCT2),
    ("Marketing", "Campaign Cost", "SUM ( campaigns[cost] )", CUR0),
    ("Marketing", "Campaign Revenue", "SUM ( campaigns[revenue_generated] )", CUR0),
    ("Marketing", "Cost per Conversion", "DIVIDE ( [Campaign Cost], SUM ( campaigns[conversions] ) )", CUR2),
    ("Marketing", "Campaign ROI", "DIVIDE ( [Campaign Revenue] - [Campaign Cost], [Campaign Cost] )", MULT),

    ("Sponsorship", "Sponsor Impressions", "SUM ( sponsorship[impressions] )", NUM),
    ("Sponsorship", "Sponsor Engagements", "SUM ( sponsorship[engagements] )", NUM),
    ("Sponsorship", "Engagement Rate %", "DIVIDE ( [Sponsor Engagements], [Sponsor Impressions] )", PCT2),
    ("Sponsorship", "Estimated Partner Value", "SUM ( sponsorship[estimated_value] )", CUR0),
    ("Sponsorship", "Active Partners", "DISTINCTCOUNT ( sponsorship[sponsor_id] )", NUM),
]
MEASURE_NAMES = {m[1] for m in MEASURES}
SUM_COLUMNS = {"quantity", "ticket_revenue", "tickets_scanned", "opened", "clicked", "converted", "impressions",
               "engagements", "estimated_value", "cost", "clicks", "conversions", "revenue_generated", "capacity"}
M_TYPE = {T: "type text", I: "Int64.Type", D: "type number", DT: "type date"}


def q(name: str) -> str:
    """Quote a TMDL object name when it needs it."""
    return name if name.replace("_", "").isalnum() else "'" + name.replace("'", "''") + "'"


def table_tmdl(table: str) -> str:
    cols = TABLES[table]
    out = [f"table {q(table)}", f"\tlineageTag: {guid()}", ""]
    for name, typ in cols:
        out.append(f"\tcolumn {q(name)}")
        out.append(f"\t\tdataType: {'dateTime' if typ == DT else typ}")
        if typ == DT:
            out.append("\t\tformatString: Short Date")
        elif typ == I:
            out.append("\t\tformatString: 0")
        out.append(f"\t\tlineageTag: {guid()}")
        summarize = "sum" if (name in SUM_COLUMNS and table != "fan_segments" and typ in (I, D)) else "none"
        out.append(f"\t\tsummarizeBy: {summarize}")
        out.append(f"\t\tsourceColumn: {name}")
        if (table, name) in SORT_BY:
            out.append(f"\t\tsortByColumn: {q(SORT_BY[(table, name)])}")
        out.append("")
        out.append("\t\tannotation SummarizationSetBy = Automatic")
        if typ == DT:
            out.append("")
            out.append("\t\tannotation UnderlyingDateTimeDataType = Date")
        out.append("")
    for name, expr, sort_by in CALC_COLUMNS.get(table, []):
        out.append(f"\tcolumn {q(name)} = {expr}")
        out.append(f"\t\tlineageTag: {guid()}")
        out.append("\t\tsummarizeBy: none")
        if sort_by:
            out.append(f"\t\tsortByColumn: {q(sort_by)}")
        out.append("")
        out.append("\t\tannotation SummarizationSetBy = Automatic")
        out.append("")

    types = ", ".join('{"%s", %s}' % (n, M_TYPE[t]) for n, t in cols)
    steps = [
        f'Source = Csv.Document(File.Contents(DataFolder & "\\{table}.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
        "Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
    ]
    last = "Headers"
    if table in NULL_IF_EMPTY:
        cols_list = ", ".join(f'"{c}"' for c in NULL_IF_EMPTY[table])
        steps.append(f'Blanks = Table.ReplaceValue({last}, "", null, Replacer.ReplaceValue, {{{cols_list}}}),')
        last = "Blanks"
    steps.append(f'Typed = Table.TransformColumnTypes({last}, {{{types}}}, "en-US")')
    out.append(f"\tpartition {q(table)} = m")
    out.append("\t\tmode: import")
    out.append("\t\tsource =")
    out.append("\t\t\t\tlet")
    out.extend("\t\t\t\t    " + s for s in steps)
    out.append("\t\t\t\tin")
    out.append("\t\t\t\t    Typed")
    out.append("")
    out.append("\tannotation PBI_ResultType = Table")
    out.append("")
    return "\n".join(out)


def measures_tmdl() -> str:
    out = [f"table {M}", f"\tlineageTag: {guid()}", ""]
    for section, name, expr, fmt in MEASURES:
        out.append(f"\tmeasure {q(name)} = {expr}")
        if fmt:
            out.append(f"\t\tformatString: {fmt}")
        out.append(f"\t\tdisplayFolder: {section}")
        out.append(f"\t\tlineageTag: {guid()}")
        out.append("")
    out += ["\tcolumn Placeholder", "\t\tdataType: string", "\t\tisHidden", f"\t\tlineageTag: {guid()}",
            "\t\tsummarizeBy: none", "\t\tsourceColumn: Placeholder", "",
            "\t\tannotation SummarizationSetBy = Automatic", "",
            f"\tpartition {M} = m", "\t\tmode: import", "\t\tsource =",
            "\t\t\t\tlet", "\t\t\t\t    Source = #table(type table [Placeholder = text], {})",
            "\t\t\t\tin", "\t\t\t\t    Source", "",
            "\tannotation PBI_ResultType = Table", ""]
    return "\n".join(out)


def build_model(data_folder: str):
    d = MODEL_DIR / "definition"
    write_json(MODEL_DIR / "definition.pbism", {"version": "4.0", "settings": {}})
    write_json(MODEL_DIR / ".platform", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "SemanticModel", "displayName": NAME},
        "config": {"version": "2.0", "logicalId": guid()}})
    write(d / "database.tmdl", "database\n\tcompatibilityLevel: 1567\n")
    order = json.dumps(["DataFolder"] + list(TABLES) + [M], separators=(",", ":"))
    model = ["model Model", "\tculture: en-US", "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
             "\tsourceQueryCulture: en-US", "\tdataAccessOptions", "\t\tlegacyRedirects",
             "\t\treturnErrorValuesAsNull", "", "annotation __PBI_TimeIntelligenceEnabled = 0", "",
             f"annotation PBI_QueryOrder = {order}", ""]
    model += [f"ref table {q(t)}" for t in list(TABLES) + [M]]
    write(d / "model.tmdl", "\n".join(model) + "\n")

    rel = []
    for many, one in RELATIONSHIPS:
        rel += [f"relationship {guid()}", f"\tfromColumn: {many}", f"\ttoColumn: {one}", ""]
    rel += [f"relationship {guid()}", "\tcrossFilteringBehavior: bothDirections", "\tfromCardinality: one",
            "\tfromColumn: fan_segments.fan_id", "\ttoColumn: fans.fan_id", ""]
    write(d / "relationships.tmdl", "\n".join(rel))

    write(d / "expressions.tmdl",
          f'expression DataFolder = "{data_folder}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
          f"\tlineageTag: {guid()}\n\n\tannotation PBI_ResultType = Text\n")
    for t in TABLES:
        write(d / "tables" / f"{t}.tmdl", table_tmdl(t))
    write(d / "tables" / f"{M}.tmdl", measures_tmdl())


# =============================================================================
# Report
# =============================================================================
def lit(text: str) -> dict:
    return {"expr": {"Literal": {"Value": "'" + text.replace("'", "''") + "'"}}}


def raw(value: str) -> dict:
    return {"expr": {"Literal": {"Value": value}}}


def field(ref: str) -> dict:
    """'Measure Name' -> measure in _Measures. 'table.column' -> column."""
    if ref in MEASURE_NAMES:
        return {"Measure": {"Expression": {"SourceRef": {"Entity": M}}, "Property": ref}}
    table, column = ref.split(".", 1)
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": column}}


def proj(ref: str, display: str = None, active: bool = False) -> dict:
    is_measure = ref in MEASURE_NAMES
    p = {"field": field(ref),
         "queryRef": f"{M}.{ref}" if is_measure else ref,
         "nativeQueryRef": ref if is_measure else ref.split(".", 1)[1]}
    if display:
        p["displayName"] = display
    if active:
        p["active"] = True
    return p


def in_filter(ref: str, values: list) -> dict:
    table, column = ref.split(".", 1)
    return {"name": "Filter" + hexid(), "field": field(ref), "type": "Categorical",
            "filter": {"Version": 2, "From": [{"Name": "t", "Entity": table, "Type": 0}],
                       "Where": [{"Condition": {"In": {
                           "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "t"}},
                                                       "Property": column}}],
                           "Values": [[{"Literal": {"Value": "'" + v.replace("'", "''") + "'"}}] for v in values]}}}]},
            "howCreated": "User"}


class Page:
    def __init__(self, title: str):
        self.name = "ReportSection" + hexid()
        self.title = title
        self.visuals = []
        self.z = 0

    def add(self, vtype, x, y, w, h, roles=None, title=None, sort=None, objects=None, filters=None):
        self.z += 1000
        visual = {"visualType": vtype}
        if roles:
            state = {}
            for role, items in roles.items():
                projections = []
                for k, item in enumerate(items):
                    ref, display = item if isinstance(item, tuple) else (item, None)
                    is_axis = role in ("Category", "Rows", "Columns") or vtype == "slicer"
                    projections.append(proj(ref, display, active=is_axis and k == 0 and ref not in MEASURE_NAMES))
                state[role] = {"projections": projections}
            visual["query"] = {"queryState": state}
            if sort:
                visual["query"]["sortDefinition"] = {"sort": [{"field": field(sort[0]), "direction": sort[1]}]}
        if objects:
            visual["objects"] = objects
        if title:
            visual["visualContainerObjects"] = {"title": [{"properties": {"show": raw("true"), "text": lit(title)}}]}
        visual["drillFilterOtherVisuals"] = True
        container = {"$schema": f"{SCHEMA}/visualContainer/1.6.0/schema.json", "name": hexid(),
                     "position": {"x": x, "y": y, "z": self.z, "height": h, "width": w, "tabOrder": self.z},
                     "visual": visual}
        if filters:
            container["filterConfig"] = {"filters": filters}
        self.visuals.append(container)

    def text(self, x, y, w, h, paragraphs):
        """paragraphs: list of (text, font size pt, bold, hex color)."""
        self.z += 1000
        paras = []
        for value, size, bold, color in paragraphs:
            style = {"fontSize": f"{size}pt", "color": color}
            if bold:
                style["fontWeight"] = "bold"
            paras.append({"textRuns": [{"value": value, "textStyle": style}]})
        self.visuals.append({
            "$schema": f"{SCHEMA}/visualContainer/1.6.0/schema.json", "name": hexid(),
            "position": {"x": x, "y": y, "z": self.z, "height": h, "width": w, "tabOrder": self.z},
            "visual": {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": paras}}]},
                       "drillFilterOtherVisuals": True}})

    def card_grid(self, items, per_row, y0, h=84):
        """items: list of (measure, label), laid out in rows of per_row cards."""
        gap, x0 = 10, 20
        w = (1240 - gap * (per_row - 1)) / per_row
        for k, (measure, label) in enumerate(items):
            self.add("card", x0 + (k % per_row) * (w + gap), y0 + (k // per_row) * (h + 8), w, h,
                     {"Values": [measure]}, title=label,
                     objects={"labels": [{"properties": {"fontSize": raw("22D")}}],
                              "categoryLabels": [{"properties": {"show": raw("false")}}]})

    def header(self, subtitle: str, width: int = 620):
        self.z += 1000
        self.visuals.append({
            "$schema": f"{SCHEMA}/visualContainer/1.6.0/schema.json", "name": hexid(),
            "position": {"x": 20, "y": 8, "z": self.z, "height": 52, "width": width, "tabOrder": self.z},
            "visual": {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": [
                {"textRuns": [{"value": self.title, "textStyle": {"fontWeight": "bold", "fontSize": "20pt",
                                                                  "color": "#1D1160"}}]}]}}]},
                "drillFilterOtherVisuals": True}})
        self.z += 1000
        self.visuals.append({
            "$schema": f"{SCHEMA}/visualContainer/1.6.0/schema.json", "name": hexid(),
            "position": {"x": 20, "y": 692, "z": self.z, "height": 26, "width": 1240, "tabOrder": self.z},
            "visual": {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": [
                {"textRuns": [{"value": subtitle, "textStyle": {"fontSize": "8pt", "color": "#666666"}}]}]}}]},
                "drillFilterOtherVisuals": True}})

    def cards(self, items):
        """items: list of (measure, label). Five cards across the page."""
        w, gap, x0 = 240, 10, 20
        for k, (measure, label) in enumerate(items):
            self.add("card", x0 + k * (w + gap), 66, w, 88, {"Values": [measure]}, title=label,
                     objects={"labels": [{"properties": {"fontSize": raw("22D")}}],
                              "categoryLabels": [{"properties": {"show": raw("false")}}]})

    def slicers(self, refs):
        """Dropdown slicers in the top right corner."""
        w, gap = 190, 10
        x0 = 1260 - len(refs) * w - (len(refs) - 1) * gap
        for k, (ref, label) in enumerate(refs):
            self.add("slicer", x0 + k * (w + gap), 4, w, 58, {"Values": [ref]}, title=label,
                     objects={"data": [{"properties": {"mode": lit("Dropdown")}}],
                              "header": [{"properties": {"show": raw("false")}}]})


FOOTER = ("Independent demonstration project by Tejas Bhanushali. Simulated dataset designed to reflect realistic "
          "sports business scenarios. Not Phoenix Suns data and not affiliated with the Phoenix Suns.")
GAME_SLICERS = [("games.opponent_tier", "Opponent tier"), ("games.day_type", "Day type"), ("games.Month", "Month")]
R1Y, R1H, R2Y, R2H = 162, 258, 428, 258      # two chart rows


def build_pages():
    key = json.loads((ROOT / "outputs" / "key_numbers.json").read_text(encoding="utf-8"))
    pages = []

    # ---------------- 1. Executive Summary ----------------
    p = Page("Phoenix Suns Fan Revenue & Strategy Intelligence Hub")
    p.tab = "Executive Summary"
    p.header(FOOTER, width=1240)
    p.card_grid([("Ticket Revenue", "Total ticket revenue"), ("Attendance Rate %", "Attendance rate"),
                 ("Avg Ticket Price", "Average ticket price"), ("Sell-Through %", "Sell-through rate"),
                 ("Repeat Purchase Rate %", "Repeat purchase rate"), ("Fan Retention Rate %", "Fan retention rate"),
                 ("Conversion Rate %", "Campaign conversion rate"), ("Sponsor Engagements", "Sponsor engagements")],
                per_row=4, y0=66)
    p.add("columnChart", 20, 254, 780, 430, {"Category": ["games.Game Label"], "Y": ["Ticket Revenue"]},
          title="Ticket revenue by home game", sort=("games.Game Label", "Ascending"))
    p.add("clusteredBarChart", 810, 254, 450, 430, {"Category": ["fan_segments.segment"], "Y": ["Segment Revenue"]},
          title="Ticket revenue by fan segment", sort=("Segment Revenue", "Descending"))
    pages.append(p)

    # ---------------- 2. Ticketing & Attendance ----------------
    p = Page("Ticketing & Attendance")
    p.header(FOOTER)
    p.slicers(GAME_SLICERS)
    p.cards([("Tickets Sold", "Tickets sold"), ("Revenue per Game", "Revenue per game"),
             ("Sell-Through %", "Sell-through rate"), ("No-Show Rate %", "No-show rate"),
             ("Unsold Seats", "Unsold seats")])
    p.add("lineStackedColumnComboChart", 20, R1Y, 830, R1H,
          {"Category": ["games.Game Label"], "Y": ["Tickets Scanned", "No-Show Tickets"], "Y2": ["Capacity"]},
          title="Tickets sold versus attendance by game (scanned plus no-shows = sold)",
          sort=("games.Game Label", "Ascending"))
    p.add("pivotTable", 860, R1Y, 400, R1H,
          {"Rows": ["games.opponent_tier"], "Columns": ["games.weekday"], "Values": ["Sell-Through %"]},
          title="Sell-through: opponent tier by weekday")
    p.add("clusteredColumnChart", 20, R2Y, 330, R2H,
          {"Category": ["games.opponent_tier"], "Series": ["games.day_type"], "Y": ["No-Show Rate %"]},
          title="No-show rate by opponent tier and day type")
    p.add("donutChart", 360, R2Y, 300, R2H, {"Category": ["ticket_sales.ticket_type"], "Y": ["Ticket Revenue"]},
          title="Revenue by ticket type")
    p.add("tableEx", 670, R2Y, 590, R2H,
          {"Values": [("games.Game Label", "Game"), ("games.opponent_tier", "Tier"), ("games.weekday", "Day"),
                      ("Tickets Sold", "Sold"), ("Unsold Seats", "Unsold"), ("Sell-Through %", "Sell-through"),
                      ("No-Show Rate %", "No-show"), ("Avg Ticket Price", "Avg price")]},
          title="Games needing promotional support (lowest sell-through first)", sort=("Sell-Through %", "Ascending"))
    pages.append(p)

    # ---------------- 3. Fan Segmentation ----------------
    p = Page("Fan Segmentation")
    p.header(FOOTER)
    p.slicers([("fans.city", "City"), ("fans.age_group", "Age group")])
    p.cards([("Unique Buyers", "Unique buyers"), ("Avg Spend per Fan", "Average spend per fan"),
             ("High-Value Fans", "High-value fans"), ("At-Risk Fans", "At-risk fans"),
             ("First-Time Buyers", "First-time buyers")])
    p.add("clusteredBarChart", 20, R1Y, 400, R1H, {"Category": ["fan_segments.segment"], "Y": ["Buyers in Segment"]},
          title="Segment size", sort=("Buyers in Segment", "Descending"))
    p.add("clusteredBarChart", 430, R1Y, 400, R1H, {"Category": ["fan_segments.segment"], "Y": ["Segment Revenue"]},
          title="Revenue by segment", sort=("Segment Revenue", "Descending"))
    p.add("scatterChart", 840, R1Y, 420, R1H,
          {"Category": ["fan_segments.segment"], "X": ["Avg Engagement Score"], "Y": ["Avg Spend per Fan"],
           "Size": ["Buyers in Segment"]},
          title="Spend versus engagement by segment")
    p.add("pivotTable", 20, R2Y, 330, R2H,
          {"Rows": ["fan_segments.r_score"], "Columns": ["fan_segments.f_score"], "Values": ["Buyers in Segment"]},
          title="RFM grid: recency score (rows) by frequency score")
    p.add("tableEx", 360, R2Y, 470, R2H,
          {"Values": [("fan_segments.segment", "Segment"), ("Buyers in Segment", "Fans"), ("Segment Revenue", "Revenue"),
                      ("Avg Spend per Fan", "Avg spend"), ("Avg Games per Fan", "Avg games"),
                      ("Avg Engagement Score", "Engagement")]},
          title="Segment profile", sort=("Segment Revenue", "Descending"))
    p.add("tableEx", 840, R2Y, 420, R2H,
          {"Values": [("fan_segments.fan_id", "Fan"), ("fans.city", "City"), ("fan_segments.games_purchased", "Games"),
                      ("fan_segments.total_spend", "Spend"), ("fan_segments.recency_days", "Days since last game")]},
          title="At-risk fans: retention target list", sort=("fan_segments.total_spend", "Descending"),
          filters=[in_filter("fan_segments.segment", ["At-Risk Fan"])])
    pages.append(p)

    # ---------------- 4. Marketing & Campaign Performance ----------------
    p = Page("Marketing & Campaign Performance")
    p.header(FOOTER + " Campaign revenue uses last-touch attribution.")
    p.slicers([("campaigns.campaign_type", "Campaign type"), ("campaigns.channel", "Channel")])
    p.cards([("Messages Sent", "Messages sent"), ("Response Rate %", "Response rate"),
             ("Conversion Rate %", "Conversion rate"), ("Campaign Revenue", "Revenue from campaigns"),
             ("Campaign ROI", "Campaign ROI")])
    p.add("clusteredBarChart", 20, R1Y, 430, R1H, {"Category": ["campaigns.campaign_name"], "Y": ["Conversion Rate %"]},
          title="Conversion rate by campaign", sort=("Conversion Rate %", "Descending"))
    p.add("clusteredBarChart", 460, R1Y, 400, R1H, {"Category": ["fan_segments.segment"], "Y": ["Conversion Rate %"]},
          title="Conversion rate by fan segment", sort=("Conversion Rate %", "Descending"))
    p.add("clusteredColumnChart", 870, R1Y, 390, R1H,
          {"Category": ["campaigns.campaign_type"], "Y": ["Campaign ROI"]},
          title="ROI by campaign type", sort=("Campaign ROI", "Descending"))
    p.add("clusteredBarChart", 20, R2Y, 430, R2H, {"Category": ["campaigns.campaign_name"], "Y": ["Campaign Revenue"]},
          title="Revenue from promotions and campaigns", sort=("Campaign Revenue", "Descending"))
    p.add("tableEx", 460, R2Y, 800, R2H,
          {"Values": [("campaigns.campaign_name", "Campaign"), ("campaigns.campaign_type", "Type"),
                      ("campaigns.channel", "Channel"), ("campaigns.target_segment", "Target"),
                      ("Campaign Cost", "Cost"), ("Messages Sent", "Sent"), ("Response Rate %", "Response"),
                      ("Conversion Rate %", "Conversion"), ("Campaign Revenue", "Revenue"),
                      ("Cost per Conversion", "Cost per conv"), ("Campaign ROI", "ROI")]},
          title="Campaign detail", sort=("Campaign ROI", "Descending"))
    pages.append(p)

    # ---------------- 5. Sponsorship & Partner Insights ----------------
    p = Page("Sponsorship & Partner Insights")
    p.header(FOOTER + " Sponsor names are fictional.")
    p.slicers([("sponsorship.sponsor_name", "Partner"), ("games.opponent_tier", "Opponent tier")])
    p.cards([("Active Partners", "Partners"), ("Sponsor Impressions", "Sponsored reach (impressions)"),
             ("Sponsor Engagements", "Fan engagements"), ("Engagement Rate %", "Engagement rate"),
             ("Estimated Partner Value", "Estimated partner value")])
    p.add("clusteredBarChart", 20, R1Y, 430, R1H, {"Category": ["sponsorship.sponsor_name"], "Y": ["Sponsor Engagements"]},
          title="Fan engagements by partner", sort=("Sponsor Engagements", "Descending"))
    p.add("clusteredBarChart", 460, R1Y, 390, R1H,
          {"Category": ["sponsorship.activation_name"], "Y": ["Engagement Rate %"]},
          title="Engagement rate by sponsor activation", sort=("Engagement Rate %", "Descending"))
    p.add("pivotTable", 860, R1Y, 400, R1H,
          {"Rows": ["sponsorship.sponsor_name"], "Columns": ["sponsorship.activation_name"],
           "Values": ["Sponsor Engagements"]},
          title="Engagements: partner by activation")
    p.add("scatterChart", 20, R2Y, 430, R2H,
          {"Category": ["games.Game Label"], "Series": ["games.opponent_tier"], "X": ["Tickets Scanned"],
           "Y": ["Sponsor Engagements"]},
          title="Sponsor engagement versus attendance by game")
    p.add("tableEx", 460, R2Y, 800, R2H,
          {"Values": [("sponsorship.sponsor_name", "Partner"), ("sponsorship.activation_name", "Activation"),
                      ("Sponsor Impressions", "Impressions"), ("Sponsor Engagements", "Engagements"),
                      ("Engagement Rate %", "Engagement rate"), ("Estimated Partner Value", "Estimated value")]},
          title="Activation performance", sort=("Sponsor Engagements", "Descending"))
    pages.append(p)

    # ---------------- 6. Recommendations ----------------
    p = Page("Recommendations")
    p.header(FOOTER + " Sizing figures are scenarios built from stated assumptions, not forecasts.")
    for k, r in enumerate(key["recommendations"][:6]):
        p.text(20 + (k % 3) * 415, 70 + (k // 3) * 308, 405, 298, [
            (f"{k + 1}. {r['action']}", 13, True, "#1D1160"),
            (r["detail"], 10, False, "#252423"),
            (r["sizing"], 10, True, "#E56020"),
        ])
    pages.append(p)
    return pages


def build_report():
    d = REPORT_DIR / "definition"
    write_json(REPORT_DIR / "definition.pbir",
               {"version": "4.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}})
    write_json(REPORT_DIR / ".platform", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Report", "displayName": NAME},
        "config": {"version": "2.0", "logicalId": guid()}})
    write_json(d / "version.json", {"$schema": f"{SCHEMA}/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
    write_json(d / "report.json", {
        "$schema": f"{SCHEMA}/report/1.2.0/schema.json",
        "themeCollection": {"baseTheme": {"name": "CY24SU10", "reportVersionAtImport": "5.61",
                                          "type": "SharedResources"}},
        "layoutOptimization": "None",
        "resourcePackages": [{"name": "SharedResources", "type": "SharedResources", "items": [
            {"name": "CY24SU10", "path": "BaseThemes/CY24SU10.json", "type": "BaseTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarizedAndUnderlying",
                     "defaultFilterActionIsDataFilter": True, "defaultDrillFilterOtherVisuals": True,
                     "allowChangeFilterTypes": True, "allowInlineExploration": True, "useEnhancedTooltips": True},
        "slowDataSourceSettings": {"isCrossHighlightingDisabled": False, "isSlicerSelectionsButtonEnabled": False,
                                   "isFilterSelectionsButtonEnabled": False, "isFieldWellButtonEnabled": False,
                                   "isApplyAllButtonEnabled": False}})
    theme_target = REPORT_DIR / "StaticResources" / "SharedResources" / "BaseThemes" / "CY24SU10.json"
    theme_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(BASE_THEME, theme_target)

    pages = build_pages()
    write_json(d / "pages" / "pages.json", {"$schema": f"{SCHEMA}/pagesMetadata/1.0.0/schema.json",
                                            "pageOrder": [p.name for p in pages], "activePageName": pages[0].name})
    for p in pages:
        write_json(d / "pages" / p.name / "page.json", {
            "$schema": f"{SCHEMA}/page/1.3.0/schema.json", "name": p.name,
            "displayName": getattr(p, "tab", p.title),
            "displayOption": "FitToPage", "height": 720, "width": 1280})
        for v in p.visuals:
            write_json(d / "pages" / p.name / "visuals" / v["name"] / "visual.json", v)
    return pages


def write_dax_reference():
    lines = ["// Phoenix Suns Fan Revenue & Strategy Intelligence Hub: DAX reference",
             "// These measures and calculated columns are already inside Phoenix_Suns_Strategy_Hub.pbip.",
             "// This file is for reading, and for a manual rebuild if you ever need one.", ""]
    section = None
    for sec, name, expr, _ in MEASURES:
        if sec != section:
            lines += [f"// ---------- {sec} ----------"]
            section = sec
        lines += [f"{name} = {expr}", ""]
    lines += ["// ---------- Calculated columns ----------"]
    for table, cols in CALC_COLUMNS.items():
        for name, expr, sort_by in cols:
            lines += [f"// table: {table}" + (f", sort by column: {sort_by}" if sort_by else ""), f"{name} = {expr}", ""]
    write(PBI / "measures.dax", "\n".join(lines))


def main():
    force = "--force" in sys.argv
    pbip = PBI / f"{NAME}.pbip"
    missing = [t for t in TABLES if not (CLEAN / f"{t}.csv").exists()]
    if not (ROOT / "outputs" / "key_numbers.json").exists():
        missing.append("outputs/key_numbers.json")
    if missing:
        sys.exit(f"Clean data not found for: {', '.join(missing)}. Run python run_pipeline.py first.")
    if pbip.exists() and not force:
        print(f"  {pbip.name} already exists, left unchanged (use --force to rebuild)")
        return
    for folder in (MODEL_DIR, REPORT_DIR):
        if folder.exists():
            shutil.rmtree(folder)
    data_folder = str(CLEAN.resolve())
    build_model(data_folder)
    pages = build_report()
    write_json(pbip, {"$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
                      "version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
                      "settings": {"enableAutoRecovery": True}})
    write_dax_reference()
    print(f"  model: {len(TABLES)} tables, {len(RELATIONSHIPS) + 1} relationships, {len(MEASURES)} measures")
    print(f"  report: {len(pages)} pages, {sum(len(p.visuals) for p in pages)} visuals")
    print(f"  data folder parameter: {data_folder}")
    print(f"  open in Power BI Desktop: powerbi\\{pbip.name}")


if __name__ == "__main__":
    print("Step 4: building Power BI dashboard project")
    main()
