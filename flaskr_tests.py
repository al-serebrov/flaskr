"""Test application.

There are tests intended to check that app is functioning correctly
"""

import os
import flaskr
import unittest
import tempfile
from bs4 import BeautifulSoup


class DBTestCase(unittest.TestCase):
    """DB test class."""

    def setUp(self):
        """Set the app up."""
        self.db_fd, flaskr.app.config['DATABASE'] = tempfile.mkstemp()
        flaskr.app.config['TESTING'] = True
        self.app = flaskr.app.test_client()
        with flaskr.app.app_context():
            flaskr.init_db()

    def tearDown(self):
        """Close all connections."""
        os.close(self.db_fd)
        os.unlink(flaskr.app.config['DATABASE'])

    def test_empty_db(self):
        """Test with empty database."""
        rv = self.app.get('/')
        assert b'No entries here so far' in rv.data

    def login(self, username, password):
        """Handy method to send the authentication data."""
        return self.app.post(
            '/login',
            data=dict(
                username=username,
                password=password),
            follow_redirects=True)

    def logout(self):
        """Log the admin user out."""
        return self.app.get('logout', follow_redirects=True)


class FlaskrTestCase(DBTestCase):
    """Main application test class."""

    def setUp(self):
        """Set the app up, using the DBTestCase setUp."""
        DBTestCase.setUp(self)

    def tearDown(self):
        """Tear the app down."""
        DBTestCase.tearDown(self)

    def test_login(self):
        """It is possible to login with correct credentials."""
        # with correct credentials
        rv = self.login('admin', 'default')
        assert b'You were logged in' in rv.data

    def test_logout(self):
        """It is possible to log out."""
        rv = self.logout()
        assert b'You were logged out' in rv.data

    def test_login_incorrect_user(self):
        """It is impossible to login with incorrect username."""
        rv = self.login('adminx', 'default')
        assert b'Invalid username' in rv.data

    def test_login_incorrect_pass(self):
        """It is impossible to login with incorrect pass."""
        rv = self.login('admin', 'defaultx')
        assert b'Invalid password' in rv.data

    def test_messages(self):
        """Test messages adding."""
        self.login('admin', 'default')
        rv = self.app.post(
            '/add',
            data=dict(title='<Hello>',
                      text='<strong>HTML</strong> allowed here'),
            follow_redirects=True)
        assert b'No entries here so far' not in rv.data
        assert b'&lt;Hello&gt;' in rv.data
        assert b'<strong>HTML</strong> allowed here' in rv.data

    def test_move(self):
        """Test entry move."""
        self.login('admin', 'default')
        # post the first entry
        self.app.post(
            'add',
            data=dict(title='First one',
                      text='text1'),
            follow_redirects=True)
        # post the second entry
        self.app.post(
            'add',
            data=dict(title='Second one',
                      text='text2'),
            follow_redirects=True)
        # trying  to  move the last (by sort order) entry down
        rv = self.app.post('entry=1&move=down', follow_redirects=True)
        assert b'Unable to' in rv.data
        assert b'Successfuly' not in rv.data
        # moving the first (by sort order) entry down
        rv = self.app.post('entry=2&move=down', follow_redirects=True)
        assert b'Unable to' not in rv.data
        assert b'successfuly' in rv.data
        # testing if the entries have been moved
        soup = BeautifulSoup(rv.data, 'html.parser')
        result = soup.find_all('li')
        id_order = []
        for item in result:
            id_order.append(str(item.get('id')))
        assert '1' in id_order[0]
        assert '2' in id_order[1]


class DeleteEditTestCase(DBTestCase):
    """Tests for delete and edit entry."""

    def setUp(self):
        """Set the app up using DBTestCase setUp, and add an entry."""
        DBTestCase.setUp(self)
        self.login('admin', 'default')
        self.app.post(
            '/add',
            data=dict(title='Hello',
                      text='HTML allowed here'),
            follow_redirects=True)

    def tearDown(self):
        """Tear the app down."""
        DBTestCase.tearDown(self)

    def test_empty_db(self):
        """
        The database is not empty.

        The db is not empty here, because we added an
        entry and need to test if it's added indeed.
        """
        rv = self.app.get('/')
        assert b'Hello' in rv.data

    def test_edit(self):
        """Test entry edit."""
        self.app.get('/entry=1', follow_redirects=True)
        rv = self.app.post(
            '/entry=1',
            data=dict(title='Bye',
                      text='Nothing is allowed here'),
            follow_redirects=True)
        assert b'HTML' not in rv.data
        assert b'Entry was successfuly edited' in rv.data
        assert b'Bye' in rv.data

    def test_delete(self):
        """Test entry delete."""
        rv = self.app.post('delete=1', follow_redirects=True)
        assert b'Hello' not in rv.data
        assert b'The entry was deleted' in rv.data


if __name__ == '__main__':
    unittest.main()
