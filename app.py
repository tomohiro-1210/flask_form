from flask import Flask,render_template,url_for,redirect, session ,flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Email, EqualTo

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from pytz import timezone

app = Flask(__name__)

app.config['SECRET_KEY'] = 'mysecretkey'

# DBの設定
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#DBの作成
db = SQLAlchemy(app)
Migrate(app, db)

#Foreign Key（外部キー）の設定？
from sqlalchemy.engine import Engine
from sqlalchemy import event

class RegistrationForm(FlaskForm):
    email = StringField('メールアドレス', validators=[DataRequired(), Email(message="有効なメールアドレスを入力してください")])
    username = StringField('ユーザー名', validators=[DataRequired()])
    password = PasswordField('パスワード', validators=[DataRequired(), EqualTo('pass_comfirm', message="パスワードが一致していません")])
    pass_comfirm = PasswordField('パスワード（確認用）', validators=[DataRequired(),EqualTo('password', message="パスワードが一致していません")])
    submit = SubmitField('登録')

    # ユーザー名の重複が歩かないかを判定する
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('入力されたユーザー名は既に使われています。')
        
    # メアドの重複がないか判定する。
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('入力されたメールアドレスは既に登録されています。')
        

# ユーザーモデルの設定
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    administrator = db.Column(db.String(1))
    # リレーションシップの設定（lazy='dynamic'で1対多の設定になっている）
    post = db.relationship('BlogPost', backref='author', lazy='dynamic')

    def __init__(self, email, username, password_hash, administrator):
        self.email = email
        self.username = username
        self.password_hash = password_hash
        self.administrator = administrator

    def __repr__(self):
        return f"Username: {self.username}"
    

# ブログ投稿のDBモデル
class BlogPost(db.Model):
    __tableame__ = 'blog_post'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # ForeignKey('users.id)はUsersテーブルのidと紐づけする設定
    date = db.Column(db.DateTime, default=datetime.now(timezone('Asia/Tokyo')))
    title = db.Column(db.String(140))
    text = db.Column(db.Text)
    summary = db.Column(db.String(140))
    thumbnail = db.Column(db.String(140))

    def __init__(self, title, text, thumbnail, user_id, summary):
        self.title = title 
        self.text = text
        self.thumbnail = thumbnail
        self.user_id = user_id
        self.summary = summary

    def __repr__(self):
        return f"PostId:{self.id}, Title:{self.title}, Author: {self.author} \n"
    
# ユーザー登録
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # session['email'] = form.email.data
        # session['username'] = form.username.data
        # session['password'] = form.password.data
        
        #フォームから受け取った値をUserインスタンスで生成してDBに格納する処理
        user = User(email=form.email.data, username=form.username.data, password_hash=form.password.data, administrator="0")
        db.session.add(user)
        db.session.commit()

        # 登録後に表示されるメッセージ
        flash('ユーザーが登録されました')
        return redirect(url_for('user_maintenance'))
    return render_template('register.html', form=form)

# ユーザーの編集
@app.route('/user_maintenance')
def user_maintenance():
    users = User.query.order_by(User.id).all()

    return render_template('user_maintenance.html', users=users)

if __name__ == '__main__':
    app.run(debug=True)