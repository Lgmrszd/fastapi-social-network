from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fastapi_social_network.database import Base


class DbHolder:
    SQLALCHEMY_DATABASE_URL = "sqlite://"
    TestSessionLocal: sessionmaker

    def __init__(self):
        self.engine = None
        self.prepare_db()

    def reset(self):
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

    def prepare_db(self):
        self.engine = create_engine(
            self.SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, echo=True
        )
        self.TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)


DB_HOLDER = DbHolder()
