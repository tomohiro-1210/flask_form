from flask import Flask,render_template,url_for,redirect, session ,flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, ValidationError
from wtforms.validators import DataRequired, Email, EqualTo
from flask_login import LoginManager, UserMixin, login_user
from werkzeug.security import check_password_hash

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

#ログインマネージャーのインスタンス化
login_manager = LoginManager
login_manager.init_app(app)
login_manager.login_view = 'login'


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

#ログインmanager
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# ユーザーモデルの設定
class User(db.Model, UserMixin):
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

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    

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
    
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(message="正しいメールアドレスを入力してください")])
    password = PasswordField('password', validators=[DataRequired()])
    submit = SubmitField('ログイン')
    
# ユーザ更新のアップデート    
class UpdateUserForm(FlaskForm):
    email = StringField('メールアドレス', validators=[DataRequired(), Email(message='正しいメールアドレスを入力してください')])
    username = StringField('ユーザー名', validators=[DataRequired()])
    password = PasswordField('パスワード', validators=[EqualTo('pass_confirm', message="パスワードが一致していません")])
    pass_confirm = PasswordField('パスワード(確認)')
    submit = SubmitField('更新')

    def __init__(self, user_id, *args, **kwargs):
        super(UpdateUserForm, self).__init__(*args, **kwargs)
        self.id = user_id

    def validate_email(self, field):
        if User.query.filter(User.id != self.id).filter_by(email=field.data).first():
            raise ValidationError('入力されたメールアドレスは既に登録されています。')
        
    def validate_username(self, field):
        if User.query.filter(User.id != self.id).filter_by(username=field.data).first():
            raise ValidationError('入力されたユーザー名は既に使われています。')

@app.route('/login', methods=['GET', 'POST'])
def login():
    #ログインフォームのインスタンス化
    form = LoginForm()
    # フォームのデータが送信されたとき
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # ユーザーのデータがあったとき
        if user is not None:
            if user.check_password(form.password.data):
                login_user(user)
                next = request.args.get('next')

                if next == None or not next[0] == '/':
                    next = url_for('user_maintenance')
                return redirect(next)


            else:
                flash('パスワードが一致しません')

        else:
            flash('入力されたユーザーは存在しません。')

    return render_template('login.html', form=form)
    
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
    # users = User.query.order_by(User.id).all() #全件取得

    # ページャーを有効にする？
    page = request.args.get('page', 1, type=int)
    users = User.query.order_by(User.id).paginate(page=page, per_page=10) # 〇件ごとに取得
    return render_template('user_maintenance.html', users=users)

#更新ページのURLや処理データ
@app.route('/<int:user_id>/account', methods=['GET', 'POST'])
def account(user_id):
    user = User.query.get_or_404(user_id)
    form = UpdateUserForm(user_id)
    # データが格納された後の処理
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data

        if form.password.data:
            user.password_hash = form.password.data
        db.session.commit()

        flash('ユーザーが更新されました。')

        return redirect(url_for('user_maintenance'))
    # getメソッドで受診したときの処理
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email

    return render_template('account.html', form=form)

# 削除処理
@app.route('/<int:user_id>/delete', methods=['GET', 'POST'])
def delete_user(user_id):
    #削除処理
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('ユーザーアカウントが削除されました。')
    return redirect(url_for('user_maintenance'))

if __name__ == '__main__':
    app.run(debug=True)