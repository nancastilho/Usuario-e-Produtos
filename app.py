import sqlite3
from flask import Flask, render_template, request, url_for, flash, redirect
from werkzeug.exceptions import abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt



app = Flask(__name__, static_url_path='/static')
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'your secret key'


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn


def get_post(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    conn.close()
    if post is None:
        abort(404)
    return post


def get_setor(setor_id):
    conn = get_db_connection()
    setor = conn.execute('SELECT * FROM setores WHERE id = ?',
                         (setor_id,)).fetchone()
    conn.close()
    if setor is None:
        abort(404)
    return setor

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(20), nullable=False, unique=True)
    departamento = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(80), nullable=False)

class RegisterForm(FlaskForm):
  
    nome = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Nome"})

    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=50)], render_kw={"placeholder": "Email"})    
    
    departamento = ''

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Senha"})

    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Please choose a different one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=50)], render_kw={"placeholder": "Email"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Senha"})

    submit = SubmitField('Entrar')


@app.route('/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('index'))
    return render_template('login.html', form=form)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@ app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    conn = get_db_connection()
    setores = conn.execute('SELECT * FROM setores').fetchall()
    conn.close()
    if form.validate_on_submit() and request.method == 'POST':
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(nome=form.nome.data, username=form.username.data, departamento=request.form['dep'], password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form, setores=setores)


@app.route('/home', methods=('GET', 'POST'))
@login_required
def index():    
    dep = current_user.username
    conn = get_db_connection()
    posts = conn.execute("SELECT * FROM posts WHERE departamentos LIKE (SELECT departamento FROM user WHERE username = ?)", [dep]).fetchall()
    conn.close()
    print(dep)
    if request.method == 'POST':
            buscar = request.form['buscar']
            conn = get_db_connection()
            posts = conn.execute(
                            "SELECT * FROM posts WHERE status LIKE ? or id LIKE ? or departamentos LIKE ? or title LIKE ?", ('%'+buscar+'%', '%'+buscar+'%', '%'+buscar+'%', '%'+buscar+'%',)).fetchall()
            conn.close()
            return render_template('indexnew.html', posts=posts)

    return render_template('indexnew.html', posts=posts)


@app.route('/graph', methods=('GET', 'POST'))
@login_required
def graph():
    conn = get_db_connection()
    posts = conn.execute(
        'SELECT departamentos, COUNT(*) AS total FROM posts GROUP BY departamentos').fetchall()
    conn.close()
    return render_template('graph.html', posts=posts)


@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    return render_template('post.html', post=post)


@app.route('/manual')
def manual():
    return render_template('manual.html')


@app.route('/inseredep', methods=('GET', 'POST'))
def inseredep():
    if request.method == 'POST':
        setor = request.form['insereDep']
        vf = 'v'
        
        conn = get_db_connection()
        conn.execute('INSERT INTO setores (setor, vf) VALUES (?, ?)',
                            (setor, vf))
        conn.commit()
        conn.close()
        return redirect(url_for('create'))

@app.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    conn = get_db_connection()
    setores = conn.execute('SELECT * FROM setores').fetchall()
    conn.close()
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        conclusao = request.form['conclusao']
        departamentos = request.form['departamentos']
        status = request.form['status']
        anexos = request.form['anexos']

        if not title:
            flash('É necessário ter um título!')
        else:
            conn = get_db_connection()
            conn.execute('INSERT INTO posts (title, content, conclusao, departamentos, status, anexos) VALUES (?, ?, ?, ?, ?, ?)',
                         (title, content, conclusao, departamentos, status, anexos))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))

    return render_template('create.html', setores=setores)


@app.route('/<int:id>/edit', methods=('GET', 'POST'))
def edit(id):
    post = get_post(id)
    conn = get_db_connection()
    setores = conn.execute('SELECT * FROM setores').fetchall()
    conn.close()

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        conclusao = request.form['conclusao']
        departamentos = request.form['departamentos']
        status = request.form['status']
        anexos = request.form['anexos']

        if not title:
            flash('É necessário ter um título!')
        else:
            conn = get_db_connection()
            conn.execute('UPDATE posts SET title = ?, content = ?, conclusao = ?, departamentos = ?, status = ?, anexos = ?'
                         ' WHERE id = ?',
                         (title, content, conclusao, departamentos, status, anexos, id))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))

    return render_template('edit.html', post=post, setores=setores)


@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    post = get_post(id)
    conn = get_db_connection()
    conn.execute('DELETE FROM posts WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('"{}" deletado com sucesso'.format(post['title']))
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)

# @app.route('/cadastro', methods=('GET', 'POST'))
# def cadastro():
#     conn = get_db_connection()
#     setores = conn.execute('SELECT * FROM setores').fetchall()
#     conn.close()
#     if request.method == 'POST':
#         nome = request.form['nome']
#         email = request.form['email']
#         senha = request.form['senha']
#         dep = request.form['dep']

#         if not nome and not email and not senha:
#             flash('É necessário ter as informaçoes!')
#         else:
#             conn = get_db_connection()
#             conn.execute('INSERT INTO contas (nome, email, senha, departamento) VALUES (?, ?, ?, ?)',
#                          (nome, email, senha, dep))
#             conn.commit()
#             conn.close()
#             return redirect(url_for('index'))
#     return render_template('cadastro.html', setores=setores)
