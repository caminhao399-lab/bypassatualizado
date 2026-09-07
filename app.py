import os
import datetime
import uuid
import logging
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Importando o motor de bypass
try:
    from engine import BypassEngine
    print("[*] ENGINE DETECTADA: Modo de Produção Ativado.")
except ImportError:
    class BypassEngine:
        def process_apk(self, input_file, output_file):
            return True
    print("[!] AVISO: Engine não encontrada. Usando modo de simulação de teste.")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kl_bypass_ultra_secret_2024'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
CORS(app)

# Configuração de Logging Profissional
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Criação de pastas de sistema
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
os.makedirs('templates', exist_ok=True)

# Instanciando o motor
engine = BypassEngine()

# --- ROTAS DO PAINEL (FRONTEND) ---

@app.route('/')
def index():
    """Carrega a interface do seu Dashboard"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Erro ao carregar template: {str(e)}")
        return f"Erro no Servidor: Certifique-se de que o index.html está na pasta templates. {str(e)}", 500

# --- ROTAS DA API (BACKEND - O MOTOR DE BYPASS) ---

@app.route('/api/v1/upload', methods=['POST'])
def upload_apk():
    """Recebe o APK e inicia o processo de bypass"""
    try:
        if 'file' not in request.files:
            return jsonify({"status": "error", "message": "Nenhum arquivo enviado"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"status": "error", "message": "Arquivo sem nome"}), 400

        if not file.filename.lower().endswith('.apk'):
            return jsonify({"status": "error", "message": "Apenas arquivos .apk são permitidos"}), 400

        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)

        logger.info(f"[UPLOAD] Recebido: {filename}")

        # Gerando identificador único para o processo
        process_id = uuid.uuid4().hex[:8]
        output_filename = f"bypass_{process_id}_{filename}"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)

        # Chamada para o motor de bypass real
        logger.info(f"[*] Iniciando motor de bypass para: {filename}")
        
        # Simulando o tempo de processamento para a UI não travar
        success = engine.process_apk(input_path, output_path)

        if success:
            logger.info(f"[SUCCESS] Bypass concluído para: {filename}")
            return jsonify({
                "status": "success",
                "message": "Bypass aplicado com sucesso! O APK está pronto.",
                "download_url": f"/download/{output_filename}",
                "filename": output_filename
            }), 200
        else:
            raise Exception("O motor de bypass falhou no processamento.")

    except Exception as e:
        logger.error(f"[!] ERRO NO UPLOAD/PROCESSAMENTO: {str(e)}")
        return jsonify({"status": "error", "message": f"Erro no servidor: {str(e)}"}), 500

@app.route('/api/v1/download/<filename>', methods=['GET'])
def download_apk(filename):
    """Rota para baixar o APK já processado"""
    try:
        filename = secure_filename(filename)
        filepath = os.path.join(app.config['PROCESSED_FOLDER'], filename)
        
        if os.path.exists(filepath):
            logger.info(f"[DOWNLOAD] Iniciando download: {filename}")
            return send_from_directory(app.config['PROCESSED_FOLDER'], filename)
        else:
            return jsonify({"status": "error", "message": "Arquivo não encontrado no servidor"}), 404
    except Exception as e:
        logger.error(f"[!] ERRO NO DOWNLOAD: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n{'='*40}\n   KL BYPASS ENGINE - READY\n{'='*40}")
    print(f"[*] Servidor Online: http://localhost:{port}")
    print(f"{'='*40}\n")
    app.run(host='0.0.0.0', port=port, debug=True)
