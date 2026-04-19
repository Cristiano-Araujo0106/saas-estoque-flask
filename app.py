from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
import os
import bcrypt

base_dir = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(base_dir, "templates"),
    static_folder=os.path.join(base_dir, "static")
)

app.secret_key = "chave_super_secreta"

# ---------------- BANCO ----------------
def conectar():
    return sqlite3.connect(os.path.join(base_dir, "database.db"))

with conectar() as conn:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE,
        senha BLOB
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        preco REAL,
        quantidade INTEGER
    )
    """)

# ---------------- AUXILIAR ----------------
def logado():
    return "user" in session

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]

        with conectar() as conn:
            user = conn.execute(
                "SELECT * FROM usuarios WHERE usuario=?",
                (usuario,)
            ).fetchone()

        if user and bcrypt.checkpw(senha.encode(), user[2]):
            session["user"] = usuario
            flash("Bem-vindo!")
            return redirect("/home")

        flash("Login inválido")

    return render_template("login.html")

# ---------------- REGISTRO ----------------
@app.route("/registrar", methods=["GET", "POST"])
def registrar():
    if request.method == "POST":
        usuario = request.form["usuario"]
        senha = request.form["senha"]

        with conectar() as conn:
            existe = conn.execute(
                "SELECT * FROM usuarios WHERE usuario=?",
                (usuario,)
            ).fetchone()

            if existe:
                flash("Usuário já existe")
                return redirect("/registrar")

            senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt())

            conn.execute(
                "INSERT INTO usuarios (usuario, senha) VALUES (?, ?)",
                (usuario, senha_hash)
            )

        flash("Conta criada!")
        return redirect("/")

    return render_template("registrar.html")

# ---------------- HOME (AQUI ESTÁ O QUE VOCÊ QUER) ----------------
@app.route("/home")
def home():
    if not logado():
        return redirect("/")

    with conectar() as conn:
        produtos = conn.execute("SELECT * FROM produtos").fetchall()

    total_produtos = len(produtos)
    total_itens = sum(p[3] for p in produtos)
    valor_total = sum(p[2] * p[3] for p in produtos)

    return render_template(
        "index.html",
        produtos=produtos,
        total_produtos=total_produtos,
        total_itens=total_itens,
        valor_total=valor_total
    )

# ---------------- CADASTRAR ----------------
@app.route("/cadastrar", methods=["GET", "POST"])
def cadastrar():
    if not logado():
        return redirect("/")

    if request.method == "POST":
        nome = request.form["nome"]
        preco = float(request.form["preco"])
        quantidade = int(request.form["quantidade"])

        with conectar() as conn:
            conn.execute(
                "INSERT INTO produtos (nome, preco, quantidade) VALUES (?, ?, ?)",
                (nome, preco, quantidade)
            )

        flash("Produto adicionado!")
        return redirect("/home")

    return render_template("cadastrar.html")

# ---------------- EDITAR ----------------
@app.route("/editar/<int:id>", methods=["GET", "POST"])
def editar(id):
    if not logado():
        return redirect("/")

    with conectar() as conn:
        produto = conn.execute(
            "SELECT * FROM produtos WHERE id=?",
            (id,)
        ).fetchone()

    if request.method == "POST":
        nome = request.form["nome"]
        preco = float(request.form["preco"])
        quantidade = int(request.form["quantidade"])

        with conectar() as conn:
            conn.execute("""
                UPDATE produtos
                SET nome=?, preco=?, quantidade=?
                WHERE id=?
            """, (nome, preco, quantidade, id))

        flash("Atualizado!")
        return redirect("/home")

    return render_template("editar.html", produto=produto)

# ---------------- DELETAR ----------------
@app.route("/deletar/<int:id>")
def deletar(id):
    if not logado():
        return redirect("/")

    with conectar() as conn:
        conn.execute("DELETE FROM produtos WHERE id=?", (id,))

    flash("Removido!")
    return redirect("/home")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- START ----------------
if __name__ == "__main__":
    app.run(debug=True)