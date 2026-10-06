-- Phoenix Suns Fan Revenue & Strategy Intelligence Hub: relational schema (SQLite)
-- All tables hold simulated data.
DROP VIEW IF EXISTS v_game_summary;
DROP VIEW IF EXISTS v_fan_summary;
DROP TABLE IF EXISTS fan_segments;
DROP TABLE IF EXISTS sponsorship;
DROP TABLE IF EXISTS campaign_responses;
DROP TABLE IF EXISTS attendance;
DROP TABLE IF EXISTS ticket_sales;
DROP TABLE IF EXISTS campaigns;
DROP TABLE IF EXISTS games;
DROP TABLE IF EXISTS fans;

CREATE TABLE fans (
    fan_id               TEXT PRIMARY KEY,
    age_group            TEXT NOT NULL,
    city                 TEXT NOT NULL,
    acquisition_channel  TEXT NOT NULL,
    membership_status    TEXT NOT NULL,
    join_date            TEXT NOT NULL
);

CREATE TABLE games (
    game_id        TEXT PRIMARY KEY,
    opponent       TEXT NOT NULL,
    game_date      TEXT NOT NULL,
    weekday        TEXT NOT NULL,
    day_type       TEXT NOT NULL,
    game_type      TEXT NOT NULL,
    home_away      TEXT NOT NULL,
    opponent_tier  TEXT NOT NULL,
    capacity       INTEGER NOT NULL
);

CREATE TABLE campaigns (
    campaign_id        TEXT PRIMARY KEY,
    campaign_name      TEXT NOT NULL,
    campaign_type      TEXT NOT NULL,
    channel            TEXT NOT NULL,
    target_segment     TEXT NOT NULL,
    send_date          TEXT NOT NULL,
    cost               REAL NOT NULL,
    impressions        INTEGER NOT NULL,
    clicks             INTEGER NOT NULL,
    conversions        INTEGER NOT NULL,
    revenue_generated  REAL NOT NULL
);

CREATE TABLE ticket_sales (
    transaction_id    TEXT PRIMARY KEY,
    fan_id            TEXT NOT NULL REFERENCES fans(fan_id),
    game_id           TEXT NOT NULL REFERENCES games(game_id),
    ticket_type       TEXT NOT NULL,
    seat_section      TEXT NOT NULL,
    quantity          INTEGER NOT NULL CHECK (quantity > 0),
    ticket_revenue    REAL NOT NULL CHECK (ticket_revenue > 0),
    purchase_date     TEXT NOT NULL,
    purchase_channel  TEXT NOT NULL,
    campaign_id       TEXT REFERENCES campaigns(campaign_id)
);

CREATE TABLE attendance (
    attendance_id    TEXT PRIMARY KEY,
    transaction_id   TEXT NOT NULL REFERENCES ticket_sales(transaction_id),
    fan_id           TEXT NOT NULL REFERENCES fans(fan_id),
    game_id          TEXT NOT NULL REFERENCES games(game_id),
    tickets_scanned  INTEGER NOT NULL,
    scanned_flag     INTEGER NOT NULL
);

CREATE TABLE campaign_responses (
    response_id  TEXT PRIMARY KEY,
    campaign_id  TEXT NOT NULL REFERENCES campaigns(campaign_id),
    fan_id       TEXT NOT NULL REFERENCES fans(fan_id),
    opened       INTEGER NOT NULL,
    clicked      INTEGER NOT NULL,
    converted    INTEGER NOT NULL
);

CREATE TABLE sponsorship (
    sponsorship_id   TEXT PRIMARY KEY,
    sponsor_id       TEXT NOT NULL,
    sponsor_name     TEXT NOT NULL,
    activation_name  TEXT NOT NULL,
    game_id          TEXT NOT NULL REFERENCES games(game_id),
    impressions      INTEGER NOT NULL,
    engagements      INTEGER NOT NULL,
    estimated_value  REAL NOT NULL
);

CREATE INDEX ix_sales_fan  ON ticket_sales(fan_id);
CREATE INDEX ix_sales_game ON ticket_sales(game_id);
CREATE INDEX ix_att_game   ON attendance(game_id);
CREATE INDEX ix_att_fan    ON attendance(fan_id);
CREATE INDEX ix_resp_fan   ON campaign_responses(fan_id);

CREATE VIEW v_game_summary AS
WITH s AS (
    SELECT game_id, SUM(quantity) AS tickets_sold, SUM(ticket_revenue) AS ticket_revenue
    FROM ticket_sales GROUP BY game_id
),
a AS (
    SELECT game_id, SUM(tickets_scanned) AS tickets_scanned
    FROM attendance GROUP BY game_id
)
SELECT g.game_id, g.game_date, g.opponent, g.opponent_tier, g.weekday, g.day_type, g.game_type, g.capacity,
       s.tickets_sold, a.tickets_scanned,
       ROUND(s.ticket_revenue, 2)                               AS ticket_revenue,
       ROUND(s.ticket_revenue / s.tickets_sold, 2)              AS avg_ticket_price,
       ROUND(1.0 * s.tickets_sold / g.capacity, 4)              AS sell_through,
       ROUND(1.0 * a.tickets_scanned / s.tickets_sold, 4)       AS attendance_rate,
       ROUND(1.0 - 1.0 * a.tickets_scanned / s.tickets_sold, 4) AS no_show_rate,
       g.capacity - s.tickets_sold                              AS unsold_seats
FROM games g
JOIN s ON s.game_id = g.game_id
JOIN a ON a.game_id = g.game_id;

CREATE VIEW v_fan_summary AS
WITH s AS (
    SELECT fan_id, COUNT(DISTINCT game_id) AS games_purchased, SUM(quantity) AS tickets_purchased,
           SUM(ticket_revenue) AS total_spend
    FROM ticket_sales GROUP BY fan_id
),
lg AS (
    SELECT t.fan_id, MAX(g.game_date) AS last_game_date
    FROM ticket_sales t JOIN games g ON g.game_id = t.game_id GROUP BY t.fan_id
),
a AS (
    SELECT fan_id, SUM(scanned_flag) AS games_attended, SUM(tickets_scanned) AS tickets_scanned
    FROM attendance GROUP BY fan_id
),
r AS (
    SELECT fan_id, COUNT(*) AS messages_received, SUM(opened) AS messages_opened, SUM(converted) AS conversions
    FROM campaign_responses GROUP BY fan_id
)
SELECT f.fan_id, f.membership_status,
       COALESCE(s.games_purchased, 0)    AS games_purchased,
       COALESCE(s.tickets_purchased, 0)  AS tickets_purchased,
       COALESCE(a.games_attended, 0)     AS games_attended,
       COALESCE(a.tickets_scanned, 0)    AS tickets_scanned,
       ROUND(COALESCE(s.total_spend, 0), 2) AS total_spend,
       lg.last_game_date,
       COALESCE(r.messages_received, 0)  AS messages_received,
       COALESCE(r.messages_opened, 0)    AS messages_opened,
       COALESCE(r.conversions, 0)        AS campaign_conversions
FROM fans f
LEFT JOIN s  ON s.fan_id = f.fan_id
LEFT JOIN lg ON lg.fan_id = f.fan_id
LEFT JOIN a  ON a.fan_id = f.fan_id
LEFT JOIN r  ON r.fan_id = f.fan_id;
