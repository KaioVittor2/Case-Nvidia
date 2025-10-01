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
    goal="Realizar pesquisas detalhadas e exaustivas sobre startups investidas por VCs, garantindo dados completos e precisos",
    backstory=(
        "Você é um pesquisador especializado em venture capital com acesso a ferramentas "
        "avançadas de busca e análise. Você realiza pesquisas em múltiplas camadas, "
        "primeiro coletando informações gerais, depois aprofundando em aspectos específicos, "
        "e finalmente enriquecendo dados faltantes através de buscas direcionadas. "
        "Sua missão é garantir que cada startup tenha o máximo de informações possível, "
        "incluindo valores de investimento, datas precisas, URLs reais e perfis de fundadores."
    ),
    llm=cerebras_llm,
    verbose=True,
    allow_delegation=False
) if DEPENDENCIES_AVAILABLE else None


def search_web_exa(query, num_results=10):
    """
    Busca na web usando a API da Exa
    """
    if not DEPENDENCIES_AVAILABLE or not exa_client:
        raise RuntimeError("Exa API not available. Install exa-py.")
    
    try:
        print(f"🔍 Buscando Exa: '{query}' (num_results={num_results})")
        
        result = exa_client.search_and_contents(
            query,
            type="neural",  # MUDOU: de "auto" para "neural"
            num_results=num_results,
            text={
                "max_characters": 2000,
                "include_html_tags": False  # NOVO
            },
            use_autoprompt=True  # NOVO: melhora queries automáticas
        )
        
        sources = []
        for r in result.results:
            if r.text:
                sources.append({
                    "title": r.title or "Untitled",
                    "content": r.text,
                    "url": getattr(r, 'url', ''),
                    "score": getattr(r, 'score', 0)
                })
        
        print(f"✓ Exa retornou {len(sources)} fontes")
        
        if not sources:
            print(f"⚠️ AVISO: Nenhuma fonte com conteúdo para query: {query}")
        
        sources.sort(key=lambda x: x.get('score', 0), reverse=True)
        return sources
        
    except Exception as e:
        print(f"❌ ERRO na busca Exa: {str(e)}")
        print(f"   Query: {query}")
        import traceback
        traceback.print_exc()
        return []


def analyze_with_cerebras(prompt, max_tokens=1000, temperature=0.1):
    """
    Analisa texto usando a API da Cerebras
    
    VERSÃO REFINADA: Temperatura mais baixa para respostas mais precisas
    
    Args:
        prompt (str): Prompt para análise
        max_tokens (int): Número máximo de tokens na resposta (aumentado de 600)
        temperature (float): Temperatura para geração (reduzida de 0.2 para 0.1)
    
    Returns:
        str: Resposta da IA
    """
    if not DEPENDENCIES_AVAILABLE or not cerebras_client:
        raise RuntimeError("Cerebras API not available. Install cerebras-cloud-sdk.")
    
    try:
        chat_completion = cerebras_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise data extraction specialist. "
                        "Always provide accurate, structured data in the exact format requested. "
                        "Never add explanations or markdown formatting unless explicitly asked."
                    )
                },
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


def buscar_informacao_especifica(startup_nome, campo_faltante, vc_name):
    """
    NOVA FUNÇÃO: Busca informação específica para um campo faltante
    
    Args:
        startup_nome (str): Nome da startup
        campo_faltante (str): Campo que precisa ser preenchido
        vc_name (str): Nome do VC investidor
    
    Returns:
        str: Valor encontrado ou None
    """
    if not DEPENDENCIES_AVAILABLE or not exa_client:
        return None
    
    # Mapear campos para queries específicas
    query_templates = {
        'valor_investimento': f'"{startup_nome}" {vc_name} funding amount raised million',
        'data_investimento': f'"{startup_nome}" {vc_name} investment date announced',
        'rodada': f'"{startup_nome}" {vc_name} series round seed',
        'linkedin_fundador': f'"{startup_nome}" founder CEO LinkedIn',
        'site': f'"{startup_nome}" official website',
        'ano_fundacao': f'"{startup_nome}" founded year established'
    }
    
    query = query_templates.get(campo_faltante, f'"{startup_nome}" {vc_name} {campo_faltante}')
    
    try:
        # Busca muito específica
        sources = search_web_exa(query, num_results=3)
        
        if not sources:
            return None
        
        # Usar IA para extrair informação específica
        context = f"Startup: {startup_nome}\nBuscando: {campo_faltante}\n\nFontes:\n\n"
        for source in sources[:2]:
            context += f"{source['title']}\n{source['content'][:1000]}\n\n"
        
        extraction_prompt = f"""{context}

Extract ONLY the {campo_faltante} for {startup_nome}.

Return ONLY the value, nothing else. If not found, return "Not found".

Value:"""
        
        resultado = analyze_with_cerebras(extraction_prompt, max_tokens=100, temperature=0.0)
        
        if resultado and "not found" not in resultado.lower():
            return resultado.strip()
        
        return None
        
    except Exception as e:
        print(f"Erro ao buscar {campo_faltante}: {str(e)}")
        return None


def verificar_completude_dados(startups):
    """
    NOVA FUNÇÃO: Verifica completude dos dados das startups
    
    Args:
        startups (list): Lista de startups
    
    Returns:
        dict: Estatísticas de completude
    """
    if not startups:
        return {"total": 0, "completas": 0, "percentual": 0}
    
    campos_importantes = [
        'nome', 'site', 'setor', 'ano_fundacao', 'valor_investimento',
        'rodada', 'data_investimento', 'vc_investidor', 'descricao_breve',
        'linkedin_fundador'
    ]
    
    completas = 0
    total_campos = len(campos_importantes)
    
    for startup in startups:
        campos_preenchidos = sum(
            1 for campo in campos_importantes
            if startup.get(campo) and startup.get(campo) not in ["Não informado", "—", ""]
        )
        
        # Considerar completa se tiver pelo menos 7 dos 10 campos
        if campos_preenchidos >= 7:
            completas += 1
    
    return {
        "total": len(startups),
        "completas": completas,
        "percentual": round((completas / len(startups)) * 100, 1) if startups else 0,
        "media_campos_preenchidos": round(
            sum(
                sum(
                    1 for campo in campos_importantes
                    if s.get(campo) and s.get(campo) not in ["Não informado", "—", ""]
                )
                for s in startups
            ) / len(startups),
            1
        ) if startups else 0
    }


def gerar_relatorio_qualidade(startups):
    """
    NOVA FUNÇÃO: Gera relatório de qualidade dos dados
    
    Args:
        startups (list): Lista de startups
    
    Returns:
        str: Relatório formatado
    """
    if not startups:
        return "Nenhuma startup para análise"
    
    stats = verificar_completude_dados(startups)
    
    # Análise por campo
    campos_importantes = [
        'nome', 'site', 'setor', 'ano_fundacao', 'valor_investimento',
        'rodada', 'data_investimento', 'vc_investidor', 'descricao_breve',
        'linkedin_fundador'
    ]
    
    campo_stats = {}
    for campo in campos_importantes:
        preenchidos = sum(
            1 for s in startups
            if s.get(campo) and s.get(campo) not in ["Não informado", "—", ""]
        )
        campo_stats[campo] = {
            "preenchidos": preenchidos,
            "percentual": round((preenchidos / len(startups)) * 100, 1)
        }
    
    relatorio = f"""
╔══════════════════════════════════════════════════════════╗
║           RELATÓRIO DE QUALIDADE DOS DADOS               ║
╚══════════════════════════════════════════════════════════╝

📊 ESTATÍSTICAS GERAIS:
   • Total de startups: {stats['total']}
   • Startups completas (≥7 campos): {stats['completas']} ({stats['percentual']}%)
   • Média de campos preenchidos: {stats['media_campos_preenchidos']}/10

📋 COMPLETUDE POR CAMPO:
"""
    
    for campo, stat in sorted(campo_stats.items(), key=lambda x: x[1]['percentual'], reverse=True):
        barra = "█" * int(stat['percentual'] / 5)
        relatorio += f"   {campo:20s}: {barra:20s} {stat['percentual']}% ({stat['preenchidos']}/{len(startups)})\n"
    
    # Identificar campos mais problemáticos
    campos_problematicos = [
        campo for campo, stat in campo_stats.items()
        if stat['percentual'] < 50
    ]
    
    if campos_problematicos:
        relatorio += f"\n⚠️  CAMPOS COM BAIXA COMPLETUDE:\n"
        for campo in campos_problematicos:
            relatorio += f"   • {campo}: {campo_stats[campo]['percentual']}%\n"
    
    return relatorio


def extrair_urls_validas(text):
    """
    NOVA FUNÇÃO: Extrai URLs válidas de texto
    
    Args:
        text (str): Texto contendo possíveis URLs
    
    Returns:
        list: Lista de URLs encontradas
    """
    import re
    
    # Padrão para URLs
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    
    urls = re.findall(url_pattern, text)
    
    # Filtrar URLs válidas
    valid_urls = []
    for url in urls:
        # Remover pontuação final
        url = url.rstrip('.,;:!?)')
        
        # Verificar se é um domínio válido
        if '.' in url and len(url) > 10:
            valid_urls.append(url)
    
    return valid_urls


def normalizar_valor_investimento(valor_str):
    """
    NOVA FUNÇÃO: Normaliza valores de investimento para formato padrão
    
    Args:
        valor_str (str): String com valor de investimento
    
    Returns:
        str: Valor normalizado
    """
    if not valor_str or valor_str in ["Não informado", "—", ""]:
        return "Não informado"
    
    import re
    
    # Padrões comuns
    valor_str = str(valor_str).strip()
    
    # Extrair número e unidade
    patterns = [
        r'([\d,.]+)\s*(million|M|milhões?)',
        r'([\d,.]+)\s*(billion|B|bilhões?)',
        r'([\d,.]+)\s*(thousand|K|mil)',
        r'\$\s*([\d,.]+)M',
        r'R\$\s*([\d,.]+)\s*milhões?',
        r'US\$\s*([\d,.]+)M'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, valor_str, re.IGNORECASE)
        if match:
            numero = match.group(1).replace(',', '.')
            
            try:
                valor = float(numero)
                
                # Determinar unidade
                if 'billion' in valor_str.lower() or 'bilh' in valor_str.lower() or 'B' in valor_str:
                    return f"US$ {valor:.1f} bilhões"
                elif 'thousand' in valor_str.lower() or 'K' in valor_str or 'mil' in valor_str.lower():
                    return f"US$ {valor:.0f} mil"
                else:
                    # Milhões é o padrão
                    if 'R$' in valor_str or 'R\\' in valor_str:
                        return f"R$ {valor:.1f} milhões"
                    else:
                        return f"US$ {valor:.1f} milhões"
            except:
                pass
    
    # Se não conseguiu normalizar, retornar valor original
    return valor_str


def validar_url(url):
    """
    NOVA FUNÇÃO: Valida se uma URL é válida e acessível
    
    Args:
        url (str): URL para validar
    
    Returns:
        bool: True se válida, False caso contrário
    """
    if not url or url in ["Não informado", "—", ""]:
        return False
    
    import re
    
    # Padrão básico de URL
    url_pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
    
    return bool(re.match(url_pattern, url))


def enriquecer_startup_individual(startup, search_func, analyze_func):
    """
    NOVA FUNÇÃO: Enriquece uma startup individual com buscas específicas
    
    Args:
        startup (dict): Dados da startup
        search_func: Função de busca
        analyze_func: Função de análise
    
    Returns:
        dict: Startup enriquecida
    """
    campos_para_enriquecer = []
    
    # Identificar campos vazios ou genéricos
    for campo in ['valor_investimento', 'data_investimento', 'rodada', 'linkedin_fundador', 'site']:
        valor = startup.get(campo, "")
        if not valor or valor in ["Não informado", "—", ""]:
            campos_para_enriquecer.append(campo)
    
    if not campos_para_enriquecer:
        return startup
    
    print(f"    🔍 Enriquecendo {startup['nome']}: {len(campos_para_enriquecer)} campos vazios")
    
    # Buscar cada campo individualmente
    for campo in campos_para_enriquecer[:3]:  # Limitar a 3 campos para não sobrecarregar
        valor_encontrado = buscar_informacao_especifica(
            startup['nome'],
            campo,
            startup.get('vc_investidor', '')
        )
        
        if valor_encontrado:
            # Normalizar valor se for investimento
            if campo == 'valor_investimento':
                valor_encontrado = normalizar_valor_investimento(valor_encontrado)
            
            # Validar URL se for site ou LinkedIn
            if campo in ['site', 'linkedin_fundador']:
                if not validar_url(valor_encontrado):
                    continue
            
            startup[campo] = valor_encontrado
            print(f"      ✓ {campo}: {valor_encontrado[:50]}...")
    
    return startup