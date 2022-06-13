# -*- coding: utf-8 -*-

from einesteine import app, db
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sqla
from werkzeug.urls import url_parse
import einesteine.forms as forms
from einesteine.models import User, Tag, Idea, Post, tag_connections
from datetime import datetime



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/add_tag/<tag_name>', methods=['POST'])
@login_required
def add_tag(tag_name):
    tag = Tag(name=tag_name, user_id=current_user.id)
    db.session.add(tag)
    db.session.commit()
    return jsonify({'status' : '200', 'tag_name' : tag_name, 'tag_id' : tag.id})

@app.route('/del_tag/<tag_id>', methods=['POST'])
@login_required
def del_tag(tag_id):
    tag = Tag.query.get(tag_id)
    if tag.user_id == current_user.id:
        db.session.delete(tag)
        db.session.commit()
    return '200'

@app.route('/connect/<idea_id>/<tag_id>', methods=['POST'])
@login_required
def connect_idea_tag(idea_id, tag_id):
    idea = Idea.query.get(idea_id)
    tag = Tag.query.get(tag_id)
    connected = False
    if tag not in idea.tags:
        idea.tags.append(tag)
        db.session.commit()
        connected = True
    return jsonify({'status' : '200', 'tag_name' : tag.name, 'connected' : connected})

@app.route('/disconnect/<idea_id>/<tag_id>', methods=['POST'])
@login_required
def disconnect_idea_tag(idea_id, tag_id):
    idea = Idea.query.get(idea_id)
    tag = Tag.query.get(tag_id)
    if tag in idea.tags:
        idea.tags.remove(tag)
        db.session.commit()
    return jsonify({'status' : '200'})

@app.route('/delete_post/<post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get(post_id)
    if post is not None:
        if post.user_id == current_user.id:
            db.session.delete(post)
            db.session.commit()
    return jsonify({'status' : '200'})

@app.route('/delete_idea/<idea_id>', methods=['POST'])
@login_required
def delete_idea(idea_id):
    idea = Idea.query.get(idea_id)
    if idea is not None:
        if idea.user_id == current_user.id:
            db.session.delete(idea)
            db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/update_idea', methods=['POST'])
@login_required
def update_idea():
    data = request.get_json()[0]
    idea = Idea.query.get(data['idea_id'])
    if idea.user_id == current_user.id:
        idea.name = data['name']
        if data['text'] != '':
            post = Post(body = data['text'], created_time = datetime.strptime(data['date'], '%d.%m.%Y %H:%M'), user_id=current_user.id, idea_id=idea.id)
            db.session.add(post)
        if data['completed'] in [True, False]:
            idea.complete = data['completed']
        db.session.commit()
    return jsonify({'status' : '200', 'post_id' : post.id, 'created_time' : post.created_time.strftime('%d.%m.%Y %H:%M')})

@app.route('/')
@app.route('/index')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = forms.LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            return redirect(url_for('login'))
        login_user(user, remember=True)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = forms.RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, register_time=datetime.now())
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/board')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user, ideas=current_user.ideas, tags=current_user.tags.all())

@app.route('/board/filtered/<tag_name>')
@login_required
def dashboard_filtered_by_tag(tag_name):
    tag = Tag.query.filter_by(name = tag_name, user_id = current_user.id).first()
    ideas = []
    if tag is not None:
        ideas = tag.ideas if tag.ideas is not None else []
    return render_template('dashboard.html', user=current_user, ideas=ideas, tags=current_user.tags.all())

@app.route('/board/completed/<stage>')
@login_required
def dashboard_filtered_by_complete(stage):
    ideas = []
    if stage == '1':
        ideas = Idea.query.filter_by(user_id = current_user.id, complete = False).all()
    if stage == '2':
        ideas = Idea.query.filter_by(user_id = current_user.id, complete = False).filter(Idea.posts).all()
    if stage == '3':
        ideas = Idea.query.filter_by(user_id = current_user.id, complete = True).all()
    return render_template('dashboard.html', user=current_user, ideas=ideas, tags=current_user.tags.all())



@app.route('/editor')
@login_required
def editor_empty():
    idea = Idea(name = 'Моя шикарная идея', created_time = datetime.now(), user_id = current_user.id, complete = False, number = 0)
    db.session.add(idea)
    db.session.commit()
    return redirect(url_for('editor', idea_id = idea.id))

@app.route('/editor/<idea_id>')
@login_required
def editor(idea_id):
    idea = Idea.query.get(idea_id)
    tags = Tag.query.filter_by(user_id=current_user.id).all()
    if idea is not None and idea.user_id == current_user.id:
        return render_template('editor.html', idea = idea, tags = tags)
    else:
        return redirect(url_for('logout'))

@app.route('/profile')
@login_required
def profile():
    return render_template('account.html', user=current_user)
