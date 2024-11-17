from flask import Flask, request, render_template, jsonify
import pyodbc
import os
import uuid
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials

# Configurações do Flask
app = Flask(__name__)
UPLOAD_FOLDER = 'anexo'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configurações do banco de dados SQL Server
server = 'servidorsqlsegurancadavi.database.windows.net'
database = 'bancoseguranca'
username = 'adminsql'
password = 'SegurancaSQL123!'
driver = '{ODBC Driver 18 for SQL Server}'

# Configurações da API do Azure
ENDPOINT = "https://faceapiseguranca.cognitiveservices.azure.com/"
KEY = "723a8ddf8a744fe39059e2f17297b490"

face_client = FaceClient(ENDPOINT, CognitiveServicesCredentials(KEY))

# Conexão com o banco de dados
def get_db_connection():
    conn = pyodbc.connect(
        f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password}'
    )
    return conn

# Função para verificar rostos na imagem
def detect_faces(image_path):
    with open(image_path, 'rb') as image_stream:
        detected_faces = face_client.face.detect_with_stream(
            image=image_stream,
            detection_model="detection_01",
            recognition_model="recognition_04",
            return_face_id=False
        )
        return len(detected_faces)  # Retorna a quantidade de rostos detectados

@app.route("/", methods=["GET", "POST"])
def index():
    cognitivo = None  # Variável para armazenar se há rosto (True/False)
    faces_count = 0  # Variável para armazenar a quantidade de rostos detectados

    if request.method == "POST":
        # Verifica se o arquivo de imagem foi enviado corretamente
        if 'imagem' not in request.files:
            return "Imagem não enviada.", 400
        
        imagem = request.files['imagem']
        if imagem.filename == '':
            return "Nenhuma imagem selecionada.", 400

        # Recebe os dados do formulário
        nome = request.form["nome"]
        email = request.form["email"]
        telefone = request.form["telefone"]
        documento = request.files["documento"]

        # Salva os arquivos na pasta de anexos
        imagem_filename = f"{uuid.uuid4()}_{imagem.filename}"
        documento_filename = f"{uuid.uuid4()}_{documento.filename}"
        imagem_path = os.path.join(app.config['UPLOAD_FOLDER'], imagem_filename)
        documento_path = os.path.join(app.config['UPLOAD_FOLDER'], documento_filename)
        imagem.save(imagem_path)
        documento.save(documento_path)

        # Verifica quantos rostos existem na imagem
        faces_count = detect_faces(imagem_path)
        cognitivo = faces_count > 0  # Define se há ou não rostos

        # Insere no banco de dados
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO Pessoas (nome, email, telefone, caminho_imagem, caminho_documento, cognitivo)
               VALUES (?, ?, ?, ?, ?, ?)''',
            (nome, email, telefone, f"/{UPLOAD_FOLDER}/{imagem_filename}", f"/{UPLOAD_FOLDER}/{documento_filename}", cognitivo)
        )
        conn.commit()
        conn.close()

    # Consulta os registros
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Pessoas")
    pessoas = cursor.fetchall()
    conn.close()

    return render_template("index.html", pessoas=pessoas, cognitivo=cognitivo, faces_count=faces_count)

if __name__ == "__main__":
    app.run(debug=True)
