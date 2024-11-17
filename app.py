from flask import Flask, request, render_template, jsonify
import pyodbc

app = Flask(__name__)

# Configurações do banco de dados SQL Server
server = 'servidorsqlsegurancadavi.database.windows.net'
database = 'bancoseguranca'
username = 'adminsql'
password = 'SegurancaSQL123!'
driver = '{ODBC Driver 18 for SQL Server}'

# Conexão com o banco de dados
def get_db_connection():
    conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};'
                          f'SERVER={server};'
                          f'DATABASE={database};'
                          f'UID={username};'
                          f'PWD={password}')
    return conn

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Recebe os dados do formulário
        nome = request.form["nome"]
        email = request.form["email"]
        telefone = request.form["telefone"]
        imagem = request.form["imagem"]
        documento = request.form["documento"]

        # Insere no banco de dados
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO Pessoas (nome, email, telefone, caminho_imagem, caminho_documento)
                          VALUES (?, ?, ?, ?, ?)''', (nome, email, telefone, imagem, documento))
        conn.commit()
        conn.close()

    # Consulta os registros
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Pessoas")
    pessoas = cursor.fetchall()
    conn.close()

    return render_template("index.html", pessoas=pessoas)

if __name__ == "__main__":
    app.run(debug=True)
