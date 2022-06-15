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
    tag = Tag(name=tag_name[:25], user_id=current_user.id)
    db.session.add(tag)
    db.session.commit()
    return jsonify({'status' : '200', 'tag_name' : tag_name, 'tag_id' : tag.id})

@app.route('/del_tag/<tag_id>', methods=['POST'])
@login_required
def del_tag(tag_id):
    tag = Tag.query.filter_by(id = tag_id, user_id = current_user.id).first()
    if tag:
        db.session.delete(tag)
        db.session.commit()
        return '200'
    else: return '500'

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

@app.route('/deleteme')
@login_required
def delete_account():
    current_user.ideas.delete()
    current_user.tags.delete()
    current_user.posts.delete()
    db.session.delete(current_user)
    db.session.commit()
    return redirect(url_for('register'))

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
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
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
    ideas = current_user.ideas.paginate(1, 50, False).items if current_user.ideas != None else None
    return render_template('dashboard.html', user=current_user, ideas=ideas, tags=current_user.tags.all(), tag_name='none', stage='none')

@app.route('/board/filtered/<tag_name>')
@login_required
def dashboard_filtered_by_tag(tag_name):
    tag = Tag.query.filter_by(name = tag_name, user_id = current_user.id).first()
    ideas = []
    if tag is not None:
        ideas = tag.ideas if tag.ideas is not None else []
        ideas = ideas.paginate(1, 50, False).items if ideas != None else None
    return render_template('dashboard.html', user=current_user, ideas=ideas, tags=current_user.tags.all(), stage='none', tag_name=tag_name)

@app.route('/board/completed/<stage>')
@login_required
def dashboard_filtered_by_complete(stage):
    ideas = []
    if stage == '1':
        ideas = Idea.query.filter_by(user_id = current_user.id, complete = False).filter(Idea.posts == None).all()
    if stage == '2':
        ideas = Idea.query.filter_by(user_id = current_user.id, complete = False).filter(Idea.posts).all()
    if stage == '3':
        ideas = Idea.query.filter_by(user_id = current_user.id, complete = True).all()
    ideas = ideas.paginate(1, 50, False).items if ideas != None else None
    return render_template('dashboard.html', user=current_user, ideas=ideas, tags=current_user.tags.all(), tagn = False, stage=stage, tag_name='none')

@app.route('/board/deep_filtered/<tag_name>/<stage>')
@login_required
def dashboard_deep_filtered(tag_name, stage):
    tag = Tag.query.filter_by(name = tag_name, user_id = current_user.id).first()
    if tag == None or tag.ideas == None:
        return redirect(url_for('dashboard'))
    if stage == '1':
        ideas = tag.ideas.filter(not Idea.complete and Idea.posts == None).all()
    if stage == '2':
        ideas = tag.ideas.filter(not Idea.complete and Idea.posts).all()
    if stage == '3':
        ideas = tag.ideas.filter(Idea.complete).all()
    if ideas == None:
        return redirect(url_for('dashboard'))
    ideas = ideas.paginate(1, 50, False) if ideas != None else None
    return render_template('dashboard.html', user=current_user, ideas=ideas, tags=current_user.tags.all(), stage=stage, tag_name=tag_name)

@app.route('/get_ideas/<tag_name>/<stage>', methods=['POST'])
@login_required
def get_ideas_page(tag_name, stage):
    data = request.get_json()[0]
    if tag_name != 'none':
        tag = Tag.query.filter_by(name = tag_name, user_id = current_user.id).first()
        if tag != None or tag.ideas != None:
            ideas = tag.ideas
        else:
            ideas = current_user.ideas
    else:
        ideas = current_user.ideas

    if stage != 'none':
        if stage == '1':
            ideas = ideas.filter(not Idea.complete and Idea.posts == None).all()
        if stage == '2':
            ideas = ideas.filter(not Idea.complete and Idea.posts).all()
        if stage == '3':
            ideas = ideas.filter(Idea.complete).all()

    if ideas == None:
        return jsonify({'status' : 200, 'ideas' : None, 'have_new' : False})
    ideas = ideas.paginate(int(data['next_page']), 50, False).items
    ideas = [{'id' : idea.id,
              'name' : idea.name,
              'number' : idea.number,
              'complete' : idea.complete,
              'created_time' : idea.created_time.strftime('%d.%m.%Y')} for idea in ideas]
    return jsonify({'status' : 200, 'ideas' : ideas, 'have_new' : True})

@app.route('/editor')
@login_required
def editor_empty():
    number = current_user.last_idea_id
    idea = Idea(name = 'Моя шикарная идея', created_time = datetime.now(), user_id = current_user.id, number = number)
    current_user.last_idea_id += 1
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

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = forms.DeleteAccountForm()
    if form.validate_on_submit():
        print(1)
        return redirect(url_for('register'))
    return render_template('account.html', user=current_user, form=form)
