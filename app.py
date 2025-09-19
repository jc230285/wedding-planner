from __future__ import annotations

import os
import json
import re
from datetime import datetime
from uuid import UUID
from typing import Any, Dict, Iterable, List

import requests
from dotenv import load_dotenv
from flask import Flask, abort, jsonify, render_template, request, url_for
import psycopg
from psycopg.rows import dict_row

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

from utils.db import normalize_database_url
from utils.entertainment_cache import get_cached_posts, get_cached_events

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
    "stag_ideas",
    "hen_ideas",
    "friday_stay_preference",
    "saturday_stay_preference",
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
    """Get Instagram posts with caching (max once per day)"""
    posts = get_cached_posts()
    return jsonify({"data": posts})


@app.get("/api/entertainment/events")
def get_facebook_events():
    """Get Facebook events with caching (max once per day)"""
    events = get_cached_events()
    return jsonify({"data": events})


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


@app.post("/api/family/stag")
def update_family_stag():
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
                    "SELECT id, family_id, stag FROM public.guests WHERE upper(family_id) = %s AND stag IS NOT NULL",
                    (family_code,),
                )
                rows = cur.fetchall()
                if not rows:
                    abort(404, description="No guests found for that family code.")

                changed_rows = [row for row in rows if row.get("stag") != status_int]

                if changed_rows:
                    cur.execute(
                        "UPDATE public.guests SET stag = %s WHERE upper(family_id) = %s AND stag IS NOT NULL",
                        (status_int, family_code),
                    )

                    log_entries = [
                        (
                            row["id"],
                            row.get("family_id"),
                            "stag",
                            None if row.get("stag") is None else str(row.get("stag")),
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
        "message": "Stag attendance updated." if updated_count else "Stag attendance already up to date.",
        "updated_guests": updated_count,
    })


@app.post("/api/family/hen")
def update_family_hen():
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
                    "SELECT id, family_id, hen FROM public.guests WHERE upper(family_id) = %s AND hen IS NOT NULL",
                    (family_code,),
                )
                rows = cur.fetchall()
                if not rows:
                    abort(404, description="No guests found for that family code.")

                changed_rows = [row for row in rows if row.get("hen") != status_int]

                if changed_rows:
                    cur.execute(
                        "UPDATE public.guests SET hen = %s WHERE upper(family_id) = %s AND hen IS NOT NULL",
                        (status_int, family_code),
                    )

                    log_entries = [
                        (
                            row["id"],
                            row.get("family_id"),
                            "hen",
                            None if row.get("hen") is None else str(row.get("hen")),
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
        "message": "Hen attendance updated." if updated_count else "Hen attendance already up to date.",
        "updated_guests": updated_count,
    })


@app.post("/api/family/ceremony")
def update_family_ceremony():
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
                    "SELECT id, family_id, ceremony FROM public.guests WHERE upper(family_id) = %s AND ceremony IS NOT NULL",
                    (family_code,),
                )
                rows = cur.fetchall()
                if not rows:
                    abort(404, description="No guests found for that family code.")

                changed_rows = [row for row in rows if row.get("ceremony") != status_int]

                if changed_rows:
                    cur.execute(
                        "UPDATE public.guests SET ceremony = %s WHERE upper(family_id) = %s AND ceremony IS NOT NULL",
                        (status_int, family_code),
                    )

                    log_entries = [
                        (
                            row["id"],
                            row.get("family_id"),
                            "ceremony",
                            None if row.get("ceremony") is None else str(row.get("ceremony")),
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
        "message": "Ceremony attendance updated." if updated_count else "Ceremony attendance already up to date.",
        "updated_guests": updated_count,
    })


@app.post("/api/family/wedding-meal")
def update_family_wedding_meal():
    payload = request.get_json(silent=True)
    if payload is None or not isinstance(payload, dict):
        abort(400, description="Request must contain a JSON object.")

    family_code_raw = payload.get("family_code") or payload.get("family_id")
    guest_id_raw = payload.get("guest_id")
    meal_preference_raw = payload.get("meal_preference")
    updated_by = payload.get("updated_by")

    if family_code_raw is None or str(family_code_raw).strip() == "":
        abort(400, description="Family code is required.")

    if guest_id_raw is None or str(guest_id_raw).strip() == "":
        abort(400, description="Guest ID is required.")

    try:
        meal_preference_int = int(meal_preference_raw)
    except (TypeError, ValueError):
        abort(400, description="Meal preference must be an integer.")

    if meal_preference_int not in {3, 4, 5}:
        abort(400, description="Meal preference must be 3 (Vegetarian), 4 (Fish), or 5 (Beef).")

    family_code = str(family_code_raw).strip().upper()
    guest_id = str(guest_id_raw).strip()

    try:
        with psycopg.connect(_require_database_url(), row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # First verify the guest belongs to the family
                cur.execute(
                    "SELECT id, family_id, wedding_meal, name FROM public.guests WHERE id = %s AND upper(family_id) = %s",
                    (guest_id, family_code),
                )
                guest_row = cur.fetchone()
                if not guest_row:
                    abort(404, description="Guest not found in that family.")

                old_meal_preference = guest_row.get("wedding_meal")

                # Only update if the meal preference has changed
                if old_meal_preference != meal_preference_int:
                    cur.execute(
                        "UPDATE public.guests SET wedding_meal = %s WHERE id = %s",
                        (meal_preference_int, guest_id),
                    )

                    # Log the change
                    cur.execute(
                        """
                        INSERT INTO public.guest_change_log
                            (guest_id, family_id, column_name, old_value, new_value, changed_by)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            guest_id,
                            guest_row.get("family_id"),
                            "wedding_meal",
                            None if old_meal_preference is None else str(old_meal_preference),
                            str(meal_preference_int),
                            updated_by,
                        ),
                    )
                    updated_count = 1
                else:
                    updated_count = 0
            conn.commit()
    except psycopg.Error as exc:
        abort(500, description=f"Database error: {exc}")

    return jsonify({
        "message": "Wedding meal preference updated." if updated_count else "Wedding meal preference already up to date.",
        "updated_guests": updated_count,
        "guest_name": guest_row.get("name") if guest_row else None,
    })


@app.post("/api/family/stag-individual")
def update_individual_stag():
    payload = request.get_json(silent=True)
    if payload is None or not isinstance(payload, dict):
        abort(400, description="Request must contain a JSON object.")

    family_code_raw = payload.get("family_code") or payload.get("family_id")
    guest_id_raw = payload.get("guest_id")
    stag_status_raw = payload.get("stag_status")
    updated_by = payload.get("updated_by")

    if family_code_raw is None or str(family_code_raw).strip() == "":
        abort(400, description="Family code is required.")

    if guest_id_raw is None or str(guest_id_raw).strip() == "":
        abort(400, description="Guest ID is required.")

    try:
        stag_status_int = int(stag_status_raw)
    except (TypeError, ValueError):
        abort(400, description="Stag status must be an integer.")

    if stag_status_int not in {0, 1}:
        abort(400, description="Stag status must be 0 (not attending) or 1 (attending).")

    family_code = str(family_code_raw).strip().upper()
    guest_id = str(guest_id_raw).strip()

    try:
        with psycopg.connect(_require_database_url(), row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # First verify the guest belongs to the family and is invited to stag
                cur.execute(
                    "SELECT id, family_id, stag, name FROM public.guests WHERE id = %s AND upper(family_id) = %s AND stag IS NOT NULL",
                    (guest_id, family_code),
                )
                guest_row = cur.fetchone()
                if not guest_row:
                    abort(404, description="Guest not found in that family or not invited to stag.")

                old_stag_status = guest_row.get("stag")

                # Only update if the stag status has changed
                if old_stag_status != stag_status_int:
                    cur.execute(
                        "UPDATE public.guests SET stag = %s WHERE id = %s",
                        (stag_status_int, guest_id),
                    )

                    # Log the change
                    cur.execute(
                        """
                        INSERT INTO public.guest_change_log
                            (guest_id, family_id, column_name, old_value, new_value, changed_by)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            guest_id,
                            guest_row.get("family_id"),
                            "stag",
                            None if old_stag_status is None else str(old_stag_status),
                            str(stag_status_int),
                            updated_by,
                        ),
                    )
                    updated_count = 1
                else:
                    updated_count = 0
            conn.commit()
    except psycopg.Error as exc:
        abort(500, description=f"Database error: {exc}")

    return jsonify({
        "message": "Stag attendance updated." if updated_count else "Stag attendance already up to date.",
        "updated_guests": updated_count,
        "guest_name": guest_row.get("name") if guest_row else None,
    })


@app.post("/api/family/hen-individual")
def update_individual_hen():
    payload = request.get_json(silent=True)
    if payload is None or not isinstance(payload, dict):
        abort(400, description="Request must contain a JSON object.")

    family_code_raw = payload.get("family_code") or payload.get("family_id")
    guest_id_raw = payload.get("guest_id")
    hen_status_raw = payload.get("hen_status")
    updated_by = payload.get("updated_by")

    if family_code_raw is None or str(family_code_raw).strip() == "":
        abort(400, description="Family code is required.")

    if guest_id_raw is None or str(guest_id_raw).strip() == "":
        abort(400, description="Guest ID is required.")

    try:
        hen_status_int = int(hen_status_raw)
    except (TypeError, ValueError):
        abort(400, description="Hen status must be an integer.")

    if hen_status_int not in {0, 1}:
        abort(400, description="Hen status must be 0 (not attending) or 1 (attending).")

    family_code = str(family_code_raw).strip().upper()
    guest_id = str(guest_id_raw).strip()

    try:
        with psycopg.connect(_require_database_url(), row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # First verify the guest belongs to the family and is invited to hen
                cur.execute(
                    "SELECT id, family_id, hen, name FROM public.guests WHERE id = %s AND upper(family_id) = %s AND hen IS NOT NULL",
                    (guest_id, family_code),
                )
                guest_row = cur.fetchone()
                if not guest_row:
                    abort(404, description="Guest not found in that family or not invited to hen.")

                old_hen_status = guest_row.get("hen")

                # Only update if the hen status has changed
                if old_hen_status != hen_status_int:
                    cur.execute(
                        "UPDATE public.guests SET hen = %s WHERE id = %s",
                        (hen_status_int, guest_id),
                    )

                    # Log the change
                    cur.execute(
                        """
                        INSERT INTO public.guest_change_log
                            (guest_id, family_id, column_name, old_value, new_value, changed_by)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            guest_id,
                            guest_row.get("family_id"),
                            "hen",
                            None if old_hen_status is None else str(old_hen_status),
                            str(hen_status_int),
                            updated_by,
                        ),
                    )
                    updated_count = 1
                else:
                    updated_count = 0
            conn.commit()
    except psycopg.Error as exc:
        abort(500, description=f"Database error: {exc}")

    return jsonify({
        "message": "Hen attendance updated." if updated_count else "Hen attendance already up to date.",
        "updated_guests": updated_count,
        "guest_name": guest_row.get("name") if guest_row else None,
    })


@app.post("/api/family/ceremony-individual")
def update_individual_ceremony():
    payload = request.get_json(silent=True)
    if payload is None or not isinstance(payload, dict):
        abort(400, description="Request must contain a JSON object.")

    family_code_raw = payload.get("family_code") or payload.get("family_id")
    guest_id_raw = payload.get("guest_id")
    ceremony_status_raw = payload.get("ceremony_status")
    updated_by = payload.get("updated_by")

    if family_code_raw is None or str(family_code_raw).strip() == "":
        abort(400, description="Family code is required.")

    if guest_id_raw is None or str(guest_id_raw).strip() == "":
        abort(400, description="Guest ID is required.")

    try:
        ceremony_status_int = int(ceremony_status_raw)
    except (TypeError, ValueError):
        abort(400, description="Ceremony status must be an integer.")

    if ceremony_status_int not in {0, 1}:
        abort(400, description="Ceremony status must be 0 (not attending) or 1 (attending).")

    family_code = str(family_code_raw).strip().upper()
    guest_id = str(guest_id_raw).strip()

    try:
        with psycopg.connect(_require_database_url(), row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # First verify the guest belongs to the family and is invited to ceremony
                cur.execute(
                    "SELECT id, family_id, ceremony, name FROM public.guests WHERE id = %s AND upper(family_id) = %s AND ceremony IS NOT NULL",
                    (guest_id, family_code),
                )
                guest_row = cur.fetchone()
                if not guest_row:
                    abort(404, description="Guest not found in that family or not invited to ceremony.")

                old_ceremony_status = guest_row.get("ceremony")

                # Only update if the ceremony status has changed
                if old_ceremony_status != ceremony_status_int:
                    cur.execute(
                        "UPDATE public.guests SET ceremony = %s WHERE id = %s",
                        (ceremony_status_int, guest_id),
                    )

                    # Log the change
                    cur.execute(
                        """
                        INSERT INTO public.guest_change_log
                            (guest_id, family_id, column_name, old_value, new_value, changed_by)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            guest_id,
                            guest_row.get("family_id"),
                            "ceremony",
                            None if old_ceremony_status is None else str(old_ceremony_status),
                            str(ceremony_status_int),
                            updated_by,
                        ),
                    )
                    updated_count = 1
                else:
                    updated_count = 0
            conn.commit()
    except psycopg.Error as exc:
        abort(500, description=f"Database error: {exc}")

    return jsonify({
        "message": "Ceremony attendance updated." if updated_count else "Ceremony attendance already up to date.",
        "updated_guests": updated_count,
        "guest_name": guest_row.get("name") if guest_row else None,
    })


@app.post("/api/family/stag-ideas")
def update_family_stag_ideas():
    payload = request.get_json(silent=True)
    if payload is None or not isinstance(payload, dict):
        abort(400, description="Request must contain a JSON object.")

    family_code_raw = payload.get("family_code") or payload.get("family_id")
    ideas = payload.get("ideas")
    updated_by = payload.get("updated_by")

    if family_code_raw is None or str(family_code_raw).strip() == "":
        abort(400, description="Family code is required.")

    if ideas is None:
        abort(400, description="Ideas content is required.")

    family_code = str(family_code_raw).strip().upper()

    try:
        with psycopg.connect(_require_database_url(), row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # Check if any guests exist for this family
                cur.execute(
                    "SELECT id FROM public.guests WHERE upper(family_id) = %s",
                    (family_code,),
                )
                rows = cur.fetchall()
                if not rows:
                    abort(404, description="No guests found for that family code.")

                # Update stag_ideas for all guests in the family
                cur.execute(
                    "UPDATE public.guests SET stag_ideas = %s WHERE upper(family_id) = %s",
                    (ideas, family_code),
                )

                # Log the change (we'll log it for the first guest as a representative)
                if rows:
                    log_entries = [(
                        rows[0]["id"],
                        family_code,
                        "stag_ideas",
                        None,  # We don't track old value for ideas
                        ideas,
                        updated_by,
                    )]
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
        abort(500, description=f"Database error: {exc}")

    return jsonify({
        "message": "Stag ideas saved successfully.",
    })


@app.post("/api/family/hen-ideas")
def update_family_hen_ideas():
    payload = request.get_json(silent=True)
    if payload is None or not isinstance(payload, dict):
        abort(400, description="Request must contain a JSON object.")

    family_code_raw = payload.get("family_code") or payload.get("family_id")
    ideas = payload.get("ideas")
    updated_by = payload.get("updated_by")

    if family_code_raw is None or str(family_code_raw).strip() == "":
        abort(400, description="Family code is required.")

    if ideas is None:
        abort(400, description="Ideas content is required.")

    family_code = str(family_code_raw).strip().upper()

    try:
        with psycopg.connect(_require_database_url(), row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # Check if any guests exist for this family
                cur.execute(
                    "SELECT id FROM public.guests WHERE upper(family_id) = %s",
                    (family_code,),
                )
                rows = cur.fetchall()
                if not rows:
                    abort(404, description="No guests found for that family code.")

                # Update hen_ideas for all guests in the family
                cur.execute(
                    "UPDATE public.guests SET hen_ideas = %s WHERE upper(family_id) = %s",
                    (ideas, family_code),
                )

                # Log the change (we'll log it for the first guest as a representative)
                if rows:
                    log_entries = [(
                        rows[0]["id"],
                        family_code,
                        "hen_ideas",
                        None,  # We don't track old value for ideas
                        ideas,
                        updated_by,
                    )]
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
        abort(500, description=f"Database error: {exc}")

    return jsonify({
        "message": "Hen ideas saved successfully.",
    })


@app.post("/api/family/music-requests")
def update_family_music_requests():
    payload = request.get_json(silent=True)
    if payload is None or not isinstance(payload, dict):
        abort(400, description="Request must contain a JSON object.")

    family_code_raw = payload.get("family_code") or payload.get("family_id")
    requests_text = payload.get("requests")
    updated_by = payload.get("updated_by")

    if family_code_raw is None or str(family_code_raw).strip() == "":
        abort(400, description="Family code is required.")

    if requests_text is None:
        abort(400, description="Requests content is required.")

    family_code = str(family_code_raw).strip().upper()

    try:
        with psycopg.connect(_require_database_url(), row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # Check if any guests exist for this family
                cur.execute(
                    "SELECT id FROM public.guests WHERE upper(family_id) = %s ORDER BY id LIMIT 1",
                    (family_code,),
                )
                first_guest = cur.fetchone()
                if not first_guest:
                    abort(404, description="No guests found for that family code.")

                # Update music_requests for the first guest only
                cur.execute(
                    "UPDATE public.guests SET music_requests = %s WHERE id = %s",
                    (requests_text, first_guest["id"]),
                )

                # Log the change
                cur.execute(
                    """
                    INSERT INTO public.guest_change_log
                        (guest_id, family_id, column_name, old_value, new_value, changed_by)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        first_guest["id"],
                        family_code,
                        "music_requests",
                        None,  # We don't track old value for requests
                        requests_text,
                        updated_by,
                    ),
                )
            conn.commit()
    except psycopg.Error as exc:
        abort(500, description=f"Database error: {exc}")

    return jsonify({
        "message": "Music requests saved successfully.",
    })


@app.post("/api/family/friday-stay")
def update_family_friday_stay():
    """Update Friday stay preference for all guests in a family"""
    payload = request.get_json(silent=True)
    if payload is None or not isinstance(payload, dict):
        abort(400, description="Request must contain a JSON object.")

    family_code = payload.get("family_code")
    stay_option = payload.get("stay_option")  # 2 for New Place Hotel, 3 for Quob Park Old House Hotel & Spa
    updated_by = payload.get("updated_by", "family")

    if not family_code or stay_option is None:
        abort(400, description="Both 'family_code' and 'stay_option' are required.")

    if stay_option not in [2, 3]:
        abort(400, description="Stay option must be 2 (New Place Hotel) or 3 (Quob Park Old House Hotel & Spa).")

    try:
        with psycopg.connect(_require_database_url(), row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # Update all guests in the family
                cur.execute(
                    "UPDATE public.guests SET friday_stay_preference = %s WHERE family_id = %s",
                    (stay_option, family_code)
                )

                # Log the change for each guest
                cur.execute(
                    "SELECT id FROM public.guests WHERE family_id = %s",
                    (family_code,)
                )
                guest_ids = [row["id"] for row in cur.fetchall()]

                for guest_id in guest_ids:
                    cur.execute(
                        """
                        INSERT INTO public.guest_change_log (guest_id, family_id, column_name, old_value, new_value, changed_by, changed_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                        """,
                        (
                            guest_id,
                            family_code,
                            "friday_stay_preference",
                            None,  # We don't track old value for stay preferences
                            stay_option,
                            updated_by,
                        ),
                    )
            conn.commit()
    except psycopg.Error as exc:
        abort(500, description=f"Database error: {exc}")

    stay_options = {
        2: "New Place Hotel",
        3: "Quob Park Old House Hotel & Spa"
    }

    return jsonify({
        "message": f"Friday stay preference updated to {stay_options[stay_option]} for all family members.",
    })


@app.post("/api/family/saturday-stay")
def update_family_saturday_stay():
    """Update Saturday stay preference for all guests in a family"""
    payload = request.get_json(silent=True)
    if payload is None or not isinstance(payload, dict):
        abort(400, description="Request must contain a JSON object.")

    family_code = payload.get("family_code")
    stay_option = payload.get("stay_option")  # 2 for New Place Hotel, 3 for Quob Park Old House Hotel & Spa, 4 for Quob Park Estate
    updated_by = payload.get("updated_by", "family")

    if not family_code or stay_option is None:
        abort(400, description="Both 'family_code' and 'stay_option' are required.")

    if stay_option not in [2, 3, 4]:
        abort(400, description="Stay option must be 2 (New Place Hotel), 3 (Quob Park Old House Hotel & Spa), or 4 (Quob Park Estate).")

    try:
        with psycopg.connect(_require_database_url(), row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                # Update all guests in the family
                cur.execute(
                    "UPDATE public.guests SET saturday_stay_preference = %s WHERE family_id = %s",
                    (stay_option, family_code)
                )

                # Log the change for each guest
                cur.execute(
                    "SELECT id FROM public.guests WHERE family_id = %s",
                    (family_code,)
                )
                guest_ids = [row["id"] for row in cur.fetchall()]

                for guest_id in guest_ids:
                    cur.execute(
                        """
                        INSERT INTO public.guest_change_log (guest_id, family_id, column_name, old_value, new_value, changed_by, changed_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                        """,
                        (
                            guest_id,
                            family_code,
                            "saturday_stay_preference",
                            None,  # We don't track old value for stay preferences
                            stay_option,
                            updated_by,
                        ),
                    )
            conn.commit()
    except psycopg.Error as exc:
        abort(500, description=f"Database error: {exc}")

    stay_options = {
        2: "New Place Hotel",
        3: "Quob Park Old House Hotel & Spa",
        4: "Quob Park Estate"
    }

    return jsonify({
        "message": f"Saturday stay preference updated to {stay_options[stay_option]} for all family members.",
    })


@app.get("/api/ai/<string:name>")
def get_ai_suggestions(name):
    """Get AI suggestions by name."""
    try:
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id, ai, name FROM public.ai WHERE name = %s ORDER BY id",
                    (name,)
                )
                rows = cur.fetchall()
                
                suggestions = []
                for row in rows:
                    suggestions.append({
                        "id": row[0],
                        "ai": row[1], 
                        "name": row[2]
                    })
                
                return jsonify(suggestions)
    except psycopg.Error as exc:
        abort(500, description=f"Database error: {exc}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

