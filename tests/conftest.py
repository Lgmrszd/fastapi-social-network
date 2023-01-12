import pytest
from .db import DB_HOLDER


@pytest.fixture(scope="class")
def get_test_db():
    """
    Fixture that prepares clear test database
    :return:
    """
    db = DB_HOLDER.TestSessionLocal()
    try:
        DB_HOLDER.reset()
        yield db
    finally:
        print("Closing the db!")
        db.close()

