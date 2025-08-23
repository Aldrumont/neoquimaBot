import os
import requests
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from database.models import User

log = logging.getLogger("uvicorn.error")

class WhatsAppService:
    """Serviço para envio de mensagens via WhatsApp Business API"""
    
    def __init__(self):
        self.token = os.getenv("WHATSAPP_TOKEN")
        self.phone_id = os.getenv("WHATSAPP_PHONE_ID")
        self.base_url = f"https://graph.facebook.com/v22.0/{self.phone_id}/messages"
        
        if not self.token or not self.phone_id:
            log.warning("WhatsApp credentials not configured. Messages will be logged only.")
    
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
    
    def send_test_response(self, to_number: str, message: str, user: User) -> Dict[str, Any]:
        """Envia resposta de teste com informações do usuário"""
        
        # Formatar última interação
        last_interact = "Nunca"
        if user.last_interact:
            try:
                last_date = user.last_interact
                last_interact = last_date.strftime("%d/%m/%Y às %H:%M")
            except:
                last_interact = str(user.last_interact)
        
        # Formatar tags
        tags_str = ", ".join(user.tags) if user.tags else "Nenhuma"
        
        # Status de expiração
        expiration_status = "Sem expiração"
        if user.expires_at:
            try:
                exp_date = user.expires_at
                if exp_date < datetime.now(exp_date.tzinfo):
                    expiration_status = f"❌ Expirado em {exp_date.strftime('%d/%m/%Y')}"
                else:
                    expiration_status = f"✅ Expira em {exp_date.strftime('%d/%m/%Y')}"
            except:
                expiration_status = f"Expira em {user.expires_at}"
        
        test_message = (
            f"🧪 TESTE EXECUTADO COM SUCESSO\n\n"
            f"📱 Número: {to_number}\n"
            f"💬 Mensagem recebida: \"{message}\"\n\n"
            f"📊 DADOS DO CADASTRO:\n"
            f"• ID: {user.id}\n"
            f"• Nome: {user.name or 'Não informado'}\n"
            f"• Empresa: {user.company or 'Não informada'}\n"
            f"• Role: {user.role}\n"
            f"• Status: {'✅ Ativo' if user.active else '❌ Inativo'}\n"
            f"• Cadastrado por: {user.added_by or 'Sistema'}\n"
            f"• Data de cadastro: {user.created_at.strftime('%d/%m/%Y às %H:%M')}\n"
            f"• Última interação: {last_interact}\n"
            f"• Total de mensagens: {user.interact_count}\n"
            f"• Expiração: {expiration_status}\n"
            f"• Tags: {tags_str}\n"
            f"• Observações: {user.note or 'Nenhuma'}\n\n"
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

# Instância global do serviço
whatsapp_service = WhatsAppService()