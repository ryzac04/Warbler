"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py

from datetime import datetime
import os
from unittest import TestCase

from models import db, User, Message, Likes

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
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data for each test."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        user = User.signup("test_name", "test_name@email.com", "test_password", None)
        id = 111
        user.id = id

        db.session.commit()

        user = User.query.get(id)

        self.user = user

    def tearDown(self):
        """Tear down test client after each test."""

        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message_model(self):
        """Does basic message model work?"""

        message = Message(
            text="test message", timestamp=datetime.utcnow(), user_id=self.user.id
        )

        db.session.add(message)
        db.session.commit()

        self.assertEqual(len(self.user.messages), 1)
        self.assertEqual(self.user.messages[0].text, "test message")

    def test_message_likes(self):
        """Do liked messages work properly?"""

        message1 = Message(
            text="test message1", timestamp=datetime.utcnow(), user_id=self.user.id
        )

        message2 = Message(
            text="test message2", timestamp=datetime.utcnow(), user_id=self.user.id
        )

        user = User.signup("test_name2", "test2_name@email.com", "test_password", None)
        id = 222
        user.id = id

        db.session.add_all([message1, message2, user])
        db.session.commit()

        user.likes.append(message2)
        db.session.commit()

        likes = Likes.query.filter(Likes.user_id == user.id).all()
        self.assertEqual(len(likes), 1)
        self.assertEqual(likes[0].message_id, message2.id)
