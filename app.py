from os import environ
from flask import Flask 
from flask import render_template
from flask import request
from flask.helpers import url_for
from wtforms import validators
from wtforms.fields.simple import TextAreaField 
from database import articles
from flask import redirect
from flask import session
from flask import g
from flask import flash
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import PasswordField
from wtforms import TextAreaField
from wtforms.validators import DataRequired, InputRequired

import sqlite3
import os

flask_app = Flask(__name__)
flask_app.config.from_pyfile("/flask/configs/default.py")

if "MDBLOG_CONFIG" in os.environ:
	flask_app.config.from_envvar("MDBLOG_CONFIG")

### FORMS

class LoginForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired()])

class ArticleForm(FlaskForm):
	title = StringField('Title', validators=[DataRequired()])
	content = TextAreaField('Content')



### CONTROLLERS
@flask_app.route("/")
def view_welcome_page():
	return render_template("welcome_page.jinja")

@flask_app.route("/about/")
def view_about():
	return render_template("about.jinja")

@flask_app.route("/admin/")
def view_admin():
	if "logged" not in session:
		return redirect(url_for("view_login"))
	return render_template("admin.jinja")


### ARTICLES

@flask_app.route("/articles/new/", methods = ["GET"])
def view_add_article():
	if "logged" not in session:
		flash("You must be logged in", "alert-danger")
		return redirect(url_for("view_login"))
	form = ArticleForm()
	return render_template("aricle_editor.jinja, form=form")

@flask_app.route("/articles/", methods =["POST"])
def add_article():
	if "logged" not in session:
		flash("You must be logged in", "alert-danger")
		return redirect(url_for("view_login"))
	db = get_db()
	db.execute("insert into articles (title, content) values (?, ?)",
			[request.form.get("title"), request.form.get("content")])
	db.commit()
	flash("New article was added")
	return redirect(url_for("view_articles"))

@flask_app.route("/articles/", methods =["GET"])
def view_articles():
	db = get_db()
	cur = db.execute("select * from articles order by id desc")
	articles = cur.fetchall()
	return render_template("articles.jinja", articles=articles)

@flask_app.route("/articles/<int:art_id>")
def view_article(art_id):
	db = get_db()
	cur = db.execute("select * from articles where id = art_id")
	article = cur.fetchone() 
	if article:
		return render_template("article.jinja", article=article)
	return render_template("article_not_found.jinja", art_id=art_id)


@flask_app.route("/login/", methods=["GET"])
def view_login():
	login_form = LoginForm()
	flash("You must be logged in", "alert-danger")
	return render_template("login.jinja", form=login_form)

@flask_app.route("/login/", methods=["POST"])
def view_login_user():
	login_form = LoginForm(request.form)
	if login_form.validate():
		if login_form.username.data == flask_app.config["USERNAME"] and \
			login_form.password.data == flask_app.config["PASSWORD"]:
			session["logged"] = True
			flash("Login successful", "success")
			return redirect(url_for("view_admin"))
		else:
			flash("Invalid credentials", "alert-danger")
			return redirect(url_for("view_login"))
	else:
		for error in login_form.errors:
			flash("{} is missing".format(error), "alert-danger")
		return redirect(url_for("view_login"))


@flask_app.route("/logout/", methods = ["POST"])
def logout_user():
	session.pop("logged")
	flash("You were logged out", "success")
	return redirect(url_for("view_welcome_page"))


### UTILS
def connect_db():
	rv = sqlite3.connect(flask_app.config["DATABASE"])
	rv.row_factory = sqlite3.Row
	return rv

def get_db():
	if not hasattr(g, "sqlite_db"):
		g.sqlite_db = connect_db()
	return g.sqlite_db

@flask_app.teardown_appcontext
def close_db(error):
	if hasattr(g, "sqlite_db"):
		g.sqlite_db.close()

def init_db(app):
	with app.app_context():
		db = get_db()
		with open("schema.sql", "r") as fp:
			db.cursor().executescript(fp.read())
		db.commit()
