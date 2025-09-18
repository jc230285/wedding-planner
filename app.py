from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Iterable, List

from dotenv import load_dotenv
from flask import Flask, abort, jsonify, render_template, request
import psycopg
from psycopg.rows import dict_row

from utils.db import normalize_database_url

load_dotenv()

app = Flask(__name__)

DATABASE_URL_RAW = os.getenv("DATABASE_URL")
DATABASE_URL = normalize_database_url(DATABASE_URL_RAW) if DATABASE_URL_RAW else None

INT_COLUMNS = {"stag", "hen", "friday_room", "ceremony", "wedding_meal", "saturday_room"}
UPDATABLE_COLUMNS = {
    "name",
    "age",
    "side",
    "guest_type",
    "sex",
    "stag",
    "hen",
    "friday_room",
    "ceremony",
    "wedding_meal",
    "restrictions",
    "saturday_room",
    "email",
    "mobile",
    "address",
    "family_id",
    "music_requests",
    "comment",
}
FIELD_ALIASES = {"family_code": "family_id"}
GUEST_COLUMNS = (
    "id",
    "name",
    "age",
    "side",
    "guest_type",
    "sex",
    "stag",
    "hen",
    "friday_room",
    "ceremony",
    "wedding_meal",
    "restrictions",
    "saturday_room",
    "email",
    "mobile",
    "address",
    "family_id",
    "music_requests",
    "comment",
    "created_at",
)


def _require_database_url() -> str:
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not configured.")
    return DATABASE_URL


def _serialize_guest(row: Dict[str, Any]) -> Dict[str, Any]:
    data = dict(row)
    created_at = data.get("created_at")
    if isinstance(created_at, datetime):
        data["created_at"] = created_at.isoformat()
    return data


def _fetch_guests(where_clause: str = "", params: Iterable[Any] = ()) -> List[Dict[str, Any]]:
    sql = f"SELECT {', '.join(GUEST_COLUMNS)} FROM public.guests"
    if where_clause:
        sql = f"{sql} {where_clause}"
    sql = f"{sql} ORDER BY name ASC"

    with psycopg.connect(_require_database_url(), row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, tuple(params))
            rows = cur.fetchall()
    return [_serialize_guest(row) for row in rows]


@app.route("/")
def home() -> str:
    return render_template("index.html")


@app.get("/api/guests")
def get_all_guests():
    guests = _fetch_guests()
    return jsonify({"data": guests})


@app.get("/api/guests/family/<string:family_code>")
def get_guests_by_family(family_code: str):
    guests = _fetch_guests("WHERE family_id = %s", (family_code,))
    if not guests:
        abort(404, description="No guests found for that family code.")
    return jsonify({"data": guests})


@app.get("/api/guests/no-family")
def get_guests_without_family():
    guests = _fetch_guests("WHERE family_id IS NULL OR family_id = ''")
    return jsonify({"data": guests})


def _normalize_update_value(column: str, value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None
    if column in INT_COLUMNS and value is not None:
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Column '{column}' expects an integer.") from exc
    return value


@app.post("/api/guests/update")
def update_guest():
    payload = request.get_json(silent=True)
    if payload is None or not isinstance(payload, dict):
        abort(400, description="Request must contain a JSON object.")

    guest_id = payload.get("id")
    family_code = payload.get("family_code") or payload.get("family_id")
    if not guest_id or not family_code:
        abort(400, description="Both 'id' and 'family_code' (or 'family_id') are required.")

    updates: Dict[str, Any] = {}
    for key, value in payload.items():
        if key in {"id", "family_code"}:
            continue
        column = FIELD_ALIASES.get(key, key)
        if column not in UPDATABLE_COLUMNS:
            abort(400, description=f"Field '{key}' cannot be updated.")
        try:
            updates[column] = _normalize_update_value(column, value)
        except ValueError as exc:
            abort(400, description=str(exc))

    if not updates:
        abort(400, description="No updatable fields were provided.")

    updated_by = payload.get("updated_by")

    try:
        with psycopg.connect(_require_database_url(), row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM public.guests WHERE id = %s AND family_id = %s",
                    (guest_id, family_code),
                )
                current = cur.fetchone()
                if current is None:
                    abort(404, description="Guest not found for provided id and family code.")

                changed: Dict[str, Dict[str, Any]] = {}
                for column, new_value in updates.items():
                    if current.get(column) != new_value:
                        changed[column] = {"old": current.get(column), "new": new_value}

                if not changed:
                    return jsonify({"message": "No changes detected."}), 200

                set_clause = ", ".join(f"{column} = %s" for column in changed)
                params = [data["new"] for data in changed.values()]
                params.extend([guest_id, family_code])
                cur.execute(
                    f"UPDATE public.guests SET {set_clause} WHERE id = %s AND family_id = %s",
                    params,
                )

                log_family_id = updates.get("family_id", current.get("family_id"))
                log_entries = [
                    (
                        guest_id,
                        log_family_id,
                        column,
                        None if change["old"] is None else str(change["old"]),
                        None if change["new"] is None else str(change["new"]),
                        updated_by,
                    )
                    for column, change in changed.items()
                ]
                cur.executemany(
                    """
                    INSERT INTO public.guest_change_log
                        (guest_id, family_id, column_name, old_value, new_value, changed_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    log_entries,
                )
            conn.commit()
    except psycopg.Error as exc:
        abort(500, description=f"Database error: {exc.pgerror or exc.diag.message_primary}")

    return jsonify({
        "message": "Guest updated successfully.",
        "updated_fields": list(changed.keys()),
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)