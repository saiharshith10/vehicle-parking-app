from flask import current_app as app
from controllers.database import db
from controllers.models import User, parking_lot, parking_spot
from werkzeug.security import generate_password_hash,check_password_hash
def create_tables():
    with app.app_context():
        db.create_all()
        admin = User.query.filter_by(id=1).first()

        if not admin:
            admin = User(username='admin',email='admin@admin.com',passhash=generate_password_hash('admin'),name='admin', address='admin', pincode='admin', is_admin=True)
            db.session.add(admin)
            db.session.commit()
    return "Tables created successfully and admin user added if it didn't exist." 