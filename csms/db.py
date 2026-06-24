"""SQLite storage for the CSMS POC — charge points, sessions and meter readings.

Keeps the data that matters for billing: who charged, where, how much (kWh),
when it started and stopped. This is the table you will later push to Priority.
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).parent / "csms.db"


@contextmanager
def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init_db():
    with conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS charge_points (
                id            TEXT PRIMARY KEY,   -- the charge point identity (URL path)
                vendor        TEXT,
                model         TEXT,
                serial        TEXT,
                last_seen     TEXT,
                status        TEXT
            );

            CREATE TABLE IF NOT EXISTS sessions (
                transaction_id INTEGER PRIMARY KEY,  -- our id, also returned to the charger
                charge_point   TEXT,
                connector_id   INTEGER,
                id_tag         TEXT,                 -- RFID / app token that started it
                meter_start    INTEGER,              -- Wh
                meter_stop     INTEGER,              -- Wh
                kwh            REAL,                  -- computed on stop
                started_at     TEXT,
                stopped_at     TEXT,
                reason         TEXT,
                billed         INTEGER DEFAULT 0      -- 0 = not yet sent to Priority
            );

            CREATE TABLE IF NOT EXISTS meter_values (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id INTEGER,
                connector_id   INTEGER,
                measurand      TEXT,
                value          TEXT,
                unit           TEXT,
                ts             TEXT
            );
            """
        )


def upsert_charge_point(cp_id, vendor=None, model=None, serial=None, ts=None, status=None):
    with conn() as c:
        c.execute(
            """
            INSERT INTO charge_points (id, vendor, model, serial, last_seen, status)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                vendor    = COALESCE(excluded.vendor, vendor),
                model     = COALESCE(excluded.model, model),
                serial    = COALESCE(excluded.serial, serial),
                last_seen = COALESCE(excluded.last_seen, last_seen),
                status    = COALESCE(excluded.status, status)
            """,
            (cp_id, vendor, model, serial, ts, status),
        )


def next_transaction_id():
    with conn() as c:
        row = c.execute("SELECT COALESCE(MAX(transaction_id), 0) + 1 AS n FROM sessions").fetchone()
        return row["n"]


def start_session(transaction_id, cp_id, connector_id, id_tag, meter_start, started_at):
    with conn() as c:
        c.execute(
            """INSERT INTO sessions
               (transaction_id, charge_point, connector_id, id_tag, meter_start, started_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (transaction_id, cp_id, connector_id, id_tag, meter_start, started_at),
        )


def stop_session(transaction_id, meter_stop, stopped_at, reason):
    with conn() as c:
        row = c.execute(
            "SELECT meter_start FROM sessions WHERE transaction_id = ?", (transaction_id,)
        ).fetchone()
        kwh = None
        if row and row["meter_start"] is not None and meter_stop is not None:
            kwh = round((meter_stop - row["meter_start"]) / 1000.0, 3)
        c.execute(
            """UPDATE sessions
               SET meter_stop = ?, stopped_at = ?, reason = ?, kwh = ?
               WHERE transaction_id = ?""",
            (meter_stop, stopped_at, reason, kwh, transaction_id),
        )
        return kwh


def add_meter_value(transaction_id, connector_id, measurand, value, unit, ts):
    with conn() as c:
        c.execute(
            """INSERT INTO meter_values
               (transaction_id, connector_id, measurand, value, unit, ts)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (transaction_id, connector_id, measurand, value, unit, ts),
        )
