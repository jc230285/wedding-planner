from __future__ import annotations

import os
from datetime import datetime
from uuid import UUID
from typing import Any, Dict, Iterable, List

import requests
from dotenv import load_dotenv
from flask import Flask, abort, jsonify, render_template, request, url_for
import psycopg
from psycopg.rows import dict_row

from utils.db import normalize_database_url

load_dotenv()

app = Flask(__name__)

DATABASE_URL_RAW = os.getenv("DATABASE_URL")
DATABASE_URL = normalize_database_url(DATABASE_URL_RAW) if DATABASE_URL_RAW else None
INSTAGRAM_USER_ID = os.getenv("INSTAGRAM_USER_ID")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")

INT_COLUMNS = {"stag", "hen", "friday_room", "ceremony", "wedding_meal", "saturday_room", "attendance_status"}
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
    "attendance_status",
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
    "attendance_status",
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
    family_code_raw = request.args.get("family_code", "")
    family_code_clean = family_code_raw.strip()
    family_code = family_code_clean.upper()

    show_rsvp_form = True
    family_code_valid = False
    family_guests = []
    all_guests = []
    guests_without_family = []
    data_error = None
    attendance_status = None
    pending_invites = False

    if family_code:
        try:
            family_guests = _fetch_guests("WHERE upper(family_id) = %s", (family_code,))
            family_code_valid = len(family_guests) > 0
            show_rsvp_form = not family_code_valid

            all_guests = _fetch_guests()
            guests_without_family = _fetch_guests("WHERE family_id IS NULL OR family_id = ''")

            if family_code_valid:
                statuses = {guest.get("attendance_status") for guest in family_guests if guest.get("attendance_status") is not None}
                if statuses:
                    pending_invites = 2 in statuses
                    responded_statuses = {status for status in statuses if status in (0, 1)}
                    if responded_statuses and len(responded_statuses) == 1 and len(statuses - responded_statuses) <= 1:
                        attendance_status = responded_statuses.pop()
        except psycopg.Error as exc:
            data_error = str(exc)
            app.logger.exception("Failed to load guest data for code %s", family_code)
            family_guests = []
            all_guests = []
            guests_without_family = []
            show_rsvp_form = True
            family_code_valid = False
            attendance_status = None
            pending_invites = False

    return render_template(
        "index.html",
        family_code=family_code,
        family_code_valid=family_code_valid,
        show_rsvp_form=show_rsvp_form,
        family_guests=family_guests,
        all_guests=all_guests,
        guests_without_family=guests_without_family,
        data_error=data_error,
        attendance_status=attendance_status,
        pending_invites=pending_invites,
    )


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


@app.get("/api/entertainment/posts")
def get_entertainment_posts():
    posts: List[Dict[str, Any]] = []
    if INSTAGRAM_USER_ID and INSTAGRAM_ACCESS_TOKEN:
        try:
            response = requests.get(
                f"https://graph.instagram.com/{INSTAGRAM_USER_ID}/media",
                params={
                    "fields": "id,caption,permalink,media_url,thumbnail_url,media_type,timestamp",
                    "access_token": INSTAGRAM_ACCESS_TOKEN,
                    "limit": 5,
                },
                timeout=8,
            )
            if response.ok:
                for item in response.json().get("data", []):
                    if item.get("media_type") not in {"IMAGE", "CAROUSEL_ALBUM", "VIDEO"}:
                        continue
                    image_url = item.get("media_url") or item.get("thumbnail_url")
                    if not image_url:
                        continue
                    caption = (item.get("caption") or "").strip()
                    if len(caption) > 140:
                        caption = caption[:137].rstrip() + "…"
                    posts.append(
                        {
                            "caption": caption,
                            "permalink": item.get("permalink"),
                            "image_url": image_url,
                            "timestamp": item.get("timestamp"),
                        }
                    )
        except requests.RequestException:
            posts = []

    if len(posts) < 3:
        fallback_image = url_for("static", filename="images/entertainment.jpg")
        posts.extend(
            [
                {
                    "caption": "Beard live highlight reel – book us for your next party!",
                    "permalink": "https://www.instagram.com/beardbanduk/",
                    "image_url": fallback_image,
                    "timestamp": None,
                },
                {
                    "caption": "Late-night DJ sets keep the dance floor packed until close.",
                    "permalink": "https://www.instagram.com/beardbanduk/",
                    "image_url": fallback_image,
                    "timestamp": None,
                },
                {
                    "caption": "Behind the scenes with the band – follow @beardbanduk for more!",
                    "permalink": "https://www.instagram.com/beardbanduk/",
                    "image_url": fallback_image,
                    "timestamp": None,
                },
            ][: 3 - len(posts)]
        )

    return jsonify({"data": posts[:3]})


@app.get("/api/guest-changes")
def get_guest_changes():
    limit = request.args.get("limit", 50, type=int)
    if limit > 100:
        limit = 100  # Cap at 100 for safety

    sql = """
        SELECT
            gcl.id,
            gcl.guest_id,
            g.name as guest_name,
            gcl.family_id,
            gcl.column_name,
            gcl.old_value,
            gcl.new_value,
            gcl.changed_by,
            gcl.changed_at
        FROM public.guest_change_log gcl
        LEFT JOIN public.guests g ON gcl.guest_id = g.id
        ORDER BY gcl.changed_at DESC
        LIMIT %s
    """

    with psycopg.connect(_require_database_url(), row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (limit,))
            rows = cur.fetchall()

    # Serialize datetime
    for row in rows:
        if isinstance(row["changed_at"], datetime):
            row["changed_at"] = row["changed_at"].isoformat()

    return jsonify({"data": rows})


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



@app.route("/api/guests/<uuid:guest_id>", methods=["PATCH"])
def update_guest_by_id(guest_id: UUID):
    guest_id_str = str(guest_id)
    payload = request.get_json(silent=True)
    if payload is None or not isinstance(payload, dict):
        abort(400, description="Request must contain a JSON object.")

    updates: Dict[str, Any] = {}
    for key, value in payload.items():
        column = FIELD_ALIASES.get(key, key)
        if column not in UPDATABLE_COLUMNS:
            abort(400, description=f"Field '{key}' cannot be updated.")
        try:
            updates[column] = _normalize_update_value(column, value)
        except ValueError as exc:
            abort(400, description=str(exc))

    if not updates:
        abort(400, description="No updatable fields were provided.")

    updated_by = payload.get("updated_by", "admin")

    try:
        with psycopg.connect(_require_database_url(), row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # Check if guest exists
                cur.execute("SELECT * FROM public.guests WHERE id = %s", (guest_id_str,))
                current = cur.fetchone()
                if current is None:
                    abort(404, description="Guest not found.")

                changed: Dict[str, Dict[str, Any]] = {}
                for column, new_value in updates.items():
                    if current.get(column) != new_value:
                        changed[column] = {"old": current.get(column), "new": new_value}

                if not changed:
                    return jsonify({"message": "No changes detected."}), 200

                # Update the guest
                set_clause = ", ".join(f"{column} = %s" for column in changed)
                params = [data["new"] for data in changed.values()]
                params.append(guest_id_str)
                cur.execute(
                    f"UPDATE public.guests SET {set_clause} WHERE id = %s",
                    params,
                )

                # Log the changes
                log_entries = [
                    (
                        guest_id_str,
                        current.get("family_id"),
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


@app.post("/api/family/attendance")
def update_family_attendance():
    payload = request.get_json(silent=True)
    if payload is None or not isinstance(payload, dict):
        abort(400, description="Request must contain a JSON object.")

    family_code_raw = payload.get("family_code") or payload.get("family_id")
    status_raw = payload.get("status")
    updated_by = payload.get("updated_by")

    if family_code_raw is None or str(family_code_raw).strip() == "":
        abort(400, description="Family code is required.")

    try:
        status_int = int(status_raw)
    except (TypeError, ValueError):
        abort(400, description="Status must be an integer.")

    if status_int not in {0, 1, 2}:
        abort(400, description="Status must be 0 (not attending), 1 (attending), or 2 (invited).")

    family_code = str(family_code_raw).strip().upper()

    try:
        with psycopg.connect(_require_database_url(), row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, family_id, attendance_status FROM public.guests WHERE upper(family_id) = %s",
                    (family_code,),
                )
                rows = cur.fetchall()
                if not rows:
                    abort(404, description="No guests found for that family code.")

                changed_rows = [row for row in rows if row.get("attendance_status") != status_int]

                if changed_rows:
                    cur.execute(
                        "UPDATE public.guests SET attendance_status = %s WHERE upper(family_id) = %s",
                        (status_int, family_code),
                    )

                    log_entries = [
                        (
                            row["id"],
                            row.get("family_id"),
                            "attendance_status",
                            None if row.get("attendance_status") is None else str(row.get("attendance_status")),
                            str(status_int),
                            updated_by,
                        )
                        for row in changed_rows
                    ]
                    cur.executemany(
                        """
                        INSERT INTO public.guest_change_log
                            (guest_id, family_id, column_name, old_value, new_value, changed_by)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        log_entries,
                    )
                    updated_count = len(changed_rows)
                else:
                    updated_count = 0
            conn.commit()
    except psycopg.Error as exc:
        abort(500, description=f"Database error: {exc}")

    return jsonify({
        "message": "Attendance updated." if updated_count else "Attendance already up to date.",
        "updated_guests": updated_count,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

