"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ["DATABASE_URL"] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Create test clients, add sample data for each test."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        user1 = User.signup(
            "test_name1", "test_name1@email.com", "test_password1", None
        )
        id1 = 111
        user1.id = id1

        user2 = User.signup(
            "test_name2", "test_name2@email.com", "test_password2", None
        )
        id2 = 222
        user2.id = id2

        db.session.commit()

        user1 = User.query.get(id1)
        user2 = User.query.get(id2)

        self.user1 = user1
        self.user2 = user2

    def tearDown(self):
        """Tear down test clients after each test."""

        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic user model work?"""

        u = User(email="test@test.com", username="testuser", password="HASHED_PASSWORD")

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_repr(self):
        """Does __repr__ method work?"""

        u1 = self.user1.__repr__()
        self.assertEqual(u1, "<User #111: test_name1, test_name1@email.com>")

    def test_is_followed_by(self):
        """Does is_followed_by method work?"""

        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user2.is_followed_by(self.user1))
        self.assertFalse(self.user1.is_followed_by(self.user2))

    def test_is_following(self):
        """Does is_following method work?"""

        self.user1.following.append(self.user2)
        db.session.commit()

        self.assertTrue(self.user1.is_following(self.user2))
        self.assertFalse(self.user2.is_following(self.user1))

    def test_signup(self):
        """Does signup method work?"""

        user1 = User.signup("testname1", "testname1@email.com", "test_password", None)
        db.session.commit()

        self.assertEqual(user1.username, "testname1")
        self.assertEqual(user1.email, "testname1@email.com")
        self.assertTrue(user1.password.startswith("$2b$"))
        self.assertEqual(user1.image_url, "/static/images/default-pic.png")

    def test_authenticate(self):
        """Does authenticate method work?"""

        user1 = User.signup("testname1", "testname1@email.com", "test_password", None)
        db.session.commit()
        user1_account = User.authenticate("testname1", "test_password")

        self.assertEqual(user1, user1_account)

    def test_authenticate_invalid_username(self):
        """Does authentication fail when given an invalid username?"""

        user1 = User.signup("testname1", "testname1@email.com", "test_password", None)
        db.session.commit()
        user1_account = User.authenticate("testname2", "test_password")

        self.assertNotEqual(user1, user1_account)

    def test_authenticate_invalid_password(self):
        """Does authentication fail when given an invalid password?"""

        user1 = User.signup("testname1", "testname1@email.com", "test_password", None)
        db.session.commit()
        user1_account = User.authenticate("testname1", "test_password2")

        self.assertNotEqual(user1, user1_account)
