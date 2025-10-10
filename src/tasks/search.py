from crewai import Task
from agents.vc_research_agent import vc_research_agent

vc_research_task = Task(
    description=(
        "Pesquise e liste 10 startups que foram investidas por cada venture capital: {vc_list}. "
        "Retorne os dados em uma lista de dicionários JSON, sem CSV e sem texto extra. "
        "Cada dicionário deve conter as chaves: "
        "['nome', 'site', 'setor', 'ano_fundacao', 'valor_investimento', 'rodada', 'data_investimento', "
        "'vc_investidor', 'descricao_breve', 'linkedin_fundador']."
    ),
    expected_output="""
    Uma lista JSON de objetos no formato:
    [
      {
        "nome": "Startup 1",
        "site": "https://...",
        "setor": "Fintech",
        "ano_fundacao": "2019",
        "valor_investimento": "10M USD",
        "rodada": "Series A",
        "data_investimento": "2023-04-10",
        "vc_investidor": "Kaszek Ventures",
        "descricao_breve": "Startup de pagamentos...",
        "linkedin_fundador": "https://linkedin.com/in/fundador"
      }
    ]
    """,
    agent=vc_research_agent,
    output_file=None
)