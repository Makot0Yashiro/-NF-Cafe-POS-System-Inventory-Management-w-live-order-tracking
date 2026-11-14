from datetime import datetime, timezone

from flask import Blueprint, abort, flash, jsonify, redirect, render_template, request, session, url_for

from ..auth_utils import check_csrf, login_required
from ..db import get_db
from .admin import admin_required

bp = Blueprint("notifications", __name__)


def _rows(user_id, limit=100):
    return get_db().execute(
        "SELECT id,title,body,kind,order_id,created_at,read_at FROM notifications "
        "WHERE user_id=? ORDER BY id DESC LIMIT ?",
        (user_id, limit)).fetchall()


@bp.get("/notifications")
@login_required
def page():
    rows = _rows(session["user_id"])
    return render_template("user/notifications.html", notifications=rows)


@bp.get("/admin/notifications")
@admin_required
def admin_page():
    history = get_db().execute(
        "SELECT title,body,kind,created_at,COUNT(*) AS recipients FROM notifications "
        "WHERE order_id IS NULL GROUP BY title,body,kind,created_at ORDER BY created_at DESC LIMIT 50"
    ).fetchall()
    order_history = get_db().execute(
        "SELECT id,title,body,kind,order_id,created_at,read_at FROM notifications "
        "WHERE user_id=? AND order_id IS NOT NULL ORDER BY id DESC LIMIT 100",
        (session["user_id"],)).fetchall()
    return render_template("admin/notifications.html", history=history, order_history=order_history)


@bp.post("/admin/notifications")
@admin_required
def broadcast():
    check_csrf()
    title = str(request.form.get("title", "")).strip()
    body = str(request.form.get("body", "")).strip()
    kind = request.form.get("kind")
    if not title or len(title) > 120 or not body or len(body) > 500:
        flash("Enter a title (up to 120 characters) and a message (up to 500 characters).")
        return redirect(url_for("notifications.admin_page"))
    if kind not in ("promo", "menu", "announcement"):
        flash("Choose a valid notification type.")
        return redirect(url_for("notifications.admin_page"))
    db = get_db()
    created_at = datetime.now(timezone.utc).isoformat()
    cur = db.execute(
        "INSERT INTO notifications(user_id,title,body,kind,created_at) "
        "SELECT id,?,?,?,? FROM users WHERE is_admin=0",
        (title, body, kind, created_at))
    db.commit()
    flash(f"Notification sent to {cur.rowcount} customers.")
    return redirect(url_for("notifications.admin_page"))


@bp.get("/api/notifications")
@login_required
def list_notifications():
    rows = _rows(session["user_id"], 50)
    unread = get_db().execute(
        "SELECT COUNT(*) AS n FROM notifications WHERE user_id=? AND read_at IS NULL",
        (session["user_id"],)).fetchone()["n"]
    return jsonify(unread=unread, notifications=rows)


@bp.get("/admin/api/notifications")
@admin_required
def admin_notification_count():
    unread = get_db().execute(
        "SELECT COUNT(*) AS n FROM notifications WHERE user_id=? AND kind='order' AND read_at IS NULL",
        (session["user_id"],)).fetchone()["n"]
    return jsonify(unread=unread)


@bp.post("/admin/api/notifications/<int:notification_id>/read")
@admin_required
def mark_admin_notification_read(notification_id):
    check_csrf()
    db = get_db()
    cur = db.execute(
        "UPDATE notifications SET read_at=? WHERE id=? AND user_id=? AND kind='order' AND read_at IS NULL",
        (datetime.now(timezone.utc).isoformat(), notification_id, session["user_id"]))
    db.commit()
    if cur.rowcount == 0:
        exists = db.execute(
            "SELECT 1 FROM notifications WHERE id=? AND user_id=? AND kind='order'",
            (notification_id, session["user_id"])).fetchone()
        if not exists:
            abort(404)
    return jsonify(read=True)


@bp.post("/api/notifications/<int:notification_id>/read")
@login_required
def mark_read(notification_id):
    check_csrf()
    db = get_db()
    cur = db.execute(
        "UPDATE notifications SET read_at=? WHERE id=? AND user_id=? AND read_at IS NULL",
        (datetime.now(timezone.utc).isoformat(), notification_id, session["user_id"]))
    db.commit()
    if cur.rowcount == 0:
        exists = db.execute("SELECT 1 FROM notifications WHERE id=? AND user_id=?",
                            (notification_id, session["user_id"])).fetchone()
        if not exists:
            abort(404)
    return jsonify(read=True)
