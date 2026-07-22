# backend/scripts/create_admin.py
"""CLI script to seed default admin user."""

from backend.app import create_app
from backend.extensions import db
from backend.models.user import User

def create_admin():
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@attijaribank.com.tn",
                role="admin",
                full_name="Administrateur KUSOR",
                department="Direction de la Conformité",
            )
            admin.set_password("Admin123!")
            db.session.add(admin)
            db.session.commit()
            print("Default admin created: admin / Admin123!")
        else:
            print("Admin user already exists.")

if __name__ == "__main__":
    create_admin()
