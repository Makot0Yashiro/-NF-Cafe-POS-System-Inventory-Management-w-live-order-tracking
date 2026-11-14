def add_user_notification(db, user_id, title, body, kind="order", order_id=None, created_at=None):
    db.execute(
        "INSERT INTO notifications(user_id,title,body,kind,order_id,created_at) VALUES(?,?,?,?,?,?)",
        (user_id, title, body, kind, order_id, created_at))


def add_admin_notification(db, title, body, order_id, created_at):
    db.execute(
        "INSERT INTO notifications(user_id,title,body,kind,order_id,created_at) "
        "SELECT id,?,?, 'order',?,? FROM users WHERE is_admin=1",
        (title, body, order_id, created_at))
