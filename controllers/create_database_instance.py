from flask import current_app as app
from controllers.database import db
from controllers.models import User, parking_lot, parking_spot
def create_tables():
    with app.app_context():
        db.create_all()
        is_admin = User.query.filter_by(username='admin').first()

        if not is_admin:
            admin = User(username='admin',email='admin@admin.com',passhash='admin',name='admin',is_admin=True)
            db.session.add(admin)
        db.session.commit()  