from einesteine import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin



@login.user_loader
def load_user(id):
    return User.query.get(int(id))

tag_connections = db.Table('tag_connections',
                  db.Column('tagged_id', db.Integer, db.ForeignKey('idea.id')),
                  db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
                  )

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    register_time = db.Column(db.DateTime)
    ideas = db.relationship('Idea', backref='idea_author', lazy='dynamic')
    posts = db.relationship('Post', backref='post_author', lazy='dynamic')
    tags = db.relationship('Tag', backref='tag_author', lazy='dynamic')
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    def __repr__(self):
        return f'<User {self.username}>'

class Idea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))
    number = db.Column(db.Integer)
    complete = db.Column(db.Boolean())
    created_time = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    posts = db.relationship('Post', backref='idea_post', lazy='dynamic')
    def length(self):
        return len(self.posts)
    def __repr__(self):
        return f'<Idea {self.name}>'

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(3000))
    created_time = db.Column(db.DateTime)
    idea_id = db.Column(db.Integer, db.ForeignKey('idea.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    def __repr__(self):
        return f'<Post {self.body}>'


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    ideas = db.relationship('Idea', secondary = tag_connections,
                            secondaryjoin = (tag_connections.c.tag_id == Idea.id),
                            primaryjoin = (tag_connections.c.tagged_id == id),
                            backref=db.backref('tags', lazy='dynamic'), lazy='dynamic')
    def __repr__(self):
        return f'<Tag {self.name}>'
