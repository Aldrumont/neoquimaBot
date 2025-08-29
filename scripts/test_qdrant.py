#!/usr/bin/env python3
"""
Script de teste para o Qdrant Vector Database
Testa operações básicas: criar coleção, inserir vetores, buscar
"""

import requests
import json
import time
from typing import List, Dict, Any

class QdrantTester:
    def __init__(self, base_url: str = "http://localhost:6333"):
        self.base_url = base_url
        self.collection_name = "test_collection"
        
    def test_health(self) -> bool:
        """Testa se o Qdrant está respondendo"""
        try:
            response = requests.get(f"{self.base_url}/collections")
            if response.status_code == 200:
                print("✅ Qdrant está respondendo")
                return True
            else:
                print(f"❌ Qdrant retornou status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erro ao conectar com Qdrant: {e}")
            return False
    
    def create_collection(self, vector_size: int = 1536) -> bool:
        """Cria uma coleção de teste"""
        try:
            payload = {
                "vectors": {
                    "size": vector_size,
                    "distance": "Cosine"
                }
            }
            
            response = requests.put(
                f"{self.base_url}/collections/{self.collection_name}",
                json=payload
            )
            
            if response.status_code == 200:
                print(f"✅ Coleção '{self.collection_name}' criada com sucesso")
                return True
            elif response.status_code == 400 and "already exists" in response.text:
                print(f"ℹ️ Coleção '{self.collection_name}' já existe")
                return True
            else:
                print(f"❌ Erro ao criar coleção: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao criar coleção: {e}")
            return False
    
    def insert_test_vectors(self, count: int = 5) -> bool:
        """Insere vetores de teste na coleção"""
        try:
            # Gerar vetores de teste (simulando embeddings reais)
            vectors = []
            for i in range(count):
                # Vetor aleatório de 1536 dimensões (simulando OpenAI embeddings)
                import random
                vector = [random.uniform(-1, 1) for _ in range(1536)]
                
                payload = {
                    "points": [
                        {
                            "id": i + 1,
                            "vector": vector,
                            "payload": {
                                "text": f"Documento de teste {i + 1}",
                                "category": "teste",
                                "metadata": {
                                    "source": "script_teste",
                                    "timestamp": time.time()
                                }
                            }
                        }
                    ]
                }
                
                response = requests.put(
                    f"{self.base_url}/collections/{self.collection_name}/points",
                    json=payload
                )
                
                if response.status_code == 200:
                    print(f"✅ Vetor {i + 1} inserido com sucesso")
                else:
                    print(f"❌ Erro ao inserir vetor {i + 1}: {response.status_code}")
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao inserir vetores: {e}")
            return False
    
    def search_vectors(self, query_vector: List[float] = None, limit: int = 3) -> bool:
        """Testa busca vetorial"""
        try:
            if query_vector is None:
                # Gerar vetor de consulta aleatório
                import random
                query_vector = [random.uniform(-1, 1) for _ in range(1536)]
            
            payload = {
                "vector": query_vector,
                "limit": limit,
                "with_payload": True,
                "with_vector": False
            }
            
            response = requests.post(
                f"{self.base_url}/collections/{self.collection_name}/points/search",
                json=payload
            )
            
            if response.status_code == 200:
                results = response.json()
                print(f"✅ Busca realizada com sucesso")
                print(f"   Resultados encontrados: {len(results['result'])}")
                
                for i, result in enumerate(results['result']):
                    print(f"   {i + 1}. ID: {result['id']}, Score: {result['score']:.4f}")
                    if 'payload' in result:
                        print(f"      Texto: {result['payload'].get('text', 'N/A')}")
                
                return True
            else:
                print(f"❌ Erro na busca: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erro na busca: {e}")
            return False
    
    def get_collection_info(self) -> bool:
        """Obtém informações da coleção"""
        try:
            response = requests.get(f"{self.base_url}/collections/{self.collection_name}")
            
            if response.status_code == 200:
                info = response.json()
                print(f"✅ Informações da coleção '{self.collection_name}':")
                print(f"   Status: {info['result']['status']}")
                print(f"   Pontos: {info['result']['points_count']}")
                print(f"   Segmentos: {info['result']['segments_count']}")
                print(f"   Tamanho do vetor: {info['result']['config']['params']['vectors']['size']}")
                print(f"   Distância: {info['result']['config']['params']['vectors']['distance']}")
                return True
            else:
                print(f"❌ Erro ao obter informações: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao obter informações: {e}")
            return False
    
    def cleanup(self) -> bool:
        """Remove a coleção de teste"""
        try:
            response = requests.delete(f"{self.base_url}/collections/{self.collection_name}")
            
            if response.status_code == 200:
                print(f"✅ Coleção '{self.collection_name}' removida com sucesso")
                return True
            else:
                print(f"❌ Erro ao remover coleção: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao remover coleção: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Executa todos os testes"""
        print("🚀 Iniciando testes do Qdrant...")
        print("=" * 50)
        
        # Teste 1: Health check
        if not self.test_health():
            return False
        
        print()
        
        # Teste 2: Criar coleção
        if not self.create_collection():
            return False
        
        print()
        
        # Teste 3: Inserir vetores
        if not self.insert_test_vectors():
            return False
        
        print()
        
        # Teste 4: Informações da coleção
        if not self.get_collection_info():
            return False
        
        print()
        
        # Teste 5: Busca vetorial
        if not self.search_vectors():
            return False
        
        print()
        print("✅ Todos os testes passaram com sucesso!")
        print("=" * 50)
        
        # Perguntar se quer limpar
        cleanup = input("🧹 Deseja remover a coleção de teste? (s/n): ").lower().strip()
        if cleanup in ['s', 'sim', 'y', 'yes']:
            self.cleanup()
        
        return True

def main():
    """Função principal"""
    print("🧪 Testador do Qdrant Vector Database")
    print("Este script testa operações básicas do Qdrant")
    print()
    
    # Verificar se o Qdrant está rodando
    tester = QdrantTester()
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⏹️ Testes interrompidos pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro inesperado: {e}")

if __name__ == "__main__":
    main() 