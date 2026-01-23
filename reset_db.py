from app.database import engine, Base
from app.models import *  # Import all models to ensure metadata is populated


def reset_database():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped.")


if __name__ == "__main__":
    reset_database()
