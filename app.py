import os
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FileField
from wtforms.validators import DataRequired, Length, Email
from flask_wtf.file import FileAllowed
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_migrate import Migrate

# Khởi tạo Flask và các phần mở rộng
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'postgresql+psycopg2://postgres:123456@localhost/social_blog_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Định nghĩa hàm user_loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Mô hình User
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    avatar = db.Column(db.String(120), default='default.jpg')
    bio = db.Column(db.Text, nullable=True)  # Thông tin cá nhân

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Mô hình Post
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    likes = db.relationship('Like', backref='post', lazy='dynamic')
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

# Mô hình Like
class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

# Mô hình Comment
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

# Mô hình PostFollow
class PostFollow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    user = db.relationship('User', backref='post_follows')
    post = db.relationship('Post', backref='followers')

# Biểu mẫu
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class UpdateProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    bio = TextAreaField('Bio', validators=[Length(max=500)])  # Mô tả cá nhân
    avatar = FileField('Update Avatar', validators=[FileAllowed(['jpg', 'png', 'gif'])])
    submit = SubmitField('Update')

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post')

class CommentForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Comment')

# Route chính
@app.route('/')
def index():
    posts = Post.query.all()
    return render_template('index.html', posts=posts)

# Route đăng nhập
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your email and password.', 'danger')
    return render_template('login.html', form=form)

# Route đăng xuất
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# Route đăng ký
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.bio = form.bio.data

        # Xử lý file avatar
        if form.avatar.data:
            avatar_file = form.avatar.data
            avatar_filename = secure_filename(avatar_file.filename)
            avatar_file.save(os.path.join('static/avatars', avatar_filename))
            current_user.avatar = avatar_filename  # Cập nhật tên file avatar
        
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.bio.data = current_user.bio
    return render_template('profile.html', form=form)

@app.route('/profile/view', methods=['GET'])
@login_required
def view_profile():
    avatar_path = f"/static/avatars/{current_user.avatar}"  # Đường dẫn đến avatar
    return render_template('view_profile.html', user=current_user, avatar_path=avatar_path)

# Route để xem danh sách người dùng
@app.route('/users')
@login_required  # Ensure that only logged-in users can access this page
def users():
    all_users = User.query.all()  # Fetch all users from the database
    return render_template('users.html', users=all_users)  # Render the users.html template with the list of users

# Route để tạo bài đăng
@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author_id=current_user.id)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('index'))
    return render_template('create_post.html', form=form)

# Route để like bài viết
@app.route('/post/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(post_id):
    post = Post.query.get_or_404(post_id)
    like = Like.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if like is None:
        new_like = Like(user_id=current_user.id, post_id=post.id)
        db.session.add(new_like)
        flash('You liked this post!', 'success')
        action = 'liked'
    else:
        db.session.delete(like)
        flash('You unliked this post.', 'success')
        action = 'unliked'
    db.session.commit()

    # Trả về dữ liệu JSON để cập nhật giao diện
    return {
        'action': action,
        'likes_count': post.likes.count()
    }

# Route để xem bài đăng
@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    comments = Comment.query.filter_by(post_id=post_id).all()
    form = CommentForm()
    followed = PostFollow.query.filter_by(user_id=current_user.id, post_id=post_id).first() if current_user.is_authenticated else None
    return render_template('view_post.html', post=post, comments=comments, form=form, followed=followed)

# Route để chỉnh sửa bài đăng
@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author_id != current_user.id:
        flash('You are not authorized to edit this post.', 'danger')
        return redirect(url_for('index'))
    
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('view_post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('edit_post.html', form=form)

# Route để xóa bài đăng
@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author_id != current_user.id:
        flash('You are not authorized to delete this post.', 'danger')
        return redirect(url_for('index'))
    
    db.session.delete(post)
    db.session.commit()
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('index'))

# Route để bình luận
@app.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def comment(post_id):
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(content=form.content.data, author_id=current_user.id, post_id=post_id)
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been added!', 'success')
    return redirect(url_for('view_post', post_id=post_id))

# Route để theo dõi bài viết
@app.route('/post/<int:post_id>/follow', methods=['POST'])
@login_required
def follow_post(post_id):
    post = Post.query.get_or_404(post_id)
    follow = PostFollow.query.filter_by(user_id=current_user.id, post_id=post.id).first()
    if follow is None:
        new_follow = PostFollow(user_id=current_user.id, post_id=post.id)
        db.session.add(new_follow)
        flash('You are now following this post!', 'success')
    else:
        db.session.delete(follow)
        flash('You have unfollowed this post.', 'success')
    db.session.commit()
    return redirect(url_for('view_post', post_id=post_id))

# Chạy ứng dụng
if __name__ == '__main__':
    app.run(debug=True)
