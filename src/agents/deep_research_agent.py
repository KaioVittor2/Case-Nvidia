# arquivo: src/agents/deep_research_agent.py
from crewai import Agent, LLM
import os

try:
    from exa_py import Exa
    from cerebras.cloud.sdk import Cerebras
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False
    print("⚠️ Deep Research dependencies not available. Install: pip install exa-py cerebras-cloud-sdk")

# Inicializar clientes apenas se dependências disponíveis
if DEPENDENCIES_AVAILABLE:
    exa_client = Exa(api_key=os.environ.get("EXA_API_KEY", ""))
    cerebras_client = Cerebras(api_key=os.environ.get("CEREBRAS_API_KEY", ""))
    
    # Configurar LLM da Cerebras para o agente
    cerebras_llm = LLM(
        model="llama-4-scout-17b-16e-instruct",
        api_key=os.environ.get("CEREBRAS_API_KEY", ""),
        base_url="https://api.cerebras.ai/v1"
    )
else:
    exa_client = None
    cerebras_client = None
    cerebras_llm = None

# Criar agente
deep_research_agent = Agent(
    role="Especialista em Pesquisa Profunda de Venture Capital",
    goal="Realizar pesquisas detalhadas em múltiplas camadas sobre startups investidas por VCs",
    backstory=(
        "Você é um pesquisador especializado em venture capital com acesso a ferramentas "
        "avançadas de busca e análise. Você realiza pesquisas em camadas, primeiro coletando "
        "informações gerais e depois aprofundando em aspectos específicos para obter dados "
        "completos e precisos sobre investimentos de VCs em startups."
    ),
    llm=cerebras_llm,
    verbose=True,
    allow_delegation=False
) if DEPENDENCIES_AVAILABLE else None

def search_web_exa(query, num_results=5):
    """
    Busca na web usando a API da Exa
    
    Args:
        query (str): Consulta de pesquisa
        num_results (int): Número de resultados desejados
    
    Returns:
        list: Lista de resultados com título e conteúdo
    """
    if not DEPENDENCIES_AVAILABLE or not exa_client:
        raise RuntimeError("Exa API not available. Install exa-py.")
    
    try:
        result = exa_client.search_and_contents(
            query,
            type="auto",
            num_results=num_results,
            text={"max_characters": 1000}
        )
        
        sources = []
        for r in result.results:
            if r.text and len(r.text) > 200:
                sources.append({
                    "title": r.title or "Untitled",
                    "content": r.text,
                    "url": getattr(r, 'url', '')
                })
        
        return sources
    except Exception as e:
        print(f"Erro na busca Exa: {str(e)}")
        return []

def analyze_with_cerebras(prompt, max_tokens=600, temperature=0.2):
    """
    Analisa texto usando a API da Cerebras
    
    Args:
        prompt (str): Prompt para análise
        max_tokens (int): Número máximo de tokens na resposta
        temperature (float): Temperatura para geração
    
    Returns:
        str: Resposta da IA
    """
    if not DEPENDENCIES_AVAILABLE or not cerebras_client:
        raise RuntimeError("Cerebras API not available. Install cerebras-cloud-sdk.")
    
    try:
        chat_completion = cerebras_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-4-scout-17b-16e-instruct",
            max_tokens=max_tokens,
            temperature=temperature
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Erro na análise Cerebras: {str(e)}")
        return ""

def generate_follow_up_query(initial_sources, original_query):
    """
    Gera uma pergunta de aprofundamento baseada nas fontes iniciais
    
    Args:
        initial_sources (list): Fontes coletadas na primeira camada
        original_query (str): Consulta original
    
    Returns:
        str: Pergunta de aprofundamento
    """
    if not initial_sources:
        return original_query + " detailed information"
    
    context = f"Consulta original: {original_query}\n\nFontes encontradas:\n"
    for i, source in enumerate(initial_sources[:4], 1):
        context += f"{i}. {source['title']}: {source['content'][:300]}...\n\n"
    
    prompt = f"""{context}

Com base nessas fontes sobre startups investidas por VCs, qual é a pergunta de aprofundamento 
mais importante que nos ajudaria a obter informações mais detalhadas e específicas?

Foque em:
- Valores de investimento específicos
- Datas e rodadas de investimento
- Informações sobre fundadores
- Setores e mercados

Responda apenas com a pergunta de busca em inglês, sem explicações adicionais."""
    
    follow_up = analyze_with_cerebras(prompt, max_tokens=100, temperature=0.3)
    return follow_up.strip().strip('"').strip("'")

def synthesize_final_report(all_sources, vc_list, original_query, follow_up_query):
    """
    Sintetiza relatório final com todas as fontes coletadas
    
    Args:
        all_sources (list): Todas as fontes coletadas
        vc_list (list): Lista de VCs pesquisadas
        original_query (str): Consulta original
        follow_up_query (str): Consulta de aprofundamento
    
    Returns:
        str: Relatório JSON estruturado
    """
    if not all_sources:
        return '[]'
    
    context = f"""Consulta original: {original_query}
Consulta de aprofundamento: {follow_up_query}
VCs pesquisadas: {', '.join(vc_list)}

Todas as fontes coletadas:
"""
    
    for i, source in enumerate(all_sources[:10], 1):
        context += f"{i}. {source['title']}: {source['content'][:500]}...\n\n"
    
    prompt = f"""{context}

Com base em todas as fontes coletadas acima, crie uma lista JSON de startups investidas pelas VCs: {', '.join(vc_list)}.

REGRAS CRÍTICAS:
1. Retorne APENAS um array JSON válido, começando com [ e terminando com ]
2. NÃO adicione texto antes ou depois do JSON
3. NÃO use markdown, NÃO use ```json
4. Busque pelo menos 10 startups para CADA VC mencionada
5. Cada objeto deve ter EXATAMENTE estas chaves:
   - nome (string)
   - site (string, URL completa ou "Não informado")
   - setor (string, ex: "Fintech", "SaaS", "E-commerce")
   - ano_fundacao (string, ex: "2020" ou "Não informado")
   - valor_investimento (string, ex: "US$ 10 milhões" ou "R$ 5 milhões")
   - rodada (string, ex: "Série A", "Seed", "Série B")
   - data_investimento (string, formato YYYY-MM-DD ou "Não informado")
   - vc_investidor (string, nome da VC que investiu)
   - descricao_breve (string, 1-2 frases sobre a startup)
   - linkedin_fundador (string, URL do LinkedIn ou "Não informado")

FORMATO ESPERADO:
[
  {{
    "nome": "Airbnb",
    "site": "https://www.airbnb.com",
    "setor": "Marketplace",
    "ano_fundacao": "2008",
    "valor_investimento": "US$ 20 milhões",
    "rodada": "Série A",
    "data_investimento": "2010-11-16",
    "vc_investidor": "Sequoia Capital",
    "descricao_breve": "Plataforma de hospedagem e experiências de viagem.",
    "linkedin_fundador": "https://www.linkedin.com/in/brianchesky"
  }}
]

Agora retorne o JSON das startups encontradas:"""
    
    response = analyze_with_cerebras(prompt, max_tokens=4000, temperature=0.2)
    return response