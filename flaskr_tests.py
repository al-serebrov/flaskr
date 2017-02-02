"""Test application.

There are tests intended to check that app is functioning correctly
"""

import os
import flaskr
import unittest
import tempfile
import fnmatch


class FlaskrTestCase(unittest.TestCase):
    """Test class."""

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

    def test_login_logout(self):
        """Login/logout test."""
        # with correct credentials
        rv = self.login('admin', 'default')
        assert b'You were logged in' in rv.data
        # logout
        rv = self.logout()
        assert b'You were logged out' in rv.data
        # with incorrect login
        rv = self.login('adminx', 'default')
        assert b'Invalid username' in rv.data
        # with invalid password
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

    def test_edit(self):
        """Test entry edit."""
        self.login('admin', 'default')
        self.app.post(
            '/add',
            data=dict(title='Hello',
                      text='HTML allowed here'),
            follow_redirects=True)
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
        self.login('admin', 'default')
        self.app.post(
            'add',
            data=dict(title='Hey',
                      text='World'),
            follow_redirects=True)
        rv = self.app.post('delete=1', follow_redirects=True)
        assert b'Hey' not in rv.data
        assert b'The entry was deleted' in rv.data

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
        """print(rv.data)
        is_correct_order = False
        if fnmatch.fnmatch('rv.data', '.<li id=\'1\'>.*<li id=\'2\'>.'):
            is_correct_order = True
        print(is_correct_order)
        
        in process
        """

if __name__ == '__main__':
    # import pdb; pdb.set_trace()
    unittest.main()
