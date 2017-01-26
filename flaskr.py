"""
This is a small Flask application with blog-like functionlaity.

Created just for training purposes.
"""

import os
import sqlite3
import fnmatch
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash

app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment varible
app.config.update(dict(
    DATABASE = os.path.join(app.root_path, 'flaskr.db'),
    SECRET_KEY = 'development key',
    USERNAME = 'admin',
    PASSWORD = 'default'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def connect_db():
    """Connect to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def get_db():
    """Open a new database connection if there is non yet for
    the current application context."""
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


def init_db():
    """Apply database schema."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Initialize the database."""
    init_db()
    print("Initialized the database")


@app.teardown_appcontext
def close_db(error):
    """Close the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def show_entries():
    """Show all entries."""
    db = get_db()
    cur = db.execute('select id, title, text from entries order by sort_order desc')
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries)


@app.route('/add', methods=['POST'])
def add_entry():
    """Add new entry."""
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    max_order_id = db.execute('SELECT MAX(sort_order) FROM entries').fetchone()[0]
    if max_order_id is None:
        new_order_id = 1
    else:
        new_order_id = max_order_id + 1
    db.execute(
        'insert into entries (title, text, sort_order) values (?, ?, ?)',
        [
            request.form['title'],
            request.form['text'],
            new_order_id
        ]
    )
    db.commit()
    flash('New entry was successfuly posted')
    return redirect(url_for('show_entries'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Log the admin user in."""
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    """Log the admin user out."""
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))


@app.route('/delete=<int:entry_id>', methods=['POST'])
def delete_entry(entry_id):
    """Delete entry from database and shows entries again."""
    db = get_db()
    db.execute('delete from entries where id= (?)', (entry_id,))
    db.commit()
    flash('The entry was deleted')
    return redirect(url_for('show_entries'))

@app.route('/entry=<id>', methods=['GET'])
def show_entry(id):
    """Show a singly entry."""
    db = get_db()
    cur = db.execute(
        'select title, text from entries where id = (?)', 
        (id,)
    )
    entries = cur.fetchall()
    return render_template('edit_entry.html',id=id,entries=entries)
    
@app.route('/entry=<id>', methods=['POST'])
def update_entry(id):
    """Update ecntry title and text"""
    db = get_db()
    db.execute(
        'update entries set title = ?, text = ? where id = ?', 
        [request.form['title'], request.form['text'], id]
    )
    db.commit()
    flash('Entry was successfuly edited')
    return redirect(url_for('show_entries'))

    moving_entry_so = db.execute(
        'select sort_order from entries where id = (?)',
        (int(entry_id),)
    ).fetchone()[0]
    if fnmatch.fnmatch(direction, 'up'):
        another_entry_id_so = db.execute(
            '''select id, sort_order from entries
            where sort_order > (?)
            order by sort_order asc limit 1''',
            (moving_entry_so,)
        ).fetchone()
    elif fnmatch.fnmatch(direction, 'down'):
        another_entry_id_so = db.execute(
            '''select id, sort_order from entries
            where sort_order < (?)
            order by sort_order desc limit 1''',
            (moving_entry_so,)
        ).fetchone()
    if another_entry_id_so is not None:
        temp_id = another_entry_id_so[0]
        temp_so = another_entry_id_so[1]
        db.execute(
            'UPDATE entries set sort_order = ? where id = ?',
            (moving_entry_so, temp_id)
        )
        db.execute(
            'UPDATE entries set sort_order = ? where id = ?',
            (temp_so, entry_id)
        )
        db.commit()
    else:
        """Appears when there's no entry with with bigger or smaller order id
        in other words, if we trying to move up the topmost entry or move down
        the very last entry"""
        flash('Unable to move entry %s' % str(direction))

    return redirect(url_for('show_entries'))
