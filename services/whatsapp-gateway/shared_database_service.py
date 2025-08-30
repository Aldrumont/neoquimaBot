import requests
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

class SharedDatabaseService:
    """Serviço para comunicação com a API compartilhada"""
    
    def __init__(self):
        self.base_url = os.getenv("SHARED_DATABASE_URL", "http://shared-database-api:8000")
        self.api_prefix = ""  # Sem prefixo para as APIs de contexto
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Faz requisição para a API compartilhada"""
        url = f"{self.base_url}{self.api_prefix}{endpoint}"
        
        print(f"[DEBUG] _make_request: {method} {url}")
        print(f"[DEBUG] Params: {params}")
        print(f"[DEBUG] Data: {data}")
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, params=params, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, timeout=10)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, timeout=10)
            elif method.upper() == "DELETE":
                response = requests.delete(url, timeout=10)
            else:
                raise ValueError(f"Método HTTP não suportado: {method}")
            
            print(f"[DEBUG] Response status: {response.status_code}")
            print(f"[DEBUG] Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            
            if response.status_code == 204:  # No Content
                return {"success": True}
            
            result = response.json()
            print(f"[DEBUG] Response JSON: {result}")
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na requisição para API compartilhada: {e}")
            return {"error": str(e)}
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
            return {"error": str(e)}
    
    def get_user_by_number(self, number: str) -> Optional[Dict[str, Any]]:
        """Busca usuário por número"""
        params = {"search": number}
        response = self._make_request("GET", "/whatsapp/users", params=params)
        
        if "error" in response:
            return None
        
        users = response.get("users", [])
        if users:
            return users[0]  # Retorna o primeiro usuário encontrado
        return None
    
    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Cria um novo usuário"""
        response = self._make_request("POST", "/whatsapp/users", data=user_data)
        
        if "error" in response:
            return None
        
        return response
    
    def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Atualiza um usuário existente"""
        response = self._make_request("PUT", f"/whatsapp/users/{user_id}", data=user_data)
        
        if "error" in response:
            return None
        
        return response
    
    def record_interaction(self, user_id: int, message: str) -> bool:
        """Registra uma interação do usuário"""
        data = {"message": message}
        response = self._make_request("POST", f"/whatsapp/users/{user_id}/interact", data=data)
        
        return "error" not in response
    
    def get_users_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas dos usuários"""
        response = self._make_request("GET", "/whatsapp/users")
        
        if "error" in response:
            return {"total": 0, "active": 0, "inactive": 0}
        
        total = response.get("total", 0)
        users = response.get("users", [])
        
        active = sum(1 for user in users if user.get("active", False))
        inactive = total - active
        
        return {
            "total": total,
            "active": active,
            "inactive": inactive
        }
    
    def search_users(self, search_term: str = "", limit: int = 100, skip: int = 0) -> Dict[str, Any]:
        """Busca usuários por termo"""
        params = {
            "search": search_term,
            "limit": limit,
            "skip": skip
        }
        response = self._make_request("GET", "/whatsapp/users", params=params)
        
        if "error" in response:
            return {"users": [], "total": 0}
        
        return response
    
    def get_conversation_history(self, session_key: str, limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Busca histórico de conversas de uma sessão"""
        import urllib.parse
        
        # TEMPORARIAMENTE - usar URL sem codificação para testar
        # encoded_session_key = urllib.parse.quote_plus(session_key)
        encoded_session_key = session_key
        
        params = {
            "session_key": encoded_session_key,
            "limit": limit
        }
        
        print(f"[DEBUG] Buscando histórico para session_key: {session_key}")
        print(f"[DEBUG] URL codificada: {encoded_session_key}")
        print(f"[DEBUG] Params: {params}")
        
        response = self._make_request("GET", "/conversations/turns", params=params)
        
        print(f"[DEBUG] Response da API: {response}")
        print(f"[DEBUG] Tipo da response: {type(response)}")
        
        if "error" in response:
            print(f"❌ Erro ao buscar histórico: {response['error']}")
            return None
        
        # Converter para formato esperado pelo conversation_handler
        turns = []
        for turn in response:
            print(f"[DEBUG] Processando turn: {turn}")
            turns.append({
                "role": turn.get("role", "unknown"),
                "content": turn.get("content", ""),
                "turn_number": turn.get("turn_number", 0),
                "created_at": turn.get("created_at", "")
            })
        
        print(f"[DEBUG] Turns processados: {turns}")
        
        # Ordenar por número do turno (crescente para manter ordem cronológica)
        turns.sort(key=lambda x: x["turn_number"])
        
        print(f"[DEBUG] Turns ordenados: {turns}")
        
        return turns

    # ========= MÉTODOS PARA SISTEMA DE CONTEXTO CONVERSACIONAL =========
    
    def get_active_session(self, whatsapp_number: str) -> Optional[Dict[str, Any]]:
        """Busca sessão ativa para um número de WhatsApp"""
        params = {"whatsapp_number": whatsapp_number, "active": True}
        response = self._make_request("GET", "/conversations/sessions", params=params)
        
        if "error" in response:
            return None
        
        # A API retorna uma lista diretamente
        if isinstance(response, list):
            sessions = response
        else:
            sessions = response.get("sessions", [])
        
        if sessions:
            return sessions[0]  # Retorna a primeira sessão ativa
        return None
    
    def create_conversation_session(self, session_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Cria uma nova sessão de conversa"""
        response = self._make_request("POST", "/conversations/sessions", data=session_data)
        
        if "error" in response:
            return None
        
        return response
    
    def deactivate_session(self, session_key: str) -> bool:
        """Desativa uma sessão de conversa"""
        data = {"is_active": False}
        response = self._make_request("PUT", f"/conversations/sessions/{session_key}", data=data)
        
        return "error" not in response
    
    def deactivate_session_by_number(self, whatsapp_number: str) -> bool:
        """Desativa todas as sessões ativas de um número"""
        # Primeiro buscar sessões ativas
        session = self.get_active_session(whatsapp_number)
        if session:
            return self.deactivate_session(session["session_key"])
        return True
    
    def update_session_activity(self, session_key: str) -> bool:
        """Atualiza a última atividade de uma sessão"""
        data = {"last_activity": datetime.now(timezone.utc).isoformat()}
        response = self._make_request("PUT", f"/conversations/sessions/{session_key}", data=data)
        
        return "error" not in response
    
    def update_session_turn_count(self, session_key: str, turn_count: int) -> bool:
        """Atualiza o contador de turnos de uma sessão"""
        data = {"current_turn_count": turn_count}
        response = self._make_request("PUT", f"/conversations/sessions/{session_key}", data=data)
        
        return "error" not in response
    
    def create_conversation_turn(self, turn_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Salva um turno da conversa no banco"""
        response = self._make_request("POST", "/conversations/turns", data=turn_data)
        
        if "error" in response:
            return None
        
        return response
    
    def create_user_memory(self, whatsapp_number: str, memory_type: str, memory_value: str, confidence: float) -> Optional[Dict[str, Any]]:
        """Cria uma nova memória do usuário"""
        memory_data = {
            "whatsapp_number": whatsapp_number,
            "memory_type": memory_type,
            "memory_value": memory_value,
            "confidence": confidence,
            "opt_in_status": True  # Assumir que usuário deu opt-in
        }
        
        response = self._make_request("POST", "/conversations/memories", data=memory_data)
        
        if "error" in response:
            return None
        
        return response
    
    def create_audit_log(self, audit_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Registra log de auditoria"""
        response = self._make_request("POST", "/conversations/audit", data=audit_data)
        
        if "error" not in response:
            return None
        
        return response
    
    def get_conversation_context(self, session_key: str) -> Optional[Dict[str, Any]]:
        """Obtém o contexto completo de uma conversa"""
        response = self._make_request("GET", f"/conversations/sessions/{session_key}/context")
        
        if "error" in response:
            return None
        
        return response
    
    def update_rolling_summary(self, session_key: str, summary: str) -> bool:
        """Atualiza o resumo acumulado de uma sessão"""
        data = {"rolling_summary": summary}
        response = self._make_request("PUT", f"/conversations/sessions/{session_key}", data=data)
        
        return "error" not in response 