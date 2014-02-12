#! /usr/bin/python
import bcrypt
import config
import os
import sqlite3
import datetime
from flask import Flask, request, g, render_template, session, url_for, redirect, flash

cfg = config.Config('weightr.cfg')

app = Flask(__name__)

app.config.update(dict(
	DATABASE=os.path.join(app.root_path, 'weightr.db'),
	DEBUG=cfg.weightr.debug,
	SECRET_KEY=cfg.weightr.secret_key,
))

todo = (
	dict(
		description = 'add weight meassurement',
		progress = 80,
	),
	dict(
		description = 'add show weights',
		progress = 5,
	),
	dict(
		description = 'add fancy graphics',
		progress = 0,
	),
	dict(
		description = 'add preferences / settings',
		progress = 0,
	),
)


@app.route('/')
def index():
	if not session.get('loggedin'):
		return redirect(url_for('login'))

	return render_template('layout.html', todo=todo)

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		db = get_db()
		cur = db.execute("SELECT * FROM user WHERE login = ?",
			[request.form['login']])
		users = cur.fetchall()

		if len(users) is not 1:
			flash('User not found!', 'warning')
		elif not (bcrypt.hashpw(request.form['pass'], users[0]['pass']) == users[0]['pass']):
			flash('Wrong pass!', 'danger')
		else:
			session['loggedin'] = True
			session['user_id'] = users[0]['id']
			session['username'] = users[0]['login']
			return redirect(url_for('index'))

	return render_template('login.html')

@app.route('/logout')
def logout():
	if not session.get('loggedin'):
		return redirect(url_for('login'))

	if 'loggedin' in session:
		session.pop('loggedin')
		flash('Erfolgreich abgemeldet.', 'info')
	return redirect(url_for('index'))

@app.route('/user/<username>')
def user(username):
	if not session.get('loggedin'):
		return redirect(url_for('login'))

	user = None
	weights = None

	if session.get('username') == username:
		db = get_db()
		cur = db.execute('SELECT * FROM user WHERE id = ?', [session.get('user_id')])
		user = cur.fetchall()[0]

		cur = db.execute('SELECT * FROM weights WHERE user_id = ?', [session.get('user_id')])
		weights = cur.fetchall()

	else:
		flash('Sorry, you can only access your own data at this point!', 'info')

	return render_template('user.html', user=user, weights=weights)

@app.route('/update', methods=['GET', 'POST'])
def update():
	if not session.get('loggedin'):
		return redirect(url_for('login'))

	error = None
	if request.method == 'POST':
		weight = None
		try:
			weight = float(request.form['weight'].replace(',', '.'))
		except ValueError:
			error = 'You have to insert a number!'

		if weight:
			db = get_db()
			db.execute("INSERT INTO weights (user_id, timestamp, weight) VALUES (?, ?, ?)", [session.get('user_id'), datetime.datetime.now(), weight])
			db.commit()

			flash('Saved successfully', 'success')

	return render_template('update.html', error=error)


def get_db():
	if not hasattr(g, 'database'):
		g.database = connect_db()
	return g.database

def connect_db():
	db = sqlite3.connect(app.config['DATABASE'], detect_types=sqlite3.PARSE_DECLTYPES)
	db.row_factory = sqlite3.Row
	return db

def init_db():
	with app.app_context():
		db = get_db()
		with app.open_resource('schema.sql', mode='r') as f:
			db.cursor().executescript(f.read())
		db.commit()

def create_user(login, password):
	if login is not None and password is not None:
		with app.app_context():
			db = get_db()
			db.execute("INSERT INTO user (login, pass) VALUES (?, ?)",
				[login, bcrypt.hashpw(password, bcrypt.gensalt())])
			db.commit()


if __name__ == '__main__':
	app.run('0.0.0.0', debug=app.config['DEBUG'])