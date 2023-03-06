import sqlite3
import urllib.request
import os
from flask import Flask, render_template, request, url_for, flash, redirect, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from flask_bcrypt import Bcrypt
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from werkzeug.utils import secure_filename
from werkzeug.exceptions import abort
from zeep import Client

db = SQLAlchemy()
app = Flask(__name__, static_url_path='/static')
UPLOAD_FOLDER = 'static/images/'
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = 'your secret key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

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


def get_produto(produto_id):
    conn = get_db_connection()
    produto = conn.execute('SELECT * FROM produtos WHERE id = ?',
                           (produto_id,)).fetchone()
    conn.close()
    if produto is None:
        abort(404)
    return produto


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
    password = db.Column(db.String(80), nullable=False)


class RegisterForm(FlaskForm):

    nome = StringField(validators=[
        InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Nome"})

    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=50)], render_kw={"placeholder": "Email"})

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

# ROTAS DE USUARIO


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('index'))
    return render_template('login.html', form=form)


@app.route('/sair', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@ app.route('/registrar', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit() and request.method == 'POST':
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(nome=form.nome.data,
                        username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

# ACABA ROTAS DE USUARIO


@app.route('/', methods=('GET', 'POST'))
def indexOf():
    conn = get_db_connection()
    produtos = conn.execute(
        "SELECT * FROM produtos").fetchall()
    conn.close()
    if request.method == 'POST':
        buscar = request.form['buscar']
        conn = get_db_connection()
        produtos = conn.execute(
            "SELECT * FROM produtos WHERE departamentos LIKE ? or produto LIKE ?  ", ('%'+buscar+'%', '%'+buscar+'%',)).fetchall()
        conn.close()
        return render_template('indexOf.html', produtos=produtos)

    return render_template('indexOf.html', produtos=produtos)


@app.route('/orderof', methods=('GET', 'POST'))
def orderof():
    if request.method == 'POST':
        ordem = request.form['ordem']
        conn = get_db_connection()
        produtos = conn.execute(
            "select CAST(preco AS DECIMAL(7,2)) as Valor , * from produtos Where estoqueLoja >=1 order by valor "+ordem+"",).fetchall()
        conn.close()
        return render_template('indexOf.html', produtos=produtos)


@app.route('/<int:produto_id>/of')
def produtoOf(produto_id):
    produto = get_produto(produto_id)
    return render_template('produtoOf.html', produto=produto)


@app.route('/admin', methods=('GET', 'POST'))
@login_required
def index():

    dep = current_user.username
    conn = get_db_connection()
    produtos = conn.execute("SELECT * FROM produtos").fetchall()
    conn.close()
    print(dep)
    if request.method == 'POST':
        buscar = request.form['buscar']
        conn = get_db_connection()
        produtos = conn.execute(
            "SELECT * FROM produtos WHERE departamentos LIKE ? or produto LIKE ?", ('%'+buscar+'%', '%'+buscar+'%',)).fetchall()
        conn.close()
        return render_template('index.html', produtos=produtos)

    return render_template('index.html', produtos=produtos)


@app.route('/order', methods=('GET', 'POST'))
@login_required
def order():
    if request.method == 'POST':
        ordem = request.form['ordem']
        conn = get_db_connection()
        produtos = conn.execute(
            "select CAST(preco AS DECIMAL(7,2)) as Valor , * from produtos order by valor "+ordem+"",).fetchall()
        conn.close()
        return render_template('index.html', produtos=produtos)


@app.route('/<int:produto_id>')
@login_required
def produto(produto_id):
    produto = get_produto(produto_id)
    return render_template('produto.html', produto=produto)


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


@app.route('/<int:produto_id>/novaimg', methods=('GET', 'POST'))
def novaimg(produto_id):
    if request.method == 'POST':
        file = request.files['file']
        anexos = file.filename.replace(" ", "_")
        if not file:
            flash('É necessário selecionar para salvar!')
        else:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            conn = get_db_connection()
            conn.execute('UPDATE produtos SET anexos =?'
                         ' WHERE id = ?',
                         (anexos, produto_id))
            conn.commit()
            conn.close()
            return redirect(url_for('edit', id=produto_id))


@app.route('/consultar-cep', methods=['POST'])
def consultar_cep():
    client = Client(
        'https://apps.correios.com.br/SigepMasterJPA/AtendeClienteService/AtendeCliente?wsdl')
    data = client.service.consultaCEP(request.form.get('cep'))
    data = data.__dict__

    return jsonify(data['__values__'])


@app.route('/novoproduto', methods=('GET', 'POST'))
@login_required
def create():
    conn = get_db_connection()
    setores = conn.execute('SELECT * FROM setores').fetchall()
    conn.close()
    if request.method == 'POST':
        file = request.files['file']
        produto = request.form['produto']
        descricao = request.form['descricao']
        preco = request.form['preco']
        departamentos = request.form['departamentos']
        estoqueLoja = request.form['estoqueLoja']
        anexos = file.filename.replace(" ", "_")

        if not produto:
            flash('É necessário ter um título!')
        else:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            conn = get_db_connection()
            conn.execute('INSERT INTO produtos (produto, descricao, preco, departamentos, estoqueLoja, anexos) VALUES (?, ?, ?, ?, ?, ?)',
                         (produto, descricao, preco, departamentos, estoqueLoja, anexos))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))

    return render_template('create.html', setores=setores)


@app.route('/<int:id>/editar', methods=('GET', 'POST'))
def edit(id):
    produto = get_produto(id)
    conn = get_db_connection()
    setores = conn.execute('SELECT * FROM setores').fetchall()
    conn.close()

    if request.method == 'POST':
        produto = request.form['produto']
        descricao = request.form['descricao']
        preco = request.form['preco']
        departamentos = request.form['departamentos']
        estoqueLoja = request.form['estoqueLoja']

        if not produto:
            flash('É necessário ter um título!')
        else:
            conn = get_db_connection()
            conn.execute('UPDATE produtos SET produto = ?, descricao = ?, preco = ?, departamentos = ?, estoqueLoja = ?'
                         ' WHERE id = ?',
                         (produto, descricao, preco, departamentos, estoqueLoja, id))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))

    return render_template('edit.html', produto=produto, setores=setores)


@app.route('/<int:id>/delete', methods=('POST',))
def delete(id):
    produto = get_produto(id)
    conn = get_db_connection()
    conn.execute('DELETE FROM produtos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('"{}" deletado com sucesso'.format(produto['produto']))
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)

# @app.route('/cadastro', methods=('GET', 'produto'))
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
