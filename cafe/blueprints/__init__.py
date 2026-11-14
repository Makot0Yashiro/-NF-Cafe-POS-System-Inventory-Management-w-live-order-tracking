def register_blueprints(app):
    from . import main, auth, account, menu, orders, admin, inventory, media, notifications
    for m in (main, auth, account, menu, orders, admin, inventory, media, notifications):
        app.register_blueprint(m.bp)
