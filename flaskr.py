import os
import sqlite3
import fnmatch
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash

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
    #Connects to the specifif database.
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def get_db():
    '''Opens a new database connection if there is non yet for the current application context.'''
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db  = connect_db()
    return g.sqlite_db

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    '''Initializes the database.'''
    init_db()
    print("Initialized the database")

@app.teardown_appcontext
def close_db(error):
    '''Closes the database again at the end of th request.'''
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/')
def show_entries():
    db=get_db()
    cur = db.execute('select id, title, text from entries order by id desc')
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries)

@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('insert into entries (title, text) values (?, ?)',
        [request.form['title'], request.form['text']])
    db.commit()
    flash('New entry was successfuly posted')
    return redirect(url_for('show_entries'))

@app.route('/login', methods=['GET','POST'])
def login():
    error=None
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
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))


@app.route('/entry=<entry_id>&move=<direction>', methods=['GET'])
def move_entry(entry_id, direction):
    """Move entry up or down."""
    db = get_db()
    cur = db.execute('select id from entries order by id desc')
    data = []
    for i, row in enumerate(cur):
        data.append([i, row[0]])
    if fnmatch.fnmatch(direction, 'up'):
        if data[0][1] == int(entry_id):
            flash('The entry is already on the top')
            return redirect(url_for('show_entries'))
        else:
            for i, row in enumerate(data):
                if row[1] == int(entry_id):
                        current_row = data[i]
                        previous_row = data[i - 1]
                        db.execute('''UPDATE entries
                                      SET id = ?
                                      WHERE id = ?''',
                                   (99999999, current_row[1]))
                        db.execute('''UPDATE entries
                                      SET id = ?
                                      WHERE id = ?''',
                                   (current_row[1], previous_row[1]))
                        db.execute('''UPDATE entries
                                      SET id = ?
                                      WHERE id = ?''',
                                   (previous_row[1], 99999999))
        db.commit()
    elif fnmatch.fnmatch(direction, 'down'):
        if data[-1][1] == int(entry_id):
            flash('The entry is the last one, can\'t move down')
            return redirect(url_for('show_entries'))
        else:
            for i, row in enumerate(data):
                if row[1] == int(entry_id):
                    current_row = data[i]
                    previous_row = data[i + 1]
                    db.execute('''UPDATE entries
                                  SET id = ?
                                  WHERE id = ?''',
                               (99999999, current_row[1]))
                    db.execute('''UPDATE entries
                                  SET id = ?
                                  WHERE id = ?''',
                               (current_row[1], previous_row[1]))
                    db.execute('''UPDATE entries
                                  SET id = ?
                                  WHERE id = ?''',
                               (previous_row[1], 99999999))
        db.commit()
    return redirect(url_for('show_entries'))
