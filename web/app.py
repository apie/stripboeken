#!/usr/bin/env python3
import os

import flask
import flask_sqlalchemy
from flask import redirect, url_for, request, send_from_directory, render_template
from flask_mail import Mail
from flask_security import SQLAlchemyUserDatastore
from flask_security.models import fsqla_v2 as fsqla
from flask_security import Security
from flask_login import current_user
from flask_security import auth_required

import config

app = flask.Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_DEFAULT_REMEMBER_ME'] = True
app.config['SECURITY_RECOVERABLE'] = True
app.config['SECURITY_UNAUTHORIZED_VIEW'] = '/'
app.config['SECURITY_SEND_PASSWORD_RESET_NOTICE_EMAIL'] = False
app.config['SECURITY_EMAIL_SUBJECT_REGISTER'] = 'Account aangemaakt! Welkom bij Teverzamelen'

app.config['MAIL_SERVER'] = config.MAIL_SERVER
app.config['MAIL_PORT'] = config.MAIL_PORT
app.config['MAIL_USE_SSL'] = config.MAIL_USE_SSL
app.config['MAIL_USERNAME'] = config.MAIL_USERNAME
app.config['MAIL_DEFAULT_SENDER'] = config.MAIL_DEFAULT_SENDER
app.config['MAIL_PASSWORD'] = config.MAIL_PASSWORD
mail = Mail(app)
# Generate a nice key using secrets.token_urlsafe()
app.config['SECRET_KEY'] = config.SECRET_KEY
# Generate a good salt using: secrets.SystemRandom().getrandbits(128)
app.config['SECURITY_PASSWORD_SALT'] = config.SECURITY_PASSWORD_SALT

# As of Flask-SQLAlchemy 2.4.0 it is easy to pass in options directly to the
# underlying engine. This option makes sure that DB connections from the
# pool are still valid. Important for entire application since
# many DBaaS options automatically close idle connections.
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,
}

db = flask_sqlalchemy.SQLAlchemy(app)

app.config['DEBUG'] = config.DEBUG


class Collection(db.Model):
    __tablename__ = 'collection'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship("User")
    name = db.Column(db.String(255))
    public = db.Column(db.Boolean(), default=False)


class Item(db.Model):
    __tablename__ = 'item'
    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection.id'))
    collection = db.relationship("Collection", backref=db.backref('items', lazy='dynamic'))
    sequence = db.Column(db.Integer)
    name = db.Column(db.String(255))
    owned = db.Column(db.Boolean(), default=False)
    want = db.Column(db.Boolean(), default=False)
    read = db.Column(db.Boolean(), default=False)


# Define models
fsqla.FsModels.set_db_info(db)


class Role(db.Model, fsqla.FsRoleMixin):
    pass


class User(db.Model, fsqla.FsUserMixin):
    pass


user_datastore = SQLAlchemyUserDatastore(db, User, Role)
db.create_all()
security = Security(app, user_datastore)


# TODO
@app.route('/favicon.ico')
def favicon():
    return b''
    return app.send_static_file('favicon.ico')


@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


@app.route('/')
def index():
    collections = ()
    if getattr(current_user, 'email', None):
        collections = Collection.query.filter_by(user=current_user)
    return render_template('index.html', title='Teverzamelen.nl', collections=collections)


@app.route('/public')
def public():
    collections = Collection.query.filter_by(public=True)
    return render_template('public_index.html', title='Gedeelde lijstjes', collections=collections)


@app.route('/collection/<id>')
@auth_required()
def view_collection(id):
    collection = Collection.query.filter_by(user=current_user, id=id).first()
    items = Item.query.filter_by(collection=collection)
    return render_template('view_collection.html', title='Bewerk lijstje', items=items)


@app.route('/copy_collection/<id>')
@auth_required()
def copy_collection(id):
    # Copy public collection to your collections
    return f'TODO COPY {id} to {current_user.email}' #TODO


if __name__ == '__main__':
    app.run()