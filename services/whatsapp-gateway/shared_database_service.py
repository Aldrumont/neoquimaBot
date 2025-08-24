import requests
import os
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

class SharedDatabaseService:
    """Serviço para comunicação com a API compartilhada"""
    
    def __init__(self):
        self.base_url = os.getenv("SHARED_DATABASE_URL", "http://shared-database-api:8000")
        self.api_prefix = "/api/v1"
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Faz requisição para a API compartilhada"""
        url = f"{self.base_url}{self.api_prefix}{endpoint}"
        
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
            
            response.raise_for_status()
            
            if response.status_code == 204:  # No Content
                return {"success": True}
            
            return response.json()
            
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
        """Busca usuários com filtros"""
        params = {
            "search": search_term,
            "limit": limit,
            "skip": skip
        }
        
        response = self._make_request("GET", "/whatsapp/users", params=params)
        
        if "error" in response:
            return {"users": [], "total": 0}
        
        return response 