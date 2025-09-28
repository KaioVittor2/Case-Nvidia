# arquivo: src/pipelines/pipeline_manager.py
import os
from crewai import Crew, Task, LLM  # Importe LLM do crewai

# Importe seus agentes e tarefas
from src.agents.vc_research_agent import vc_research_agent
# Se você tiver mais agentes, importe-os aqui

# 1. Crie a instância do LLM da Perplexity (método do notebook)
#    Certifique-se de que load_dotenv() já foi chamado no app.py
perplexity_llm = LLM(
    model="sonar-pro", # Você confirmou que este modelo funciona para você
    base_url="https://api.perplexity.ai/", # Manter para garantir
    api_key="" # Digite sua chave de API aqui
)

# 2. Atribua o LLM ao seu agente
vc_research_agent.llm = perplexity_llm
# Se tiver outros agentes, atribua o LLM a eles também
# ex: outro_agente.llm = perplexity_llm

# 3. Defina sua função de pipeline (o resto do código)
def pesquisar_startups_por_vcs(lista_vcs: list):
    # Crie a tarefa para o agente
    pesquisa_task = Task(
        description=f"""Pesquise e liste 10 startups que foram investidas por cada venture
        capital: {lista_vcs}. Retorne os dados em uma lista de
        dicionários JSON, sem CSV e sem texto extra. Cada dicionário deve conter
        as chaves: ['nome', 'site', 'setor', 'ano_fundacao', 'valor_investimento',
        'rodada', 'data_investimento', 'vc_investidor', 'descricao_breve',
        'linkedin_fundador'].""",
        expected_output="Uma lista de dicionários JSON com os dados das startups.",
        agent=vc_research_agent
    )

    # Monte e execute o Crew
    crew_vc = Crew(
        agents=[vc_research_agent],
        tasks=[pesquisa_task],
        verbose=True
    )

    resultado_vc = crew_vc.kickoff()
    return resultado_vc