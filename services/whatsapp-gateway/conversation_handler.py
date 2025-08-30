#!/usr/bin/env python3
"""
ConversationHandler - Integra sistema de contexto conversacional com WhatsApp Gateway
"""

import logging
import uuid
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple

# Configuração de logging
log = logging.getLogger(__name__)

class ConversationHandler:
    """
    Handler principal para gerenciar conversas do WhatsApp com contexto conversacional
    """
    
    def __init__(self, shared_db_service, whatsapp_service):
        self.shared_db = shared_db_service
        self.whatsapp = whatsapp_service
        
        # URLs dos serviços
        self.llm_url = "http://llm-service:8003/api/chat"
        self.rag_url = "http://rag-service:8004/api/search"
        
        # Configurações padrão
        self.default_config = {
            "max_total_tokens": 1500,
            "summary_tokens": 200,
            "conversation_window_tokens": 800,
            "rag_context_tokens": 500,
            "session_ttl_minutes": 30,
            "max_conversation_turns": 6
        }
    
    def process_whatsapp_message(
        self, 
        whatsapp_number: str, 
        message_text: str, 
        user_data: Dict
    ) -> Dict:
        """
        Processa mensagem do WhatsApp com contexto conversacional completo
        
        Args:
            whatsapp_number: Número do WhatsApp (E.164)
            message_text: Texto da mensagem
            user_data: Dados do usuário do banco
            
        Returns:
            Dict com resultado do processamento
        """
        start_time = datetime.now()
        correlation_id = str(uuid.uuid4())
        
        log.info(f"[CONTEXTO] Iniciando processamento de mensagem: {correlation_id}")
        log.info(f"[CONTEXTO] Número: {whatsapp_number}, Mensagem: {message_text[:100]}...")
        
        try:
            log.info(f"[{correlation_id}] Processando mensagem de {whatsapp_number}")
            
            # 1. Verificar se é comando de reset
            if self._is_reset_command(message_text):
                return self._handle_reset_command(whatsapp_number, correlation_id)
            
            # 2. Obter ou criar sessão de conversa
            session_data = self._get_or_create_session(whatsapp_number, correlation_id)
            if not session_data:
                return self._create_error_response("Erro ao criar sessão", correlation_id)
            
            # 3. Buscar contexto RAG se relevante
            rag_context = None
            if not self._is_reset_command(message_text):
                rag_context = self._search_rag(message_text, correlation_id)
            
            # 4. Gerar resposta contextualizada
            response_data = self._generate_contextual_response(
                whatsapp_number, 
                message_text, 
                session_data, 
                rag_context, 
                correlation_id
            )
            
            # 5. Enviar resposta via WhatsApp
            send_result = self.whatsapp.send_text_message(
                whatsapp_number, 
                response_data["response"]
            )
            
            # 6. Log de auditoria
            self._log_audit(
                session_data["session_key"],
                correlation_id,
                "whatsapp_message_processed",
                {
                    "whatsapp_number": whatsapp_number,
                    "message_length": len(message_text),
                    "response_length": len(response_data["response"]),
                    "rag_results": len(rag_context["citations"]) if rag_context and rag_context.get("citations") else 0,
                    "session_turn": session_data["current_turn_count"]
                },
                response_data.get("total_tokens", 0),
                rag_context["average_score"] if rag_context and rag_context.get("average_score") else 0.0,
                int((datetime.now() - start_time).total_seconds() * 1000)
            )
            
            return {
                "status": "success",
                "correlation_id": correlation_id,
                "session_key": session_data["session_key"],
                "response": response_data["response"],
                "rag_context": rag_context,
                "message_sent": send_result["success"]
            }
            
        except Exception as e:
            log.error(f"[{correlation_id}] Erro ao processar mensagem: {str(e)}")
            
            # Fallback: resposta de erro amigável
            fallback_response = (
                f"Olá {user_data.get('name', 'usuário')}! 👋\n\n"
                f"🔧 Ocorreu um erro ao processar sua mensagem.\n"
                f"Tente novamente em alguns instantes ou digite 'novo assunto' para recomeçar."
            )
            
            # Enviar resposta de fallback
            send_result = self.whatsapp.send_text_message(whatsapp_number, fallback_response)
            
            return {
                "status": "error",
                "correlation_id": correlation_id,
                "error": str(e),
                "fallback_sent": send_result["success"]
            }
    
    def _is_reset_command(self, message_text: str) -> bool:
        """Verifica se a mensagem é um comando de reset"""
        reset_commands = [
            "novo assunto", "reset", "recomeçar", "nova conversa",
            "limpar", "limpar conversa", "começar de novo"
        ]
        
        message_lower = message_text.lower().strip()
        return any(cmd in message_lower for cmd in reset_commands)
    
    def _handle_reset_command(self, whatsapp_number: str, correlation_id: str) -> Dict:
        """Processa comando de reset de conversa"""
        try:
            log.info(f"[{correlation_id}] Comando de reset detectado para {whatsapp_number}")
            
            # Desativar sessão anterior
            self.shared_db.deactivate_session_by_number(whatsapp_number)
            
            # Criar nova sessão
            session_data = self._create_new_session(whatsapp_number, correlation_id)
            
            # Resposta de confirmação
            reset_response = "✅ Nova conversa iniciada! Como posso ajudar?"
            
            # Enviar resposta
            send_result = self.whatsapp.send_text_message(whatsapp_number, reset_response)
            
            # Log de auditoria
            self._log_audit(
                session_data["session_key"],
                correlation_id,
                "conversation_reset",
                {"whatsapp_number": whatsapp_number, "reset_type": "manual"},
                0, 0.0, 0
            )
            
            return {
                "status": "reset_success",
                "correlation_id": correlation_id,
                "session_key": session_data["session_key"],
                "response": reset_response,
                "message_sent": send_result["success"]
            }
            
        except Exception as e:
            log.error(f"[{correlation_id}] Erro no reset: {str(e)}")
            return self._create_error_response(f"Erro no reset: {str(e)}", correlation_id)
    
    def _get_or_create_session(self, whatsapp_number: str, correlation_id: str) -> Optional[Dict]:
        """Obtém ou cria uma sessão de conversa"""
        try:
            # Buscar sessão ativa
            session = self.shared_db.get_active_session(whatsapp_number)
            
            if session:
                # Verificar se não expirou
                if self._is_session_expired(session):
                    log.info(f"[{correlation_id}] Sessão expirada, criando nova")
                    self.shared_db.deactivate_session(session["session_key"])
                    session = None
                else:
                    # Atualizar última atividade
                    self.shared_db.update_session_activity(session["session_key"])
            
            if not session:
                # Criar nova sessão
                session = self._create_new_session(whatsapp_number, correlation_id)
            
            return session
            
        except Exception as e:
            log.error(f"[{correlation_id}] Erro ao obter/criar sessão: {str(e)}")
            return None
    
    def _create_new_session(self, whatsapp_number: str, correlation_id: str) -> Dict:
        """Cria uma nova sessão de conversa"""
        session_id = str(uuid.uuid4())
        session_key = f"{whatsapp_number}:{session_id}"
        
        session_data = {
            "session_key": session_key,
            "whatsapp_number": whatsapp_number,
            "session_id": session_id,
            "config_id": 1,  # Configuração padrão
            "current_turn_count": 0
        }
        
        # Criar no banco e obter dados retornados
        created_session = self.shared_db.create_conversation_session(session_data)
        
        if created_session and "error" not in created_session:
            # Usar dados retornados pelo banco
            session_data.update(created_session)
            log.info(f"[{correlation_id}] Nova sessão criada: {session_key}")
        else:
            log.error(f"[{correlation_id}] Erro ao criar sessão no banco: {created_session}")
            # Criar sessão local se falhar no banco
            session_data["id"] = None
            session_data["created_at"] = datetime.now(timezone.utc).isoformat()
            session_data["last_activity"] = session_data["created_at"]
        
        return session_data
    
    def _is_session_expired(self, session: Dict) -> bool:
        """Verifica se a sessão expirou"""
        if not session.get("last_activity"):
            return False
        
        try:
            last_activity = datetime.fromisoformat(
                session["last_activity"].replace('Z', '+00:00')
            )
            ttl_minutes = self.default_config["session_ttl_minutes"]
            expiry_time = last_activity + timedelta(minutes=ttl_minutes)
            
            return datetime.now(timezone.utc) > expiry_time
            
        except Exception:
            return False
    
    def _search_rag(self, query: str, correlation_id: str) -> Optional[Dict]:
        """Busca contexto RAG para a mensagem"""
        try:
            log.info(f"[{correlation_id}] Buscando RAG para: {query[:50]}...")
            
            # Fazer busca no RAG Service
            rag_payload = {
                "query": query,
                "collection": "neoquima",  # Coleção padrão
                "limit": 3
            }
            
            rag_response = requests.post(
                self.rag_url, 
                json=rag_payload, 
                timeout=10
            )
            
            if rag_response.status_code == 200:
                rag_data = rag_response.json()
                
                if rag_data.get("results") and len(rag_data["results"]) > 0:
                    citations = []
                    total_score = 0.0
                    
                    for result in rag_data["results"]:
                        citation = {
                            "document_id": result.get("document_id", "unknown"),
                            "chunk_id": result.get("chunk_id", "unknown"),
                            "score": result.get("score", 0.0),
                            "content": result.get("content", "")[:200] + "..."
                        }
                        citations.append(citation)
                        total_score += citation["score"]
                    
                    average_score = total_score / len(citations) if citations else 0.0
                    
                    log.info(f"[{correlation_id}] RAG: {len(citations)} resultados, score médio: {average_score:.2f}")
                    
                    return {
                        "citations": citations,
                        "average_score": average_score,
                        "collection": "neoquima",
                        "query": query
                    }
            
            log.info(f"[{correlation_id}] RAG: Nenhum resultado relevante")
            return None
            
        except Exception as e:
            log.warning(f"[{correlation_id}] Erro na busca RAG: {str(e)}")
            return None
    
    def _generate_contextual_response(
        self, 
        whatsapp_number: str, 
        message_text: str, 
        session_data: Dict, 
        rag_context: Optional[Dict], 
        correlation_id: str
    ) -> Dict:
        """Gera resposta contextualizada usando LLM + contexto"""
        try:
            # Construir prompt estruturado
            prompt = self._build_structured_prompt(
                message_text, 
                session_data, 
                rag_context
            )
            
            # Chamar LLM
            llm_payload = {
                "message": prompt,
                "user_id": str(whatsapp_number),
                "user_name": "usuário WhatsApp",
                "correlation_id": correlation_id
            }
            
            log.info(f"[{correlation_id}] Enviando para LLM: {len(prompt)} chars")
            
            llm_response = requests.post(
                self.llm_url, 
                json=llm_payload, 
                timeout=60  # Aumentado de 30 para 60 segundos
            )
            
            if llm_response.status_code == 200:
                llm_data = llm_response.json()
                ai_response = llm_data.get("response", "Desculpe, não consegui processar sua mensagem.")
                total_tokens = llm_data.get("total_tokens", 0)
                
                log.info(f"[{correlation_id}] Resposta LLM: {len(ai_response)} chars, {total_tokens} tokens")
                
                # Salvar turno da conversa
                self._save_conversation_turn(
                    session_data["session_key"],
                    session_data["current_turn_count"] + 1,
                    "user",
                    message_text,
                    correlation_id,
                    rag_context
                )
                
                self._save_conversation_turn(
                    session_data["session_key"],
                    session_data["current_turn_count"] + 2,
                    "assistant",
                    ai_response,
                    correlation_id
                )
                
                # Atualizar sessão
                self.shared_db.update_session_turn_count(
                    session_data["session_key"],
                    session_data["current_turn_count"] + 2
                )
                
                # Extrair memórias do usuário
                self._extract_user_memories(whatsapp_number, message_text, ai_response, correlation_id)
                
                return {
                    "response": ai_response,
                    "total_tokens": total_tokens,
                    "rag_context": rag_context
                }
 
            else:
                log.error(f"[{correlation_id}] Erro LLM: {llm_response.status_code}")
                return self._create_fallback_response(message_text)
                
        except Exception as e:
            log.error(f"[{correlation_id}] Erro ao gerar resposta: {str(e)}")
            return self._create_fallback_response(message_text)
    
    def _build_structured_prompt(
        self, 
        message_text: str, 
        session_data: Dict, 
        rag_context: Optional[Dict]
    ) -> str:
        """Constrói prompt estruturado para o LLM"""
        print(f"[DEBUG] _build_structured_prompt chamado!")
        print(f"[DEBUG] session_data: {session_data}")
        print(f"[DEBUG] message_text: {message_text}")
        
        log.info(f"[CONTEXTO] Iniciando construção do prompt para sessão: {session_data.get('session_key')}")
        log.info(f"[CONTEXTO] Mensagem: {message_text[:100]}...")
        
        prompt_parts = []
        
        # Contexto da sessão
        if session_data.get("rolling_summary"):
            prompt_parts.append(f"📝 RESUMO DA CONVERSA:\n{session_data['rolling_summary']}\n")
            log.info(f"[CONTEXTO] Resumo incluído: {session_data['rolling_summary'][:100]}...")
        else:
            log.info("[CONTEXTO] Nenhum resumo disponível para a sessão")
            print("[DEBUG] Nenhum resumo disponível")
        
        print(f"[DEBUG] Após resumo, prompt_parts tem {len(prompt_parts)} elementos")
        
        # HISTÓRICO DE CONVERSAS ANTERIORES
        try:
            print("[DEBUG] Tentando buscar histórico...")
            # Buscar histórico de conversas da sessão
            conversation_history = self.shared_db.get_conversation_history(
                session_data["session_key"], 
                limit=10  # Últimas 10 interações
            )
            
            print(f"[DEBUG] Histórico retornado: {conversation_history}")
            
            if conversation_history and len(conversation_history) > 0:
                prompt_parts.append("💬 HISTÓRICO DA CONVERSA:\n")
                
                for turn in conversation_history:
                    role_emoji = "👤" if turn["role"] == "user" else "🤖"
                    prompt_parts.append(f"{role_emoji} {turn['role'].upper()}: {turn['content']}")
                
                prompt_parts.append("")  # Linha em branco para separar
                
                log.info(f"[CONTEXTO] Histórico incluído: {len(conversation_history)} turnos")
                print(f"[DEBUG] Histórico incluído: {len(conversation_history)} turnos")
            else:
                log.info("[CONTEXTO] Nenhum histórico encontrado para a sessão")
                print("[DEBUG] Nenhum histórico encontrado")
                
        except Exception as e:
            log.error(f"[CONTEXTO] Erro ao buscar histórico: {str(e)}")
            print(f"[DEBUG] Erro ao buscar histórico: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Contexto RAG
        if rag_context and rag_context.get("citations"):
            prompt_parts.append("📚 INFORMAÇÕES RELEVANTES:\n")
            for i, citation in enumerate(rag_context["citations"], 1):
                prompt_parts.append(f"{i}. {citation['content']}")
            prompt_parts.append("")
        
        # Instruções para o LLM
        prompt_parts.append(
            "🤖 INSTRUÇÕES:\n"
            "Você é um assistente virtual da Neoquima, empresa especializada em tratamento de água.\n"
            "Responda de forma clara, profissional e útil.\n"
            "IMPORTANTE: Use o histórico da conversa acima para manter contexto e continuidade.\n"
            "Se houver informações relevantes acima, use-as para enriquecer sua resposta.\n"
            "Seja conciso mas completo.\n\n"
            "💬 PERGUNTA DO USUÁRIO:\n"
        )
        
        prompt_parts.append(message_text)
        
        final_prompt = "\n".join(prompt_parts)
        
        # LOG COMPLETO DO PROMPT PARA DEBUG
        log.info(f"[CONTEXTO] PROMPT COMPLETO ENVIADO PARA LLM:")
        log.info(f"[CONTEXTO] {'='*50}")
        log.info(f"[CONTEXTO] {final_prompt}")
        log.info(f"[CONTEXTO] {'='*50}")
        log.info(f"[CONTEXTO] Tamanho total: {len(final_prompt)} caracteres")
        
        return final_prompt
    
    def _save_conversation_turn(
        self, 
        session_key: str, 
        turn_number: int, 
        role: str, 
        content: str, 
        correlation_id: str, 
        rag_context: Optional[Dict] = None
    ):
        """Salva um turno da conversa no banco"""
        try:
            turn_data = {
                "session_key": session_key,
                "turn_number": turn_number,
                "role": role,
                "content": content,
                "correlation_id": correlation_id,
                "tokens_used": len(content.split())  # Estimativa simples
            }
            
            if rag_context:
                turn_data.update({
                    "rag_citations": rag_context.get("citations", []),
                    "rag_collection": rag_context.get("collection"),
                    "rag_query": rag_context.get("query")
                })
            
            self.shared_db.create_conversation_turn(turn_data)
            
        except Exception as e:
            log.error(f"[{correlation_id}] Erro ao salvar turno: {str(e)}")
    
    def _extract_user_memories(
        self, 
        whatsapp_number: str, 
        user_message: str, 
        ai_response: str, 
        correlation_id: str
    ):
        """Extrai e salva memórias do usuário"""
        try:
            # Memórias simples baseadas em palavras-chave
            memories = []
            
            # Empresa
            if any(word in user_message.lower() for word in ["empresa", "trabalho", "companhia"]):
                memories.append({
                    "type": "empresa",
                    "value": "Usuário mencionou empresa/trabalho",
                    "confidence": 0.8
                })
            
            # Produtos
            if any(word in user_message.lower() for word in ["produto", "nq-", "químico", "tratamento"]):
                memories.append({
                    "type": "produto",
                    "value": "Usuário interessado em produtos químicos",
                    "confidence": 0.9
                })
            
            # Localização
            if any(word in user_message.lower() for word in ["cidade", "estado", "região", "local"]):
                memories.append({
                    "type": "localizacao",
                    "value": "Usuário mencionou localização",
                    "confidence": 0.7
                })
            
            # Salvar memórias
            for memory in memories:
                self.shared_db.create_user_memory(
                    whatsapp_number,
                    memory["type"],
                    memory["value"],
                    memory["confidence"]
                )
                
            if memories:
                log.info(f"[{correlation_id}] Memórias extraídas: {len(memories)}")
                
        except Exception as e:
            log.warning(f"[{correlation_id}] Erro ao extrair memórias: {str(e)}")
    
    def _log_audit(
        self, 
        session_key: str, 
        correlation_id: str, 
        action: str, 
        details: Dict, 
        total_tokens: int, 
        rag_score_average: float, 
        latency_ms: int
    ):
        """Registra log de auditoria"""
        try:
            audit_data = {
                "session_key": session_key,
                "correlation_id": correlation_id,
                "action": action,
                "details": details,
                "total_tokens": total_tokens,
                "rag_score_average": rag_score_average,
                "latency_ms": latency_ms
            }
            
            self.shared_db.create_audit_log(audit_data)
            
        except Exception as e:
            log.error(f"[{correlation_id}] Erro ao logar auditoria: {str(e)}")
    
    def _create_error_response(self, error_message: str, correlation_id: str) -> Dict:
        """Cria resposta de erro padronizada"""
        return {
            "status": "error",
            "correlation_id": correlation_id,
            "error": error_message,
            "response": "Desculpe, ocorreu um erro. Tente novamente."
        }
    
    def _create_fallback_response(self, original_message: str) -> Dict:
        """Cria resposta de fallback quando LLM falha"""
        fallback_text = (
            "Olá! 👋\n\n"
            f"Recebi sua mensagem: \"{original_message}\"\n\n"
            "🔧 O módulo de IA está temporariamente indisponível.\n"
            "Tente novamente em alguns instantes ou digite 'novo assunto' para recomeçar."
        )
        
        return {
            "response": fallback_text,
            "total_tokens": len(fallback_text.split()),
            "rag_context": None
        } 