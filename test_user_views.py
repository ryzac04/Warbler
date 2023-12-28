"""User view tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py

from datetime import datetime

import os
from unittest import TestCase

from models import db, connect_db, Message, User, Follows, Likes

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


class UserViewTestCase(TestCase):
    """Test views for user(s)."""

    def setUp(self):
        """Create test clients and messages, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(
            username="test_name",
            email="test_name@email.com",
            password="test_password",
            image_url=None,
        )
        id = 111
        self.testuser.id = id

        self.user2 = User.signup(
            username="user2",
            email="user2@email.com",
            password="test_password2",
            image_url=None,
        )
        user2_id = 222
        self.user2.id = user2_id

        self.user3 = User.signup(
            username="user3",
            email="user3@email.com",
            password="test_password3",
            image_url=None,
        )
        user3_id = 333
        self.user3.id = user3_id

        self.user4 = User.signup(
            username="user4",
            email="user4@email.com",
            password="test_password4",
            image_url=None,
        )
        user4_id = 444
        self.user4.id = user4_id

        self.message1 = Message(
            text="test message1", timestamp=datetime.utcnow(), user_id=self.testuser.id
        )

        self.message2 = Message(
            text="test message2", timestamp=datetime.utcnow(), user_id=self.user2.id
        )

        db.session.add_all(
            [
                self.testuser,
                self.user2,
                self.user3,
                self.user4,
                self.message1,
                self.message2,
            ]
        )
        db.session.commit()

    def tearDown(self):
        """Tear down test clients after each test."""

        res = super().tearDown()
        db.session.rollback()
        return res

    def setup_followers(self):
        """Following relationships set up for use in other tests."""

        follower1 = Follows(
            user_being_followed_id=self.user2.id, user_following_id=self.testuser.id
        )
        follower2 = Follows(
            user_being_followed_id=self.user3.id, user_following_id=self.testuser.id
        )
        follower3 = Follows(
            user_being_followed_id=self.testuser.id, user_following_id=self.user2.id
        )

        db.session.add_all([follower1, follower2, follower3])
        db.session.commit()

    def setup_likes(self):
        """Likes set up for use in other tests."""

        message1 = Message(
            id=1234,
            text="test message1",
            timestamp=datetime.utcnow(),
            user_id=self.testuser.id,
        )
        message2 = Message(
            text="test message2", timestamp=datetime.utcnow(), user_id=self.testuser.id
        )
        db.session.add_all([message1, message2])
        db.session.commit()

        like = Likes(user_id=self.testuser.id, message_id=1234)
        db.session.add(like)
        db.session.commit()

    def test_login(self):
        """Test login screen."""

        with self.client as c:
            resp = c.get("/login")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Welcome back.", html)

    def test_home(self):
        """Does home page displays correct information when logged in?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get("/")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(f"{self.testuser.username}", html)

    def test_users_index(self):
        """Does users index displays correct information?"""

        with self.client as c:
            resp = c.get("/users")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("user2", html)
            self.assertIn("user3", html)

    def test_user_profile(self):
        """Can user view profile pages?"""

        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("test_name", html)
            self.assertIn("test message1", html)
            self.assertNotIn("test message2", html)

    def test_users_search(self):
        """Does user search work?"""

        with self.client as c:
            resp = c.get("/users?q=")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("test_name", html)
            self.assertIn("user2", html)
            self.assertIn("user3", html)
            self.assertIn("user4", html)
            self.assertNotIn("test message1", html)

    def test_new_messages(self):
        """Can logged in user view page to create new message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get("/messages/new")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Add my message!", html)

    def test_following_page(self):
        """Can logged in user view other followed users?"""

        self.setup_followers()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get(f"/users/{self.testuser.id}/following")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("user2", html)
            self.assertIn("user3", html)

    def test_unauthorized_following_page(self):
        """Can user view followed users if not logged in?"""

        self.setup_followers()

        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}/following", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_followers_page(self):
        """Can logged in user view users who follow them?"""

        self.setup_followers()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get(f"/users/{self.testuser.id}/followers")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("user2", html)

    def test_unauthorized_followers_page(self):
        """Can user view followers if not logged in?"""

        self.setup_followers()

        with self.client as c:
            resp = c.get(f"/users/{self.testuser.id}/followers", follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_likes_page(self):
        """Can logged in user view liked warbles?"""

        self.setup_likes()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get(f"/users/likes/{self.testuser.id}")
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("test message1", html)

    def test_edit_profile(self):
        """Can a logged in user edit their own user profile?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            testuser = User.query.filter_by(username="test_name").first()
            self.testuser.id = testuser.id

            resp = c.post(
                f"/users/profile",
                data={
                    "username": "edited_name",
                    "email": "editedemail@email.com",
                    "image_url": None,
                    "header_image_url": None,
                    "bio": "Edited bio info",
                    "password": "test_password",
                },
                follow_redirects=True,
            )
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn("edited_name", html)
            self.assertIn("Edited bio info", html)
            self.assertNotIn("test_name", html)

    def test_unauthorized_edit_profile(self):
        """Can a user edit their own profile if not logged in?"""

        with self.client as c:
            testuser = User.query.filter_by(username="test_name").first()
            self.testuser.id = testuser.id

            resp = c.post(
                f"/users/profile",
                data={
                    "username": "edited_name",
                    "email": "editedemail@email.com",
                    "image_url": None,
                    "header_image_url": None,
                    "bio": "Edited bio info",
                    "password": "test_password",
                },
                follow_redirects=True,
            )
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn("Access unauthorized", html)
