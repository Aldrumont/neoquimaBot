import os
import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from database.models import User

log = logging.getLogger("uvicorn.error")

class WhatsAppService:
    """Serviço para envio de mensagens via WhatsApp Business API"""
    
    def __init__(self, shared_db_service=None):
        self.shared_db = shared_db_service
        self.token = None
        self.phone_id = None
        self.base_url = None
        
        # Tentar carregar configuração inicial
        self._load_config()
    
    def _load_config(self):
        """Carrega configuração do WhatsApp do banco de dados"""
        if not self.shared_db:
            log.warning("SharedDatabaseService não disponível. Usando variáveis de ambiente.")
            self.token = os.getenv("WHATSAPP_TOKEN")
            self.phone_id = os.getenv("WHATSAPP_PHONE_ID")
        else:
            try:
                config = self.shared_db.get_whatsapp_config()
                if config and not config.get("error"):
                    self.token = config.get("access_token")
                    self.phone_id = config.get("phone_number_id")
                    log.info("Configuração do WhatsApp carregada do banco de dados")
                else:
                    log.warning("Configuração do WhatsApp não encontrada no banco. Usando variáveis de ambiente.")
                    self.token = os.getenv("WHATSAPP_TOKEN")
                    self.phone_id = os.getenv("WHATSAPP_PHONE_ID")
            except Exception as e:
                log.error(f"Erro ao carregar configuração do WhatsApp: {e}")
                self.token = os.getenv("WHATSAPP_TOKEN")
                self.phone_id = os.getenv("WHATSAPP_PHONE_ID")
        
        if self.phone_id:
            self.base_url = f"https://graph.facebook.com/v23.0/{self.phone_id}/messages"
        
        if not self.token or not self.phone_id:
            log.warning("WhatsApp credentials not configured. Messages will be logged only.")
    
    def refresh_config(self):
        """Recarrega configuração do banco de dados"""
        if self.shared_db:
            self._load_config()
    
    def send_text_message(self, to_number: str, message: str) -> Dict[str, Any]:
        """
        Envia mensagem de texto para número do WhatsApp
        
        Args:
            to_number: Número no formato E.164 (+5511999998888)
            message: Texto da mensagem
            
        Returns:
            Dict com resultado do envio
        """
        # Remover + do número para API do WhatsApp
        clean_number = to_number.lstrip('+')
        
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_number,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Se não tiver credenciais, apenas log
        if not self.token or not self.phone_id:
            log.info(f"[WHATSAPP SIMULATION] TO: {to_number}, MESSAGE: {message}")
            return {
                "success": True,
                "message_id": "simulated_id",
                "error": None,
                "simulated": True
            }
        
        try:
            response = requests.post(
                self.base_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                log.info(f"WhatsApp message sent successfully to {to_number}")
                return {
                    "success": True,
                    "message_id": data.get("messages", [{}])[0].get("id"),
                    "error": None,
                    "simulated": False
                }
            else:
                error_msg = f"WhatsApp API error: {response.status_code} - {response.text}"
                log.error(error_msg)
                return {
                    "success": False,
                    "message_id": None,
                    "error": error_msg,
                    "simulated": False
                }
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error sending WhatsApp message: {str(e)}"
            log.error(error_msg)
            return {
                "success": False,
                "message_id": None,
                "error": error_msg,
                "simulated": False
            }
    
    def send_user_not_found_message(self, to_number: str) -> Dict[str, Any]:
        """Envia mensagem informando que usuário não está cadastrado"""
        message = (
            "❌ Acesso Negado\n\n"
            "Seu número não está cadastrado no nosso sistema.\n"
            "Para ter acesso, entre em contato com o administrador.\n\n"
            "📞 Suporte: Entre em contato para cadastro"
        )
        return self.send_text_message(to_number, message)
    
    def send_user_inactive_message(self, to_number: str) -> Dict[str, Any]:
        """Envia mensagem informando que usuário está inativo"""
        message = (
            "⚠️ Conta Inativa\n\n"
            "Seu acesso foi temporariamente suspenso.\n"
            "Entre em contato com o administrador para reativação.\n\n"
            "📞 Suporte: Solicite reativação da conta"
        )
        return self.send_text_message(to_number, message)
    
    def send_user_expired_message(self, to_number: str, expired_at: str) -> Dict[str, Any]:
        """Envia mensagem informando que usuário expirou"""
        # Formatar data de expiração
        try:
            expired_date = datetime.fromisoformat(expired_at.replace('Z', '+00:00'))
            formatted_date = expired_date.strftime("%d/%m/%Y às %H:%M")
        except:
            formatted_date = expired_at
        
        message = (
            f"⏰ Acesso Expirado\n\n"
            f"Seu acesso expirou em {formatted_date}.\n"
            f"Entre em contato com o administrador para renovação.\n\n"
            f"📞 Suporte: Solicite renovação do acesso"
        )
        return self.send_text_message(to_number, message)
    
    def send_test_response(self, to_number: str, message: str, user: Dict[str, Any]) -> Dict[str, Any]:
        """Envia resposta de teste com informações do usuário"""
        
        # Formatar última interação
        last_interact = "Nunca"
        if user.get("last_interact"):
            try:
                last_date_str = user["last_interact"]
                # Converter string ISO para datetime
                last_date = datetime.fromisoformat(last_date_str.replace('Z', '+00:00'))
                last_interact = last_date.strftime("%d/%m/%Y às %H:%M")
            except:
                last_interact = str(user["last_interact"])
        
        # Formatar tags
        tags = user.get("tags", [])
        tags_str = ", ".join(tags) if tags else "Nenhuma"
        
        # Status de expiração
        expiration_status = "Sem expiração"
        expires_at = user.get("expires_at")
        if expires_at:
            try:
                exp_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                if exp_date < datetime.now(exp_date.tzinfo):
                    expiration_status = f"❌ Expirado em {exp_date.strftime('%d/%m/%Y')}"
                else:
                    expiration_status = f"✅ Expira em {exp_date.strftime('%d/%m/%Y')}"
            except:
                expiration_status = f"Expira em {expires_at}"
        
        # Formatar data de cadastro
        created_at_str = "N/A"
        try:
            created_at = datetime.fromisoformat(user.get("created_at", "").replace('Z', '+00:00'))
            created_at_str = created_at.strftime("%d/%m/%Y às %H:%M")
        except:
            created_at_str = str(user.get("created_at", "N/A"))
        
        test_message = (
            f"🧪 TESTE EXECUTADO COM SUCESSO\n\n"
            f"📱 Número: {to_number}\n"
            f"💬 Mensagem recebida: \"{message}\"\n\n"
            f"📊 DADOS DO CADASTRO:\n"
            f"• ID: {user.get('id', 'N/A')}\n"
            f"• Nome: {user.get('name', 'Não informado')}\n"
            f"• Empresa: {user.get('company', 'Não informada')}\n"
            f"• Role: {user.get('role', 'N/A')}\n"
            f"• Status: {'✅ Ativo' if user.get('active', False) else '❌ Inativo'}\n"
            f"• Data de cadastro: {created_at_str}\n"
            f"• Última interação: {last_interact}\n"
            f"• Total de mensagens: {user.get('interact_count', 0)}\n"
            f"• Expiração: {expiration_status}\n"
            f"• Tags: {tags_str}\n"
            f"• Observações: {user.get('note', 'Nenhuma')}\n\n"
            f"✅ Sistema funcionando corretamente!"
        )
        
        return self.send_text_message(to_number, test_message)
    
    def is_test_message(self, message: str) -> bool:
        """
        Verifica se a mensagem é um comando de teste
        
        Args:
            message: Texto da mensagem recebida
            
        Returns:
            True se for mensagem de teste
        """
        if not message:
            return False
            
        message_lower = message.lower().strip()
        test_triggers = [
            "🧪",  # Emoji de tubo de ensaio
            "teste",
            "test",
            "debug",
            "/test",
            "/teste"
        ]
        
        # Verificar se contém algum dos triggers
        for trigger in test_triggers:
            if trigger in message_lower:
                return True
                
        return False
    
    def send_llm_response(self, to_number: str, response_text: str) -> Dict[str, Any]:
        """
        Envia resposta processada pelo LLM para o usuário
        
        Args:
            to_number: Número do usuário
            response_text: Resposta gerada pelo LLM
            
        Returns:
            Resultado do envio
        """
        return self.send_text_message(to_number, response_text)

# Instância global do serviço (será configurada pelo app.py)
whatsapp_service = None

def initialize_whatsapp_service(shared_db_service):
    """Inicializa o serviço WhatsApp com o shared_db"""
    global whatsapp_service
    whatsapp_service = WhatsAppService(shared_db_service)
    return whatsapp_service