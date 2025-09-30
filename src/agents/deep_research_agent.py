"""
Deep Research Agent - Pesquisa em múltiplas camadas usando Exa e Cerebras
Baseado no notebook Deep_Research_agents_Nvidia.ipynb
"""

import os
from typing import List, Dict, Optional
from crewai import Agent, LLM

# Importar as bibliotecas necessárias
try:
    from exa_py import Exa
    from cerebras.cloud.sdk import Cerebras
except ImportError as e:
    print(f"⚠️ Erro ao importar bibliotecas: {e}")
    print("Certifique-se de ter instalado: pip install exa-py cerebras-cloud-sdk")
    raise

class DeepResearchAgent:
    """Agente especializado em pesquisa profunda usando Exa e Cerebras"""
    
    def __init__(self):
        """Inicializa o agente com as APIs necessárias"""
        # Carregar chaves de API
        self.exa_api_key = os.environ.get("EXA_API_KEY")
        self.cerebras_api_key = os.environ.get("CEREBRAS_API_KEY")
        
        if not self.exa_api_key:
            raise ValueError("EXA_API_KEY não encontrada. Configure no arquivo keys.env")
        if not self.cerebras_api_key:
            raise ValueError("CEREBRAS_API_KEY não encontrada. Configure no arquivo keys.env")
        
        # Inicializar clientes das APIs
        try:
            self.exa_client = Exa(api_key=self.exa_api_key)
            self.cerebras_client = Cerebras(api_key=self.cerebras_api_key)
            print("✅ APIs Exa e Cerebras inicializadas com sucesso")
        except Exception as e:
            print(f"❌ Erro ao inicializar APIs: {e}")
            raise
    
    def search_web_exa(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        Realiza busca na web usando Exa API
        Baseado na função search_web do notebook
        """
        try:
            print(f"🔍 Buscando: '{query}' (até {num_results} resultados)")
            
            result = self.exa_client.search_and_contents(
                query,
                type="auto",
                num_results=num_results,
                text={"max_characters": 1000}
            )
            
            # Processar resultados
            sources = []
            for res in result.results:
                if hasattr(res, 'text') and res.text:
                    sources.append({
                        "title": getattr(res, 'title', 'Sem título'),
                        "content": res.text,
                        "url": getattr(res, 'url', ''),
                        "published_date": getattr(res, 'published_date', '')
                    })
            
            print(f"✓ Encontrados {len(sources)} resultados relevantes")
            return sources
            
        except Exception as e:
            print(f"❌ Erro na busca Exa: {e}")
            return []
    
    def analyze_with_cerebras(self, prompt: str, max_tokens: int = 600, temperature: float = 0.2) -> str:
        """
        Analisa conteúdo usando Cerebras AI
        Baseado na função ask_ai do notebook
        """
        try:
            print(f"🧠 Analisando com Cerebras (max_tokens={max_tokens})")
            
            chat_completion = self.cerebras_client.chat.completions.create(
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
            
            response = chat_completion.choices[0].message.content
            print("✓ Análise concluída")
            return response
            
        except Exception as e:
            print(f"❌ Erro na análise Cerebras: {e}")
            return ""
    
    def generate_followup_question(self, initial_sources: List[Dict], original_query: str) -> str:
        """
        Gera uma pergunta de aprofundamento baseada nas fontes iniciais
        """
        # Criar contexto das fontes iniciais
        context = f"Pesquisa original: {original_query}\n\nFontes encontradas:\n"
        for i, source in enumerate(initial_sources[:4], 1):
            context += f"{i}. {source['title']}: {source['content'][:300]}...\n\n"
        
        # Prompt para gerar pergunta de follow-up
        prompt = f"""{context}

Com base nestas fontes sobre "{original_query}", qual é a pergunta de acompanhamento mais importante 
que aprofundaria nosso entendimento sobre as startups investidas e seus detalhes específicos?

Responda apenas com uma consulta de pesquisa específica e focada (sem explicação):"""
        
        followup = self.analyze_with_cerebras(prompt, max_tokens=100, temperature=0.3)
        return followup.strip().strip('"')
    
    def synthesize_results(self, all_sources: List[Dict], original_query: str, followup_query: str) -> str:
        """
        Sintetiza todos os resultados em um formato estruturado JSON
        """
        # Criar contexto completo
        context = f"Pesquisa original: {original_query}\n"
        context += f"Pesquisa de aprofundamento: {followup_query}\n\n"
        context += "Todas as fontes coletadas:\n"
        
        for i, source in enumerate(all_sources[:8], 1):
            prefix = "[Aprofundamento] " if i > 4 else ""
            context += f"{i}. {prefix}{source['title']}: {source['content'][:400]}...\n\n"
        
        # Prompt final para gerar lista estruturada
        prompt = f"""{context}

Com base em TODAS as fontes acima, liste as startups que foram investidas pelas VCs mencionadas.

IMPORTANTE: Sua resposta deve ser APENAS uma lista JSON válida, sem nenhum texto adicional antes ou depois.
Cada startup deve ser um objeto com TODAS as seguintes chaves (use "Não informado" se não encontrar a informação):

[
  {{
    "nome": "Nome da Startup",
    "site": "https://...",
    "setor": "Categoria/Indústria",
    "ano_fundacao": "Ano",
    "valor_investimento": "Valor em USD",
    "rodada": "Série/Rodada",
    "data_investimento": "Data",
    "vc_investidor": "Nome da VC",
    "descricao_breve": "Breve descrição do que a empresa faz",
    "linkedin_fundador": "Link do LinkedIn ou 'Não informado'"
  }}
]

Retorne APENAS o JSON, sem explicações ou texto adicional:"""
        
        response = self.analyze_with_cerebras(prompt, max_tokens=800, temperature=0.1)
        return response


# Criar instância do agente CrewAI
def create_deep_research_crewai_agent():
    """Cria um agente CrewAI que usa o DeepResearchAgent internamente"""
    
    # Usar o LLM padrão do CrewAI para o agente (pode ser OpenAI ou Perplexity)
    agent = Agent(
        role="Especialista em Pesquisa Profunda de VCs",
        goal="Realizar pesquisa em múltiplas camadas para encontrar informações detalhadas sobre startups investidas",
        backstory=(
            "Você é um especialista em pesquisa profunda que utiliza técnicas avançadas de busca em múltiplas "
            "camadas. Primeiro realiza uma pesquisa ampla, depois gera perguntas de aprofundamento inteligentes "
            "e finalmente sintetiza todas as informações em relatórios estruturados e completos."
        ),
        verbose=True,
        allow_delegation=False
    )
    
    # Anexar o DeepResearchAgent como ferramenta customizada
    agent._deep_research = DeepResearchAgent()
    
    return agent