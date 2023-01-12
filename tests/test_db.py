from src.fastapi_social_network.models import User, Post
from src.fastapi_social_network.security import hash_password
from .db import DB_HOLDER


class TestSelf:
    """
    Simple sanity checks that test the test suite itself
    """
    def test_init_db_empty_populate(self, get_test_db):
        """
        Test that initial test db is empty, and add some data
        :param get_test_db:
        :return:
        """
        db = get_test_db
        users = db.query(User).all()
        assert len(users) == 0
        db.add(User(
            alias="user",
            email="user@mail",
            hashed_password=hash_password("pass")
        ))
        db.commit()
        users = db.query(User).all()
        assert len(users) == 1

    def test_persist_reset(self, get_test_db):
        """
        test that data from previous test persisted and reset the db
        :param get_test_db:
        :return:
        """
        db = get_test_db
        users = db.query(User).all()
        assert len(users) == 1
        DB_HOLDER.reset()
        users = db.query(User).all()
        assert len(users) == 0

    def test_reset_success(self, get_test_db):
        """
        Test that the table is still empty, and add extra values before scope reset test
        :param get_test_db:
        :return:
        """
        db = get_test_db
        users = db.query(User).all()
        assert len(users) == 0


class TestSelfExtra:
    """
    Separate class for extra self check
    """
    def test_db_post(self, get_test_db):
        """
        Check that DB is reset in new test class
        :param get_test_db:
        :return:
        """
        db = get_test_db
        users = db.query(User).all()
        assert len(users) == 0
        db.add(User(
            alias="user",
            email="user@mail",
            hashed_password=hash_password("pass")
        ))
        db.commit()
        users = db.query(User).all()
        assert len(users) == 1


class TestDB:
    def test_prepare(self, get_test_db):
        db = get_test_db
        users = db.query(User).all()
        assert len(users) == 0
        posts = db.query(Post).all()
        assert len(posts) == 0
        for i in range(1, 11):
            user = User(
                alias=f"test_user_{i}",
                email=f"test_user_{i}@mail",
                hashed_password=hash_password(f"pass{i}")
            )
            user.posts.append(
                Post(
                    body=f"First Test Post by user f{user.alias}"
                )
            )
            user.posts.append(
                Post(
                    body=f"Second Test Post by user f{user.alias}"
                )
            )
            db.add(user)
        cool_user = User(
            alias="cool_user",
            email="cool_mail",
            hashed_password=hash_password("cool_pass")
        )
        cool_user.posts.append(
            Post(
                body="Most Liked Post"
            )
        )
        cool_user.posts.append(
            Post(
                body="Most Disliked Post"
            )
        )
        db.add(cool_user)
        db.commit()
        users = db.query(User).all()
        assert len(users) == 11
        posts = db.query(Post).all()
        assert len(posts) == 22
