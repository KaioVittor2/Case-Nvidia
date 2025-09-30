"""
Deep Pipeline Manager - Gerenciamento do pipeline de pesquisa profunda
Integração com o sistema existente
"""

from typing import List, Dict, Any
from crewai import Crew
from src.tasks.deep_research_task import DeepResearchTask, create_deep_research_task
from src.agents.deep_research_agent import create_deep_research_crewai_agent


def pesquisar_startups_profundo(lista_vcs: List[str]) -> Dict[str, Any]:
    """
    Executa pesquisa profunda em múltiplas camadas para encontrar startups
    
    Esta é a função principal que deve ser chamada pelo app.py
    
    Args:
        lista_vcs: Lista de nomes de VCs para pesquisar
        
    Returns:
        Dicionário com:
        - resultado: Lista de startups encontradas
        - metadados: Informações sobre a pesquisa
        - tipo: 'pesquisa_profunda'
    """
    
    print("\n" + "="*60)
    print("🚀 INICIANDO PESQUISA PROFUNDA")
    print("="*60)
    
    # Opção 1: Usar diretamente a classe DeepResearchTask (mais controle)
    deep_task = DeepResearchTask()
    resultado = deep_task.execute_deep_research(lista_vcs)
    
    # Adicionar flag para identificar o tipo de pesquisa
    resultado['tipo'] = 'pesquisa_profunda'
    
    print("\n" + "="*60)
    print("🏁 PESQUISA PROFUNDA CONCLUÍDA")
    print("="*60)
    
    return resultado


def pesquisar_startups_profundo_crew(lista_vcs: List[str]) -> Dict[str, Any]:
    """
    Versão alternativa usando Crew do CrewAI
    Útil se você quiser integrar com outros agentes
    
    Args:
        lista_vcs: Lista de nomes de VCs para pesquisar
        
    Returns:
        Dicionário com resultados estruturados
    """
    
    try:
        # Criar agente e task
        agent = create_deep_research_crewai_agent()
        task = create_deep_research_task(lista_vcs)
        
        # Criar e executar Crew
        crew = Crew(
            agents=[agent],
            tasks=[task],
            verbose=True
        )
        
        print(f"\n🚀 Executando Crew para pesquisa profunda: {', '.join(lista_vcs)}")
        resultado_crew = crew.kickoff()
        
        # Processar resultado do Crew
        if hasattr(resultado_crew, 'raw'):
            # Se tiver o formato esperado do CrewAI
            deep_task = DeepResearchTask()
            return deep_task._parse_synthesis(resultado_crew.raw, lista_vcs)
        else:
            # Retornar como está
            return {
                'resultado': resultado_crew,
                'tipo': 'pesquisa_profunda',
                'metadados': {
                    'vcs_pesquisadas': lista_vcs,
                    'metodo': 'crew'
                }
            }
            
    except Exception as e:
        print(f"❌ Erro no pipeline Crew: {e}")
        return {
            'resultado': [],
            'tipo': 'pesquisa_profunda',
            'erro': str(e),
            'sucesso': False
        }


def comparar_pesquisas(lista_vcs: List[str]) -> Dict[str, Any]:
    """
    Função de utilidade para comparar pesquisa normal vs profunda
    Útil para testes e avaliação
    
    Args:
        lista_vcs: Lista de VCs para pesquisar
        
    Returns:
        Dicionário com resultados de ambos os métodos
    """
    
    print("\n📊 COMPARAÇÃO: Pesquisa Normal vs Profunda")
    print("="*60)
    
    resultados = {
        'vcs': lista_vcs,
        'comparacao': {}
    }
    
    # Pesquisa normal (se existir no sistema)
    try:
        from src.pipelines.pipeline_manager import pesquisar_startups_por_vcs
        print("\n1️⃣ Executando pesquisa NORMAL...")
        resultado_normal = pesquisar_startups_por_vcs(lista_vcs)
        
        # Processar resultado
        if hasattr(resultado_normal, 'raw'):
            import json
            try:
                startups_normal = json.loads(resultado_normal.raw)
            except:
                startups_normal = []
        else:
            startups_normal = []
        
        resultados['comparacao']['normal'] = {
            'total_startups': len(startups_normal),
            'metodo': 'pesquisa_simples',
            'startups': startups_normal[:5]  # Primeiras 5 para comparação
        }
    except Exception as e:
        print(f"⚠️ Pesquisa normal não disponível: {e}")
        resultados['comparacao']['normal'] = {'erro': str(e)}
    
    # Pesquisa profunda
    print("\n2️⃣ Executando pesquisa PROFUNDA...")
    resultado_profundo = pesquisar_startups_profundo(lista_vcs)
    
    resultados['comparacao']['profunda'] = {
        'total_startups': len(resultado_profundo.get('resultado', [])),
        'metodo': 'pesquisa_profunda',
        'camadas': resultado_profundo.get('metadados', {}).get('camadas_pesquisa', 2),
        'fontes': resultado_profundo.get('metadados', {}).get('total_fontes', 0),
        'startups': resultado_profundo.get('resultado', [])[:5]  # Primeiras 5
    }
    
    # Análise comparativa
    print("\n📈 RESULTADO DA COMPARAÇÃO:")
    print(f"  Normal: {resultados['comparacao'].get('normal', {}).get('total_startups', 0)} startups")
    print(f"  Profunda: {resultados['comparacao']['profunda']['total_startups']} startups")
    print(f"  Fontes consultadas: {resultados['comparacao']['profunda']['fontes']}")
    
    return resultados