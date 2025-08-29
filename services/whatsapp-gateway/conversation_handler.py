import time
import uuid
from typing import Dict, List, Optional
import requests

from .database.conversation_manager import ConversationManager


class ConversationHandler:
    def __init__(self, db_session):
        self.conversation_manager = ConversationManager(db_session)
        self.llm_service_url = "http://llm-service:8003"
        self.rag_service_url = "http://rag-service:8004"
        
        # Comandos de reset
        self.reset_commands = [
            "novo assunto", "reset", "limpar", "nova conversa", 
            "começar de novo", "reiniciar", "zerar"
        ]
    
    def process_whatsapp_message(self, whatsapp_number: str, message: str, 
                                session_id: str = None) -> Dict:
        """Processa mensagem do WhatsApp com contexto completo"""
        start_time = time.time()
        correlation_id = str(uuid.uuid4())
        
        try:
            # 1. Verificar se é comando de reset
            if self._is_reset_command(message):
                self.conversation_manager.handle_reset_command(whatsapp_number, session_id)
                return {
                    "response": "✅ Nova conversa iniciada! Como posso ajudar?",
                    "correlation_id": correlation_id,
                    "session_reset": True
                }
            
            # 2. Obter ou criar sessão
            session = self.conversation_manager.get_or_create_session(whatsapp_number, session_id)
            
            # 3. Buscar contexto RAG
            rag_context = self._search_rag(message)
            
            # 4. Obter contexto da conversa
            conversation_context = self.conversation_manager.get_conversation_context(
                session.session_key
            )
            
            # 5. Gerar resposta com contexto completo
            response = self._generate_contextual_response(
                message, rag_context, conversation_context, correlation_id
            )
            
            # 6. Salvar turno do usuário
            user_turn = self.conversation_manager.add_conversation_turn(
                session.session_key, "user", message, rag_context, correlation_id
            )
            
            # 7. Salvar turno do assistente
            assistant_turn = self.conversation_manager.add_conversation_turn(
                session.session_key, "assistant", response["response"], 
                correlation_id=correlation_id
            )
            
            # 8. Atualizar resumo da sessão
            self.conversation_manager.update_rolling_summary(
                session.session_key, user_turn
            )
            
            # 9. Extrair memórias do usuário
            memories = self.conversation_manager.extract_user_memories(
                whatsapp_number, user_turn
            )
            
            # 10. Calcular métricas
            latency_ms = int((time.time() - start_time) * 1000)
            total_tokens = response.get("tokens_used", 0)
            rag_score_avg = self._calculate_rag_score_avg(rag_context)
            
            # 11. Log de auditoria
            self.conversation_manager.log_audit(
                session.session_key,
                "message_processed",
                {
                    "correlation_id": correlation_id,
                    "whatsapp_number": whatsapp_number,
                    "message_length": len(message),
                    "response_length": len(response["response"]),
                    "memories_extracted": len(memories),
                    "rag_results_count": len(rag_context.get("results", []))
                },
                total_tokens,
                rag_score_avg,
                latency_ms
            )
            
            return {
                "response": response["response"],
                "correlation_id": correlation_id,
                "session_key": session.session_key,
                "session_id": session.session_id,
                "rag_citations": rag_context.get("citations", []),
                "latency_ms": latency_ms,
                "tokens_used": total_tokens
            }
            
        except Exception as e:
            # Log de erro
            self.conversation_manager.log_audit(
                session.session_key if 'session' in locals() else "unknown",
                "error",
                {
                    "correlation_id": correlation_id,
                    "error": str(e),
                    "whatsapp_number": whatsapp_number
                }
            )
            
            return {
                "response": "❌ Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente.",
                "correlation_id": correlation_id,
                "error": True
            }
    
    def _is_reset_command(self, message: str) -> bool:
        """Verifica se a mensagem é um comando de reset"""
        message_lower = message.lower().strip()
        return any(cmd in message_lower for cmd in self.reset_commands)
    
    def _search_rag(self, query: str) -> Dict:
        """Busca no sistema RAG"""
        try:
            # Buscar em todas as coleções disponíveis
            collections = ["neoquima", "empresas", "pessoal", "test"]
            all_results = []
            
            for collection in collections:
                response = requests.post(
                    f"{self.rag_service_url}/search",
                    json={
                        "query": query,
                        "collection_name": collection,
                        "limit": 2,
                        "threshold": 0.0
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    results = response.json()
                    if results.get("results"):
                        all_results.extend(results["results"])
            
            # Ordenar por score e pegar os melhores
            all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
            best_results = all_results[:3]  # Top 3 resultados
            
            return {
                "results": best_results,
                "citations": [
                    {
                        "document_id": r.get("document_id"),
                        "chunk_id": r.get("chunk_id"),
                        "score": r.get("score"),
                        "collection": r.get("metadata", {}).get("filename", "unknown")
                    }
                    for r in best_results
                ],
                "query": query
            }
            
        except Exception as e:
            return {"results": [], "citations": [], "query": query, "error": str(e)}
    
    def _generate_contextual_response(self, message: str, rag_context: Dict, 
                                    conversation_context: Dict, correlation_id: str) -> Dict:
        """Gera resposta contextualizada usando LLM"""
        try:
            # Montar prompt estruturado
            prompt = self._build_structured_prompt(message, rag_context, conversation_context)
            
            # Chamar LLM Service
            response = requests.post(
                f"{self.llm_service_url}/api/chat",
                json={
                    "message": prompt,
                    "correlation_id": correlation_id,
                    "context": {
                        "rag_results": rag_context.get("results", []),
                        "conversation_history": conversation_context.get("recent_turns", []),
                        "rolling_summary": conversation_context.get("rolling_summary", "")
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "response": result.get("response", "Desculpe, não consegui gerar uma resposta."),
                    "tokens_used": result.get("tokens_used", 0)
                }
            else:
                return {
                    "response": "Desculpe, ocorreu um erro ao gerar a resposta.",
                    "tokens_used": 0
                }
                
        except Exception as e:
            return {
                "response": f"Desculpe, ocorreu um erro: {str(e)}",
                "tokens_used": 0
            }
    
    def _build_structured_prompt(self, message: str, rag_context: Dict, 
                                conversation_context: Dict) -> str:
        """Constrói prompt estruturado para o LLM"""
        
        # System prompt
        system_prompt = """Você é um assistente inteligente da Neoquima. 
        Responda de forma clara, profissional e baseada no contexto fornecido.
        Se não souber algo, seja honesto sobre isso."""
        
        # Contexto RAG
        rag_info = ""
        if rag_context.get("results"):
            rag_info = "\n\nINFORMAÇÕES RELEVANTES DOS DOCUMENTOS:\n"
            for i, result in enumerate(rag_context["results"], 1):
                rag_info += f"{i}. {result.get('content', '')[:200]}...\n"
        
        # Histórico da conversa
        conversation_history = ""
        if conversation_context.get("recent_turns"):
            conversation_history = "\n\nHISTÓRICO RECENTE DA CONVERSA:\n"
            for turn in conversation_context["recent_turns"][-4:]:  # Últimos 4 turnos
                role = "Usuário" if turn["role"] == "user" else "Assistente"
                conversation_history += f"{role}: {turn['content']}\n"
        
        # Resumo da sessão
        session_summary = ""
        if conversation_context.get("rolling_summary"):
            session_summary = f"\n\nRESUMO DA SESSÃO:\n{conversation_context['rolling_summary']}"
        
        # Instruções
        instructions = f"""
        
        INSTRUÇÕES:
        - Use as informações dos documentos quando relevante
        - Mantenha o contexto da conversa
        - Seja conciso mas completo
        - Cite as fontes quando usar informações dos documentos
        
        PERGUNTA ATUAL: {message}
        
        Responda de forma natural e contextualizada."""
        
        # Montar prompt completo
        full_prompt = f"{system_prompt}{rag_info}{conversation_history}{session_summary}{instructions}"
        
        return full_prompt
    
    def _calculate_rag_score_avg(self, rag_context: Dict) -> float:
        """Calcula score médio dos resultados RAG"""
        results = rag_context.get("results", [])
        if not results:
            return 0.0
        
        scores = [r.get("score", 0) for r in results]
        return sum(scores) / len(scores) if scores else 0.0
    
    def get_conversation_stats(self, whatsapp_number: str) -> Dict:
        """Obtém estatísticas da conversa do usuário"""
        try:
            # Buscar sessão ativa
            session = self.conversation_manager.get_or_create_session(whatsapp_number)
            
            # Buscar memórias
            memories = self.conversation_manager.get_user_memories(whatsapp_number)
            
            # Buscar contexto
            context = self.conversation_manager.get_conversation_context(session.session_key)
            
            return {
                "session_active": session.is_active,
                "turn_count": session.current_turn_count,
                "total_tokens": session.total_tokens_used,
                "memories_count": len(memories),
                "recent_turns": len(context.get("recent_turns", [])),
                "rolling_summary_length": len(context.get("rolling_summary", ""))
            }
            
        except Exception as e:
            return {"error": str(e)} 