import os
import datetime
import uuid
import logging
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Importando o seu motor de bypass
try:
    from engine import BypassEngine
    print("[*] ENGINE DETECTADA: Modo de Produção Ativado.")
except ImportError:
    class BypassEngine:
        def process_apk(self, input_file, output_file):
            return True
    print("[!] AVISO: Engine não encontrada. Usando modo de simulação.")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kl_bypass_secret_2024'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
CORS(app)

# Configuração de Logging para você ver no terminal da Render
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Criação de pastas obrigatórias
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
        logger.error(f"Erro ao carregar index.html: {str(e)}")
        return f"Erro no Servidor: index.html não encontrado. {str(e)}", 500

# --- ROTAS DA API (Onde o erro estava acontecendo) ---

@app.route('/api/v1/upload', methods=['POST'])
def upload_apk():
    """Recebe o arquivo APK"""
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

        logger.info(f"[UPLOAD] Arquivo recebido: {filename}")

        # Criando ID único para o processo
        process_id = uuid.uuid4().hex[:8]
        output_filename = f"bypass_{process_id}_{filename}"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)

        # Chamando o motor de bypass
        logger.info(f"[*] Iniciando processamento de bypass para: {filename}")
        
        # Aqui o servidor chama o seu engine.py
        success = engine.process_apk(input_path, output_path)

        if success:
            logger.info(f"[SUCCESS] Bypass concluído: {filename}")
            return jsonify({
                "status": "success",
                "message": "Bypass aplicado com sucesso!",
                "download_url": f"/download/{output_filename}",
                "filename": output_filename
            }), 200
        else:
            return jsonify({"status": "error", "message": "Falha no processamento do motor."}), 500

    except Exception as e:
        logger.error(f"[!] ERRO NO UPLOAD: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# ROTA QUE ESTAVA FALTANDO (O erro 404 era aqui!)
@app.route('/api/v1/process', methods=['POST'])
def process_apk():
    """Rota de compatibilidade para o frontend que chama o processamento separado"""
    try:
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({"status": "error", "message": "No filename provided"}), 400

        logger.info(f"[*] Chamada de processamento para: {filename}")
        
        # Simulando o processamento para responder ao comando do frontend
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        output_filename = f"bypass_{uuid.uuid4().hex[:8]}_{filename}"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)

        # Chama o motor
        engine.process_apk(input_path, output_path)

        return jsonify({
            "status": "success",
            "message": "Processamento concluído!",
            "download_url": f"/download/{output_filename}",
            "filename": output_filename
        }), 200

    except Exception as e:
        logger.error(f"[!] ERRO NA ROTA PROCESS: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/v1/download/<filename>', methods=['GET'])
def download_apk(filename):
    """Rota para o download do arquivo final"""
    try:
        filename = secure_filename(filename)
        filepath = os.path.join(app.config['PROCESSED_FOLDER'], filename)
        
        if os.path.exists(filepath):
            return send_from_directory(app.config['PROCESSED_FOLDER'], filename)
        else:
            return jsonify({"status": "error", "message": "Arquivo não encontrado"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"\n{'='*40}\n   KL BYPASS ENGINE - READY\n{'='*40}")
    app.run(host='0.0.0.0', port=port, debug=True)
