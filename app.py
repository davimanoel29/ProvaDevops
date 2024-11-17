from flask import Flask, request, render_template, jsonify
from azure.cognitiveservices.vision.face import FaceClient
from msrest.authentication import CognitiveServicesCredentials
import io

app = Flask(__name__)

# Configurações do Azure (chaves e endpoint diretamente no código)
AZURE_FACE_ENDPOINT = "https://faceapiseguranca.cognitiveservices.azure.com/"
AZURE_FACE_KEY = "723a8ddf8a744fe39059e2f17297b490"

# Inicializar o cliente Face
face_client = FaceClient(AZURE_FACE_ENDPOINT, CognitiveServicesCredentials(AZURE_FACE_KEY))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/detect", methods=["POST"])
def detect():
    # Verificar se o arquivo foi enviado
    if "image" not in request.files:
        return jsonify({"error": "Nenhuma imagem enviada."}), 400

    image = request.files["image"]

    # Certifique-se de usar um fluxo (stream) com io.BytesIO
    image_stream = io.BytesIO(image.read())

    # Chamada para o Azure Face API
    try:
        faces = face_client.face.detect_with_stream(image_stream, detection_model="detection_03")
        if faces:
            return jsonify({"message": "Pessoa detectada na imagem.", "face_count": len(faces)})
        else:
            return jsonify({"message": "Nenhuma pessoa detectada na imagem."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
