# arquivo: src/tasks/deep_research_task.py
from crewai import Task

def create_deep_research_task(vc_list, agent):
    """
    Cria uma task de pesquisa profunda em múltiplas camadas
    
    Args:
        vc_list (list): Lista de nomes de VCs para pesquisar
        agent: Agente que executará a task
    
    Returns:
        Task: Task configurada para pesquisa profunda
    """
    
    vcs_string = ", ".join(vc_list)
    
    task_description = f"""Realize uma pesquisa profunda em múltiplas camadas sobre startups investidas pelas seguintes Venture Capitals: {vcs_string}.

PROCESSO DETALHADO:

1. CAMADA 1 - PESQUISA INICIAL:
   - Busque informações gerais sobre startups investidas por cada uma dessas VCs
   - Foque em investimentos recentes (últimos 5 anos)
   - Colete pelo menos 6 fontes confiáveis e relevantes
   - Identifique padrões e áreas que necessitam aprofundamento

2. ANÁLISE INTERMEDIÁRIA:
   - Analise as fontes iniciais coletadas
   - Identifique gaps de informação (valores não especificados, datas faltando, etc.)
   - Gere uma pergunta de aprofundamento específica para buscar informações detalhadas

3. CAMADA 2 - PESQUISA DE APROFUNDAMENTO:
   - Use a pergunta gerada para realizar uma segunda rodada de buscas
   - Foque em fontes que contenham informações específicas sobre:
     * Valores exatos de investimento
     * Datas de rodadas de investimento
     * Informações sobre fundadores
     * URLs dos sites das startups
   - Colete pelo menos 5 fontes adicionais

4. SÍNTESE FINAL:
   - Combine todas as informações coletadas nas duas camadas
   - Liste pelo menos 10 startups para CADA VC mencionada
   - Organize os dados em formato JSON estruturado

REQUISITOS CRÍTICOS DE SAÍDA:

A resposta DEVE ser um JSON array válido com esta estrutura EXATA:

[
  {{
    "nome": "Nome da Startup",
    "site": "https://website.com",
    "setor": "Fintech",
    "ano_fundacao": "2020",
    "valor_investimento": "US$ 15 milhões",
    "rodada": "Série A",
    "data_investimento": "2023-06-15",
    "vc_investidor": "Sequoia Capital",
    "descricao_breve": "Breve descrição da startup e seu produto/serviço.",
    "linkedin_fundador": "https://linkedin.com/in/fundador"
  }}
]

REGRAS OBRIGATÓRIAS:
- Retorne APENAS o JSON array, sem texto antes ou depois
- NÃO use markdown (```json)
- NÃO adicione explicações
- Use "Não informado" para dados não encontrados
- Formate valores monetários como "US$ X milhões" ou "R$ X milhões"
- Use datas no formato YYYY-MM-DD quando disponível
- Cada startup deve ter TODAS as 10 chaves listadas acima

VCs alvo: {vcs_string}
Meta: {len(vc_list) * 10} startups no total (10 por VC)"""

    expected_output = f"""Um array JSON válido contendo informações detalhadas de startups investidas por {vcs_string}.

O JSON deve começar com [ e terminar com ].

Cada objeto no array deve ter estas 10 chaves obrigatórias:
- nome
- site
- setor
- ano_fundacao
- valor_investimento
- rodada
- data_investimento
- vc_investidor
- descricao_breve
- linkedin_fundador

Total esperado: pelo menos {len(vc_list) * 10} startups (10 para cada VC)."""

    return Task(
        description=task_description,
        expected_output=expected_output,
        agent=agent,
        output_file=None
    )