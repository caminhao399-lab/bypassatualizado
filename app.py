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
    print("[*] Motor de Bypass (engine.py) detectado com sucesso!")
except ImportError:
    class BypassEngine:
        def process_apk(self, input_file, output_file):
            return True
    print("[!] AVISO: Engine não encontrada. Usando modo de simulação (Modo de Teste).")

# --- CONFIGURAÇÃO DO SERVIDOR ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'kl_bypass_ultra_secret_key_2024' # Chave de segurança do servidor
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PROCESSED_FOLDER'] = 'processed'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # Limite de 100MB para upload

CORS(app)

# Configuração de Logging (Para você ver tudo o que acontece no terminal)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# --- CRIAÇÃO DE ESTRUTURA DE DIRETÓRIOS ---
def setup_directories():
    for folder in [app.config['UPLOAD_FOLDER'], app.config['PROCESSED_FOLDER'], 'templates']:
        if not os.path.exists(folder):
            os.makedirs(folder)
            logger.info(f"[+] Pasta criada: {folder}")

setup_directories()

# Instanciando o motor de bypass
engine = BypassEngine()

# --- ROTAS DO PAINEL (FRONTEND) ---

@app.route('/')
def index():
    """Carrega a interface principal do seu Dashboard"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Erro ao carregar index.html: {str(e)}")
        return f"Erro no Servidor: Arquivo index.html não encontrado na pasta templates. {str(e)}", 500

# --- ROTAS DA API (BACKEND - O CORAÇÃO DO BYPASS) ---

@app.route('/api/v1/upload', methods=['POST'])
def upload_apk():
    """Recebe o APK, salva e inicia o processo de bypass"""
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "Nenhum arquivo enviado no payload"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "O nome do arquivo está vazio"}), 400

    # Validação de Extensão (Segurança)
    if not file.filename.lower().endswith('.apk'):
        return jsonify({"status": "error", "message": "Apenas arquivos .apk são permitidos"}), 400

    filename = secure_filename(file.filename)
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        # 1. Salva o arquivo original
        file.save(input_path)
        logger.info(f"[UPLOAD] Recebido: {filename} | Tamanho: {os.path.getsize(input_path)} bytes")

        # 2. Gera nome único para evitar sobreposição de arquivos
        unique_id = uuid.uuid4().hex[:8]
        output_filename = f"bypass_{unique_id}_{filename}"
        output_path = os.path.join(app.config['PROCESSED_FOLDER'], output_filename)

        # 3. Chama o Motor de Bypass (Onde a mágica acontece)
        logger.info(f"[*] Iniciando processamento de bypass para: {filename}")
        
        # Aqui o motor vai trabalhar (Ofuscação, Injeção, etc.)
        success = engine.process_apk(input_path, output_path)

        if success:
            logger.info(f"[SUCCESS] Bypass concluído para: {filename}")
            return jsonify({
                "status": "success",
                "message": "Bypass aplicado com sucesso! O arquivo está pronto.",
                "download_url": f"/download/{output_filename}",
                "filename": output_filename
            }), 200
        else:
            raise Exception("O motor de bypass falhou no processamento interno.")

    except Exception as e:
        logger.error(f"[!] ERRO NO PROCESSAMENTO: {str(e)}")
        return jsonify({"status": "error", "message": f"Falha no processamento: {str(e)}"}), 500

@app.route('/api/v1/download/<filename>', methods=['GET'])
def download_apk(filename):
    """Rota para o usuário baixar o APK já processado"""
    try:
        filename = secure_filename(filename)
        filepath = os.path.join(app.config['PROCESSED_FOLDER'], filename)
        
        if os.path.exists(filepath):
            logger.info(f"[DOWNLOAD] Iniciando download de: {filename}")
            return send_from_directory(app.config['PROCESSED_FOLDER'], filename)
        else:
            return jsonify({"status": "error", "message": "Arquivo não encontrado no servidor"}), 404
    except Exception as e:
        logger.error(f"[!] ERRO NO DOWNLOAD: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- INICIALIZAÇÃO DO SERVIDOR ---

if __name__ == '__main__':
    # Define a porta (Local ou Render)
    port = int(os.environ.get('PORT', 5000))
    
    print("\n" + "="*40)
    print("   KL BYPASS ENGINE - READY TO USE   ")
    print("="*40)
    print(f"[*] Status: Servidor Online")
    print(f"[*] Endereço: http://localhost:{port}")
    print(f"[*] Modo: Desenvolvimento (Debug ON)")
    print("="*40 + "\n")

    app.run(host='0.0.0.0', port=port, debug=True)
