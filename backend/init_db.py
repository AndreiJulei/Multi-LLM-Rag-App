from app.db.database import db
from app.db import models
from app.core import auth

def init_admin():
    # 1. Get a database session
    session = next(db.get_db())
    
    # 2. Check if the admin already exists
    admin_email = "user@example.com"
    existing_user = session.query(models.User).filter(models.User.email == admin_email).first()
    
    if not existing_user:
        print(f"Creating admin user: {admin_email}...")
        # 3. Hash the password "stringst"
        hashed_password = auth.get_password_hash("stringst")
        
        # 4. Create the admin object
        new_admin = models.User(
            email=admin_email,
            hashed_password=hashed_password,
            is_admin=True #This makes them an admin
        )
        
        session.add(new_admin)
        session.commit()
        print("Admin user created successfully!")
    else:
        print("Admin user already exists.")

if __name__ == "__main__":
    # Create the tables if they don't exist
    db.create_tables()
    init_admin()