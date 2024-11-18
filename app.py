from flask import Flask, request, render_template, jsonify
import pyodbc
import os
import uuid
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials
import shutil

# Configurações do Flask
app = Flask(__name__)

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

# Caminhos remotos
WINDOWS_SHARED_PATH = r"\\191.232.170.155\fotos"
LINUX_SHARED_PATH = r"\\191.234.180.95\SharedFolder"

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
        # Verifica se os arquivos foram enviados corretamente
        if 'imagem' not in request.files or 'documento' not in request.files:
            return "Imagem ou documento não enviados.", 400
        
        imagem = request.files['imagem']
        documento = request.files['documento']
        
        if imagem.filename == '' or documento.filename == '':
            return "Nenhuma imagem ou documento selecionado.", 400

        # Recebe os dados do formulário
        nome = request.form["nome"]
        email = request.form["email"]
        telefone = request.form["telefone"]

        # Gera nomes únicos para os arquivos
        imagem_filename = f"{uuid.uuid4()}_{imagem.filename}"
        documento_filename = f"{uuid.uuid4()}_{documento.filename}"

        # Salva a imagem no compartilhamento do Windows
        imagem_path = os.path.join(WINDOWS_SHARED_PATH, imagem_filename)
        with open(imagem_path, 'wb') as img_file:
            shutil.copyfileobj(imagem.stream, img_file)

        # Salva o documento no compartilhamento do Linux
        documento_path = os.path.join(LINUX_SHARED_PATH, documento_filename)
        with open(documento_path, 'wb') as doc_file:
            shutil.copyfileobj(documento.stream, doc_file)

        # Verifica quantos rostos existem na imagem
        faces_count = detect_faces(imagem_path)
        cognitivo = faces_count > 0  # Define se há ou não rostos

        # Insere no banco de dados
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO Pessoas (nome, email, telefone, caminho_imagem, caminho_documento, cognitivo, rostos)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (nome, email, telefone, imagem_path, documento_path, cognitivo, faces_count)
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
