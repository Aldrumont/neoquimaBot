from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import requests
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'admin-secret-key-2024')

# Configurações
SHARED_API_URL = os.getenv('SHARED_DATABASE_URL', 'http://shared-database-api:8000')
LLM_API_URL = os.getenv('LLM_SERVICE_URL', 'http://llm-service:8003')
API_BASE_URL = f"{SHARED_API_URL}/api/v1/whatsapp"

@app.route('/')
def index():
    """Página principal do Admin UI"""
    return render_template('index.html')

@app.route('/users')
def users():
    """Página de gerenciamento de usuários"""
    return render_template('users.html')

@app.route('/llm')
def llm_config():
    """Página de configuração de LLM"""
    return render_template('llm.html')

# ========= ROTAS DE USUÁRIOS =========

@app.route('/api/users')
def get_users():
    """API para listar usuários"""
    try:
        response = requests.get(f"{API_BASE_URL}/users")
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Erro ao buscar usuários"}), 500
    except Exception as e:
        return jsonify({"error": f"Erro de conexão: {str(e)}"}), 500

@app.route('/api/users', methods=['POST'])
def create_user():
    """API para criar usuário"""
    try:
        user_data = request.json
        # Converter o número para formato internacional se necessário
        if not user_data.get('number', '').startswith('+'):
            user_data['number'] = f"+{user_data['number']}"
        
        response = requests.post(f"{API_BASE_URL}/users", json=user_data)
        if response.status_code == 201:
            return jsonify(response.json()), 201
        else:
            return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": f"Erro de conexão: {str(e)}"}), 500

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """API para atualizar usuário"""
    try:
        user_data = request.json
        # Converter o número para formato internacional se necessário
        if 'number' in user_data and not user_data['number'].startswith('+'):
            user_data['number'] = f"+{user_data['number']}"
        
        response = requests.put(f"{API_BASE_URL}/users/{user_id}", json=user_data)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": f"Erro de conexão: {str(e)}"}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """API para deletar usuário"""
    try:
        response = requests.delete(f"{API_BASE_URL}/users/{user_id}")
        if response.status_code == 204:
            return jsonify({"message": "Usuário deletado com sucesso"})
        else:
            return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": f"Erro de conexão: {str(e)}"}), 500

# ========= ROTAS DE LLM =========

@app.route('/api/llm/providers')
def get_llm_providers():
    """API para listar providers LLM disponíveis"""
    try:
        response = requests.get(f"{LLM_API_URL}/api/providers")
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Erro ao buscar providers"}), 500
    except Exception as e:
        return jsonify({"error": f"Erro de conexão: {str(e)}"}), 500

@app.route('/api/llm/config')
def get_llm_config():
    """API para obter configuração atual do LLM"""
    try:
        response = requests.get(f"{LLM_API_URL}/api/config")
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Erro ao buscar configuração"}), 500
    except Exception as e:
        return jsonify({"error": f"Erro de conexão: {str(e)}"}), 500

@app.route('/api/llm/config', methods=['PUT'])
def update_llm_config():
    """API para atualizar configuração do LLM"""
    try:
        config_data = request.json
        
        # Validar configuração antes de salvar
        validation_response = requests.post(
            f"{LLM_API_URL}/api/providers/validate",
            json=config_data
        )
        
        if validation_response.status_code == 200:
            validation_result = validation_response.json()
            if not validation_result.get("validation", {}).get("valid", False):
                return jsonify({
                    "error": "Configuração inválida",
                    "details": validation_result.get("validation", {}).get("errors", [])
                }), 400
        
        # Salvar no banco compartilhado
        response = requests.put(f"{SHARED_API_URL}/api/v1/llm/config", json=config_data)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": f"Erro de conexão: {str(e)}"}), 500

@app.route('/api/llm/health')
def get_llm_health():
    """API para verificar saúde do LLM Service"""
    try:
        response = requests.get(f"{LLM_API_URL}/health")
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Erro ao verificar saúde"}), 500
    except Exception as e:
        return jsonify({"error": f"Erro de conexão: {str(e)}"}), 500

@app.route('/api/llm/test', methods=['POST'])
def test_llm_config():
    """Testa configuração do LLM"""
    try:
        data = request.get_json()
        config = data.get('config', {})
        
        # Fazer teste via LLM Service
        test_response = requests.post(
            f"{LLM_API_URL}/api/providers/validate",
            json=config,
            timeout=30
        )
        
        if test_response.status_code == 200:
            return jsonify({
                'success': True,
                'message': 'Configuração válida!',
                'details': test_response.json()
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Erro na validação',
                'details': test_response.json() if test_response.content else 'Erro desconhecido'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao testar: {str(e)}'
        }), 500

@app.route('/api/llm/models/local')
def get_local_models():
    """Obtém modelos disponíveis localmente no Ollama"""
    try:
        response = requests.get(f"{LLM_API_URL}/api/models/local", timeout=10)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Erro ao buscar modelos locais'}), 500
    except Exception as e:
        return jsonify({'error': f'Erro: {str(e)}'}), 500

@app.route('/api/llm/models/api/<provider>')
def get_api_models(provider):
    """Obtém modelos disponíveis para um provider de API"""
    try:
        response = requests.get(f"{LLM_API_URL}/api/models/api/{provider}", timeout=10)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': f'Erro ao buscar modelos da API {provider}'}), 500
    except Exception as e:
        return jsonify({'error': f'Erro: {str(e)}'}), 500

@app.route('/api/llm/models/all')
def get_all_models():
    """Obtém todos os modelos disponíveis"""
    try:
        response = requests.get(f"{LLM_API_URL}/api/models/all", timeout=10)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Erro ao buscar todos os modelos'}), 500
    except Exception as e:
        return jsonify({'error': f'Erro: {str(e)}'}), 500

# ========= ROTAS DE SISTEMA =========

@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "service": "admin-ui",
        "timestamp": datetime.now().isoformat(),
        "shared_api_url": SHARED_API_URL,
        "llm_api_url": LLM_API_URL
    })

@app.route('/api/ngrok-status')
def ngrok_status():
    """Verifica o status do ngrok"""
    try:
        # Como estamos em container, vamos verificar se o webhook está respondendo
        # em vez de tentar acessar o ngrok diretamente
        
        # Verificar saúde do WhatsApp Gateway
        try:
            response = requests.get("http://whatsapp-gateway:8000/health", timeout=2)
            if response.status_code == 200:
                return jsonify({
                    "status": "connected",
                    "service": "whatsapp-gateway",
                    "message": "WhatsApp Gateway está funcionando"
                })
            else:
                return jsonify({
                    "status": "error",
                    "service": "whatsapp-gateway",
                    "message": f"Status HTTP: {response.status_code}"
                })
        except requests.exceptions.RequestException:
            return jsonify({
                "status": "disconnected",
                "service": "whatsapp-gateway",
                "message": "WhatsApp Gateway não está respondendo"
            })
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Erro ao verificar status: {str(e)}"
        })

if __name__ == '__main__':
    port = int(os.getenv('ADMIN_UI_PORT', 8080))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug) 