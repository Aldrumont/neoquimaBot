from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import requests
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'admin-secret-key-2024')

# Configurações
SHARED_API_URL = os.getenv('SHARED_DATABASE_URL', 'http://localhost:8000')
API_BASE_URL = f"{SHARED_API_URL}/api/v1/whatsapp"

@app.route('/')
def index():
    """Página principal do Admin UI"""
    return render_template('index.html')

@app.route('/users')
def users():
    """Página de gerenciamento de usuários"""
    return render_template('users.html')

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

@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        "status": "healthy",
        "service": "admin-ui",
        "timestamp": datetime.now().isoformat(),
        "shared_api_url": SHARED_API_URL
    })

@app.route('/api/ngrok-status')
def ngrok_status():
    """Verifica o status do ngrok"""
    try:
        # Como estamos em container, vamos verificar se o webhook está respondendo
        # em vez de tentar acessar o ngrok diretamente
        
        # Verificar se o WhatsApp Gateway está rodando (porta 8081)
        try:
            response = requests.get("http://localhost:8081/health", timeout=2)
            if response.ok:
                # Se o gateway está rodando, assumir que ngrok está ativo
                # (já que testamos que está funcionando)
                return jsonify({
                    "status": "active",
                    "url": "https://9cdf1280a932.ngrok-free.app",
                    "local_addr": "http://localhost:8081",
                    "proto": "https",
                    "note": "Status inferido via gateway"
                })
        except:
            pass
        
        # Fallback: verificar se conseguimos acessar o webhook externo
        try:
            response = requests.get("https://9cdf1280a932.ngrok-free.app/webhook?hub.mode=subscribe&hub.verify_token=neoquima_webhook_2024&hub.challenge=test", timeout=5)
            if response.status_code in [200, 400, 401]:  # Qualquer resposta válida indica que está ativo
                return jsonify({
                    "status": "active",
                    "url": "https://9cdf1280a932.ngrok-free.app",
                    "local_addr": "http://localhost:8081",
                    "proto": "https",
                    "note": "Status verificado via webhook externo"
                })
        except:
            pass
        
        return jsonify({"status": "inactive", "note": "Não foi possível verificar o status"})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/stats/messages-today')
def messages_today():
    """Conta mensagens/interações de hoje"""
    try:
        # Buscar usuários e contar interações
        response = requests.get(f"{API_BASE_URL}/users")
        if response.ok:
            data = response.json()
            users = data.get('users', [])
            
            # Contar interações de hoje
            today = datetime.now().date()
            today_messages = 0
            
            for user in users:
                if user.get('last_interact'):
                    try:
                        last_interact = datetime.fromisoformat(user['last_interact'].replace('Z', '+00:00'))
                        if last_interact.date() == today:
                            today_messages += user.get('interact_count', 0)
                    except:
                        continue
            
            return jsonify({
                "today_messages": today_messages,
                "total_users": len(users),
                "active_users": len([u for u in users if u.get('active')])
            })
        else:
            return jsonify({"today_messages": 0, "error": "Failed to fetch users"})
            
    except Exception as e:
        return jsonify({"today_messages": 0, "error": str(e)})

if __name__ == '__main__':
    port = int(os.getenv('ADMIN_UI_PORT', 8080))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug) 