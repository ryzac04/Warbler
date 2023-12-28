"""Message view tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py

from datetime import datetime

import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ["DATABASE_URL"] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config["WTF_CSRF_ENABLED"] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(
            username="test_name",
            email="test_name@email.com",
            password="test_password",
            image_url=None,
        )
        id = 111
        self.testuser.id = id

        db.session.commit()

    def tearDown(self):
        """Tear down test clients after each test."""

        res = super().tearDown()
        db.session.rollback()
        return res

    def test_add_message(self):
        """Can user add own message while logged in?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_view_message(self):
        """Can user view messages while logged in?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            message = Message(
                id=111,
                text="test message",
                timestamp=datetime.utcnow(),
                user_id=self.testuser.id,
            )
            db.session.add(message)
            db.session.commit()

            resp = c.get(f"/users/{self.testuser.id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("test message", html)

    def test_delete_message(self):
        """Can user delete own message while logged in?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            message = Message(
                id=111,
                text="test message",
                timestamp=datetime.utcnow(),
                user_id=self.testuser.id,
            )
            db.session.add(message)
            db.session.commit()

            resp = c.post(f"/messages/{message.id}/delete", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("test message", html)

    def test_add_message_no_sess(self):
        """Is user prohibited from adding messages while not logged in?"""

        with self.client as c:
            resp = c.post(
                "/messages/new", data={"text": "Test message"}, follow_redirects=True
            )
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_delete_message_no_sess(self):
        """Is user prohibited from deleting messages while not logged in?"""

        with self.client as c:
            message = Message(
                id=111,
                text="test message",
                timestamp=datetime.utcnow(),
                user_id=self.testuser.id,
            )

            resp = c.post(f"/messages/{message.id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_add_message_other_user(self):
        """Is user prohibited from adding a message as another user while logged in?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 222

            resp = c.post("/messages/new", data={"text": "Test message"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

    def test_delete_message_other_user(self):
        """Is user prohibited from deleting a message as another user while logged in?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 222

            message = Message(
                id=111,
                text="test message",
                timestamp=datetime.utcnow(),
                user_id=self.testuser.id,
            )

            resp = c.post(f"/messages/{message.id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            

            
