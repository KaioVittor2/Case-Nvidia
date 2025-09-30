"""
Deep Research Task - Orquestração da pesquisa em múltiplas camadas
Baseado na função deeper_research_topic do notebook
"""

import json
from typing import List, Dict, Any
from crewai import Task
from src.agents.deep_research_agent import DeepResearchAgent, create_deep_research_crewai_agent


class DeepResearchTask:
    """Task para orquestrar pesquisa profunda em múltiplas camadas"""
    
    def __init__(self):
        self.agent = create_deep_research_crewai_agent()
        self.deep_research = DeepResearchAgent()
    
    def execute_deep_research(self, vc_list: List[str]) -> Dict[str, Any]:
        """
        Executa pesquisa profunda em duas camadas para encontrar startups
        
        Args:
            vc_list: Lista de nomes de VCs para pesquisar
            
        Returns:
            Dicionário com resultados estruturados e metadados
        """
        # Construir query inicial
        query = f"startups investidas por {', '.join(vc_list)}"
        print(f"\n🔍 Iniciando pesquisa profunda para VCs: {', '.join(vc_list)}")
        
        try:
            # ============================================
            # CAMADA 1: Pesquisa Inicial
            # ============================================
            print("\n📊 CAMADA 1: Pesquisa inicial...")
            initial_sources = self.deep_research.search_web_exa(query, num_results=6)
            
            if not initial_sources:
                print("⚠️ Nenhuma fonte encontrada na pesquisa inicial")
                return self._empty_result(vc_list, query)
            
            print(f"✓ Encontradas {len(initial_sources)} fontes na pesquisa inicial")
            
            # ============================================
            # Geração de Pergunta de Aprofundamento
            # ============================================
            print("\n🤔 Gerando pergunta de aprofundamento...")
            followup_query = self.deep_research.generate_followup_question(
                initial_sources, 
                query
            )
            print(f"✓ Pergunta gerada: '{followup_query}'")
            
            # ============================================
            # CAMADA 2: Pesquisa de Aprofundamento
            # ============================================
            print("\n📊 CAMADA 2: Pesquisa de aprofundamento...")
            followup_sources = self.deep_research.search_web_exa(
                followup_query, 
                num_results=5
            )
            
            # Marcar fontes de follow-up
            for source in followup_sources:
                source['title'] = f"[Aprofundamento] {source['title']}"
            
            print(f"✓ Encontradas {len(followup_sources)} fontes adicionais")
            
            # ============================================
            # Combinar todas as fontes
            # ============================================
            all_sources = initial_sources + followup_sources
            print(f"\n📚 Total de fontes coletadas: {len(all_sources)}")
            
            # ============================================
            # Síntese Final
            # ============================================
            print("\n🧠 Sintetizando relatório final...")
            synthesis = self.deep_research.synthesize_results(
                all_sources,
                query,
                followup_query
            )
            
            # ============================================
            # Processar resultado
            # ============================================
            print("\n⚙️ Processando resultado...")
            result = self._parse_synthesis(synthesis, vc_list)
            
            # Adicionar metadados
            result['metadados'] = {
                'vcs_pesquisadas': vc_list,
                'total_fontes': len(all_sources),
                'query_inicial': query,
                'query_aprofundamento': followup_query,
                'camadas_pesquisa': 2,
                'fontes_iniciais': len(initial_sources),
                'fontes_aprofundamento': len(followup_sources)
            }
            
            startups_count = len(result.get('resultado', []))
            print(f"\n✅ Pesquisa concluída com sucesso! {startups_count} startups encontradas")
            
            return result
            
        except Exception as e:
            print(f"\n❌ Erro durante a pesquisa profunda: {e}")
            return self._error_result(vc_list, query, str(e))
    
    def _parse_synthesis(self, synthesis: str, vc_list: List[str]) -> Dict:
        """
        Processa a síntese e extrai o JSON estruturado
        """
        try:
            # Tentar extrair JSON diretamente
            if synthesis.strip().startswith('['):
                startups = json.loads(synthesis)
            else:
                # Tentar encontrar JSON no texto
                import re
                json_match = re.search(r'\[.*\]', synthesis, re.DOTALL)
                if json_match:
                    startups = json.loads(json_match.group())
                else:
                    # Se não conseguir extrair, retornar estrutura vazia
                    print("⚠️ Não foi possível extrair JSON da resposta")
                    startups = []
            
            # Garantir que cada startup tem todas as chaves necessárias
            required_keys = [
                'nome', 'site', 'setor', 'ano_fundacao', 
                'valor_investimento', 'rodada', 'data_investimento',
                'vc_investidor', 'descricao_breve', 'linkedin_fundador'
            ]
            
            for startup in startups:
                for key in required_keys:
                    if key not in startup:
                        startup[key] = "Não informado"
                
                # Se vc_investidor está vazio, tentar inferir das VCs pesquisadas
                if startup.get('vc_investidor') == "Não informado" and vc_list:
                    startup['vc_investidor'] = vc_list[0]  # Usar primeira VC como padrão
            
            return {
                'resultado': startups,
                'tipo': 'pesquisa_profunda',
                'sucesso': True
            }
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Erro ao processar JSON: {e}")
            return {
                'resultado': [],
                'resposta_bruta': synthesis,
                'tipo': 'pesquisa_profunda',
                'sucesso': False,
                'erro': 'Não foi possível processar o formato JSON'
            }
    
    def _empty_result(self, vc_list: List[str], query: str) -> Dict:
        """Retorna resultado vazio estruturado"""
        return {
            'resultado': [],
            'metadados': {
                'vcs_pesquisadas': vc_list,
                'total_fontes': 0,
                'query_inicial': query,
                'query_aprofundamento': '',
                'camadas_pesquisa': 0
            },
            'tipo': 'pesquisa_profunda',
            'sucesso': False,
            'mensagem': 'Nenhuma fonte encontrada'
        }
    
    def _error_result(self, vc_list: List[str], query: str, error_msg: str) -> Dict:
        """Retorna resultado de erro estruturado"""
        return {
            'resultado': [],
            'metadados': {
                'vcs_pesquisadas': vc_list,
                'query_inicial': query,
                'erro': error_msg
            },
            'tipo': 'pesquisa_profunda',
            'sucesso': False,
            'erro': error_msg
        }


# Função de conveniência para criar a task CrewAI
def create_deep_research_task(vc_list: List[str]) -> Task:
    """
    Cria uma Task CrewAI para pesquisa profunda
    
    Args:
        vc_list: Lista de VCs para pesquisar
        
    Returns:
        Task configurada para pesquisa profunda
    """
    agent = create_deep_research_crewai_agent()
    
    task = Task(
        description=f"""
        Realize uma pesquisa profunda em múltiplas camadas sobre startups investidas por: {', '.join(vc_list)}.
        
        Processo:
        1. CAMADA 1: Pesquisa inicial ampla sobre as VCs e seus investimentos
        2. ANÁLISE: Identifique áreas que precisam de mais detalhes
        3. CAMADA 2: Pesquisa focada com perguntas de aprofundamento
        4. SÍNTESE: Combine todas as informações em um relatório estruturado
        
        O resultado DEVE ser uma lista JSON com as seguintes chaves para cada startup:
        ['nome', 'site', 'setor', 'ano_fundacao', 'valor_investimento', 'rodada', 
         'data_investimento', 'vc_investidor', 'descricao_breve', 'linkedin_fundador']
        """,
        expected_output="""
        Lista JSON estruturada com informações detalhadas das startups encontradas,
        incluindo metadados sobre o processo de pesquisa em múltiplas camadas.
        """,
        agent=agent
    )
    
    return task