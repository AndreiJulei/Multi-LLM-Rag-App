from app.db.database import db, Base
from app.db import models 


def reset_database():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=db.engine)

    print("Recreating tables from the latest models...")
    Base.metadata.create_all(bind=db.engine)

    print("Database reset complete.")


if __name__ == "__main__":
    reset_database()