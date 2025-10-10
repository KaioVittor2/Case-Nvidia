# arquivo: src/pipelines/deep_pipeline_manager.py
import os
import json
import re

def pesquisar_startups_profundo(lista_vcs: list):
    """
    Realiza pesquisa profunda em múltiplas camadas sobre startups investidas por VCs
    
    VERSÃO REFINADA: Implementa busca iterativa por VC individual com enriquecimento
    de dados faltantes através de queries específicas.
    
    Args:
        lista_vcs (list): Lista de nomes de Venture Capitals para pesquisar
    
    Returns:
        dict: Resultado da pesquisa com dados estruturados em JSON
    """
    print(f"🔍 Iniciando pesquisa profunda REFINADA para VCs: {', '.join(lista_vcs)}")
    
    # Importar funções necessárias
    try:
        # Importação relativa ao diretório src
        import os
        import sys
        
        # Adicionar diretório src ao path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.dirname(current_dir)
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)
        
        from agents.deep_research_agent import (
            search_web_exa,
            analyze_with_cerebras,
            DEPENDENCIES_AVAILABLE
        )
    except ImportError as e:
        print(f"ERRO DE IMPORTAÇÃO: {e}")
        print(f"Tentando importação alternativa...")
        try:
            from src.agents.deep_research_agent import (
                search_web_exa,
                analyze_with_cerebras,
                DEPENDENCIES_AVAILABLE
            )
        except ImportError as e2:
            print(f"ERRO NA IMPORTAÇÃO ALTERNATIVA: {e2}")

    except ImportError as e:
        return {
            "erro": f"Erro ao importar módulos de Deep Research: {str(e)}",
            "resultado": []
        }
    
    if not DEPENDENCIES_AVAILABLE:
        return {
            "erro": "Deep Research dependencies não instaladas. Execute: pip install exa-py cerebras-cloud-sdk",
            "resultado": []
        }
    
    # Verificar API keys
    if not os.environ.get("EXA_API_KEY"):
        return {
            "erro": "EXA_API_KEY não configurada no arquivo keys.env",
            "resultado": []
        }
    
    if not os.environ.get("CEREBRAS_API_KEY"):
        return {
            "erro": "CEREBRAS_API_KEY não configurada no arquivo keys.env",
            "resultado": []
        }
    
    # ESTRUTURA PRINCIPAL: Iterar por cada VC individualmente
    todas_startups = []
    todas_fontes = []
    metadados_completos = {
        "vcs_pesquisadas": lista_vcs,
        "total_fontes": 0,
        "detalhes_por_vc": {}
    }
    
    for vc_name in lista_vcs:
        print(f"\n{'='*60}")
        print(f"🎯 PESQUISANDO: {vc_name}")
        print(f"{'='*60}")
        
        startups_vc = processar_vc_individual(
            vc_name,
            search_web_exa,
            analyze_with_cerebras
        )
        
        if startups_vc["sucesso"]:
            todas_startups.extend(startups_vc["startups"])
            todas_fontes.extend(startups_vc["fontes"])
            metadados_completos["detalhes_por_vc"][vc_name] = {
                "startups_encontradas": len(startups_vc["startups"]),
                "fontes_utilizadas": len(startups_vc["fontes"]),
                "queries_executadas": startups_vc["queries_executadas"]
            }
            print(f"✅ {vc_name}: {len(startups_vc['startups'])} startups encontradas")
        else:
            print(f"⚠️ {vc_name}: Erro na pesquisa - {startups_vc.get('erro', 'Desconhecido')}")
            metadados_completos["detalhes_por_vc"][vc_name] = {
                "erro": startups_vc.get("erro", "Erro desconhecido")
            }
    
    metadados_completos["total_fontes"] = len(todas_fontes)
    metadados_completos["total_startups"] = len(todas_startups)
    
    if not todas_startups:
        return {
            "erro": "Nenhuma startup encontrada após pesquisa completa",
            "resultado": [],
            "metadados": metadados_completos
        }
    
    print(f"\n{'='*60}")
    print(f"✨ PESQUISA COMPLETA")
    print(f"Total de startups: {len(todas_startups)}")
    print(f"Total de fontes: {len(todas_fontes)}")
    print(f"{'='*60}\n")
    
    return {
        "resultado": todas_startups,
        "metadados": metadados_completos
    }


def processar_vc_individual(vc_name, search_func, analyze_func):
    """
    Processa um VC individual com pesquisa em camadas e enriquecimento
    
    Args:
        vc_name (str): Nome do VC
        search_func: Função de busca web
        analyze_func: Função de análise com IA
    
    Returns:
        dict: Resultado com startups e metadados
    """
    try:
        # ===== CAMADA 1: PESQUISA INICIAL AMPLIADA =====
        print(f"\n📊 CAMADA 1: Pesquisa inicial ampliada para {vc_name}...")
        
        initial_query = f"{vc_name} portfolio investments startups"
        
        # AUMENTADO: de 6 para 12 resultados
        initial_sources = search_func(initial_query, num_results=12)
        print(f"✓ Encontradas {len(initial_sources)} fontes na pesquisa inicial")
        
        if not initial_sources:
            return {
                "sucesso": False,
                "erro": f"Nenhuma fonte encontrada para {vc_name}",
                "startups": [],
                "fontes": [],
                "queries_executadas": [initial_query]
            }
        
        # ===== EXTRAÇÃO INICIAL (com contexto completo) =====
        print(f"\n🧠 Extraindo dados iniciais...")
        startups_iniciais = extrair_startups_de_fontes(
            initial_sources,
            vc_name,
            analyze_func,
            contexto_maximo=True  # SEM truncamento
        )
        
        print(f"✓ Extração inicial: {len(startups_iniciais)} startups")
        
        # ===== CAMADA 2: ANÁLISE DE LACUNAS E ENRIQUECIMENTO =====
        print(f"\n🔍 CAMADA 2: Análise de lacunas e enriquecimento...")
        
        startups_enriquecidas, queries_enriquecimento = enriquecer_dados_faltantes(
            startups_iniciais,
            vc_name,
            search_func,
            analyze_func,
            max_iteracoes=3
        )
        
        # ===== CAMADA 3: BUSCA COMPLEMENTAR SE NECESSÁRIO =====
        queries_executadas = [initial_query] + queries_enriquecimento
        
        if len(startups_enriquecidas) < 10:
            print(f"\n📈 CAMADA 3: Busca complementar (meta: 10 startups)...")
            
            # Busca adicional com query alternativa
            complementary_query = (
                f"{vc_name} recent investments 2020-2024 "
                f"startup funding details portfolio"
            )
            
            complementary_sources = search_func(complementary_query, num_results=8)
            queries_executadas.append(complementary_query)
            
            if complementary_sources:
                startups_complementares = extrair_startups_de_fontes(
                    complementary_sources,
                    vc_name,
                    analyze_func,
                    contexto_maximo=True
                )
                
                # Adicionar startups que ainda não existem
                nomes_existentes = {s['nome'].lower() for s in startups_enriquecidas}
                for startup in startups_complementares:
                    if startup['nome'].lower() not in nomes_existentes:
                        startups_enriquecidas.append(startup)
                        nomes_existentes.add(startup['nome'].lower())
                
                print(f"✓ Busca complementar: +{len(startups_complementares)} startups")
        
        # Limitar a 10 startups mais completas
        startups_finais = selecionar_melhores_startups(startups_enriquecidas, limite=10)
        
        return {
            "sucesso": True,
            "startups": startups_finais,
            "fontes": initial_sources,
            "queries_executadas": queries_executadas
        }
        
    except Exception as e:
        print(f"❌ Erro ao processar {vc_name}: {str(e)}")
        return {
            "sucesso": False,
            "erro": str(e),
            "startups": [],
            "fontes": [],
            "queries_executadas": []
        }


def extrair_startups_de_fontes(sources, vc_name, analyze_func, contexto_maximo=False):
    """
    Extrai informações de startups das fontes coletadas
    
    Args:
        sources (list): Lista de fontes
        vc_name (str): Nome do VC
        analyze_func: Função de análise
        contexto_maximo (bool): Se True, não trunca o contexto
    
    Returns:
        list: Lista de startups extraídas
    """
    if not sources:
        return []
    
    # Preparar contexto das fontes (SEM TRUNCAMENTO se contexto_maximo=True)
    context = f"VC Investidor: {vc_name}\n\nFontes coletadas:\n\n"
    
    for i, source in enumerate(sources[:10], 1):
        content = source['content']
        
        # REMOVIDO: truncamento para 300 caracteres
        # NOVO: usar até 4000 caracteres ou conteúdo completo
        if contexto_maximo:
            content_limit = content[:4000] if len(content) > 4000 else content
        else:
            content_limit = content[:1000]
        
        context += f"=== FONTE {i}: {source['title']} ===\n{content_limit}\n\n"
    
    # Prompt RIGOROSO para extração
    prompt = f"""{context}

TAREFA CRÍTICA: Extraia informações DETALHADAS sobre startups investidas por {vc_name}.

INSTRUÇÕES OBRIGATÓRIAS:
1. Retorne APENAS um array JSON válido começando com [ e terminando com ]
2. NÃO adicione texto, markdown ou explicações
3. Busque PELO MENOS 10 startups diferentes
4. Para CADA startup, preencha TODOS os campos possíveis
5. Use "Não informado" APENAS se realmente não houver informação nas fontes

FORMATO OBRIGATÓRIO (cada startup):
{{
  "nome": "Nome Completo da Startup",
  "site": "https://website.com ou Não informado",
  "setor": "Setor específico (ex: Fintech, HealthTech, SaaS)",
  "ano_fundacao": "YYYY ou Não informado",
  "valor_investimento": "US$ X milhões ou R$ X milhões ou Não informado",
  "rodada": "Série A / Seed / Série B / etc ou Não informado",
  "data_investimento": "YYYY-MM-DD ou YYYY ou Não informado",
  "vc_investidor": "{vc_name}",
  "descricao_breve": "Descrição clara do produto/serviço (1-2 frases)",
  "linkedin_fundador": "https://linkedin.com/in/fundador ou Não informado"
}}

PRIORIDADES DE BUSCA:
- Valores de investimento SEMPRE que mencionados
- Datas específicas de rodadas
- URLs reais de websites
- LinkedIn de fundadores quando citados
- Descrições claras baseadas no conteúdo

IMPORTANTE: Seja COMPLETO e PRECISO. Extraia o máximo de informações possível.

Retorne o JSON agora:"""
    
    try:
        response = analyze_func(prompt, max_tokens=5000, temperature=0.1)
        startups = processar_resposta_json(response)
        
        # Validar e normalizar
        return validar_startups(startups, vc_name)
        
    except Exception as e:
        print(f"⚠️ Erro na extração: {str(e)}")
        return []


def enriquecer_dados_faltantes(startups, vc_name, search_func, analyze_func, max_iteracoes=3):
    """
    Enriquece startups com dados faltantes através de buscas específicas
    
    Args:
        startups (list): Lista de startups com possíveis dados faltantes
        vc_name (str): Nome do VC
        search_func: Função de busca
        analyze_func: Função de análise
        max_iteracoes (int): Número máximo de ciclos de enriquecimento
    
    Returns:
        tuple: (startups_enriquecidas, lista_de_queries_executadas)
    """
    queries_executadas = []
    
    for iteracao in range(max_iteracoes):
        print(f"\n🔄 Ciclo de enriquecimento {iteracao + 1}/{max_iteracoes}")
        
        # Identificar startups com dados faltantes
        startups_incompletas = []
        for startup in startups:
            campos_vazios = identificar_campos_vazios(startup)
            if campos_vazios:
                startups_incompletas.append({
                    "startup": startup,
                    "campos_vazios": campos_vazios
                })
        
        if not startups_incompletas:
            print("✅ Todas as startups estão completas!")
            break
        
        print(f"📋 {len(startups_incompletas)} startups necessitam enriquecimento")
        
        # Processar até 5 startups por iteração (para não sobrecarregar)
        for item in startups_incompletas[:5]:
            startup = item["startup"]
            campos_vazios = item["campos_vazios"]
            
            # Gerar query específica para esta startup
            query = gerar_query_enriquecimento(startup, campos_vazios, vc_name)
            queries_executadas.append(query)
            
            print(f"  🔎 Buscando: {startup['nome']} - Campos: {', '.join(campos_vazios)}")
            
            try:
                # Busca específica
                fontes_especificas = search_func(query, num_results=3)
                
                if fontes_especificas:
                    # Enriquecer com novas informações
                    dados_novos = extrair_dados_especificos(
                        fontes_especificas,
                        startup,
                        campos_vazios,
                        analyze_func
                    )
                    
                    # Atualizar startup
                    for campo, valor in dados_novos.items():
                        if valor and valor != "Não informado":
                            startup[campo] = valor
                            print(f"    ✓ {campo}: {valor[:50]}...")
                
            except Exception as e:
                print(f"    ⚠️ Erro ao enriquecer: {str(e)}")
                continue
    
    return startups, queries_executadas


def identificar_campos_vazios(startup):
    """Identifica campos vazios ou com 'Não informado'"""
    campos_importantes = [
        'valor_investimento', 'data_investimento', 'rodada',
        'linkedin_fundador', 'site', 'ano_fundacao'
    ]
    
    vazios = []
    for campo in campos_importantes:
        valor = startup.get(campo, "")
        if not valor or valor == "Não informado" or valor == "—":
            vazios.append(campo)
    
    return vazios


def gerar_query_enriquecimento(startup, campos_vazios, vc_name):
    """Gera query específica para preencher campos faltantes"""
    nome = startup['nome']
    
    # Mapear campos para termos de busca
    termos = {
        'valor_investimento': 'funding amount raised',
        'data_investimento': 'investment date round',
        'rodada': 'funding round series',
        'linkedin_fundador': 'founder CEO LinkedIn profile',
        'site': 'official website',
        'ano_fundacao': 'founded year'
    }
    
    # Construir query focada
    termos_busca = ' '.join([termos.get(campo, campo) for campo in campos_vazios[:3]])
    
    query = f'"{nome}" {vc_name} {termos_busca}'
    
    return query


def extrair_dados_especificos(sources, startup, campos_vazios, analyze_func):
    """Extrai dados específicos para preencher campos faltantes"""
    if not sources:
        return {}
    
    context = f"Startup: {startup['nome']}\nCampos a preencher: {', '.join(campos_vazios)}\n\nFontes:\n\n"
    
    for i, source in enumerate(sources, 1):
        context += f"=== FONTE {i} ===\n{source['content'][:2000]}\n\n"
    
    prompt = f"""{context}

TAREFA: Extraia APENAS as informações específicas para preencher os campos vazios da startup "{startup['nome']}".

Campos necessários: {', '.join(campos_vazios)}

Retorne um JSON com APENAS os campos que você encontrou informações:
{{
  "campo1": "valor encontrado",
  "campo2": "valor encontrado"
}}

NÃO inclua campos se não encontrou informação válida nas fontes.
Retorne {{}} se nenhuma informação foi encontrada.

JSON:"""
    
    try:
        response = analyze_func(prompt, max_tokens=500, temperature=0.1)
        dados = processar_resposta_json(response)
        return dados if isinstance(dados, dict) else {}
    except:
        return {}


def selecionar_melhores_startups(startups, limite=10):
    """Seleciona as startups mais completas"""
    if len(startups) <= limite:
        return startups
    
    # Calcular score de completude
    for startup in startups:
        campos_preenchidos = sum(
            1 for v in startup.values()
            if v and v != "Não informado" and v != "—"
        )
        startup['_completude_score'] = campos_preenchidos
    
    # Ordenar por completude e pegar top N
    startups_ordenadas = sorted(
        startups,
        key=lambda x: x.get('_completude_score', 0),
        reverse=True
    )
    
    # Remover score temporário
    melhores = startups_ordenadas[:limite]
    for s in melhores:
        s.pop('_completude_score', None)
    
    return melhores


def validar_startups(startups, vc_name):
    """Valida e normaliza estrutura das startups"""
    if not isinstance(startups, list):
        return []
    
    campos_obrigatorios = [
        'nome', 'site', 'setor', 'ano_fundacao', 'valor_investimento',
        'rodada', 'data_investimento', 'vc_investidor', 'descricao_breve',
        'linkedin_fundador'
    ]
    
    validadas = []
    for item in startups:
        if not isinstance(item, dict):
            continue
        
        # Garantir todos os campos
        startup_validada = {}
        for campo in campos_obrigatorios:
            valor = item.get(campo, "Não informado")
            startup_validada[campo] = valor if valor else "Não informado"
        
        # Garantir que vc_investidor está correto
        startup_validada['vc_investidor'] = vc_name
        
        # Normalizar nome
        if startup_validada['nome'] and startup_validada['nome'] != "Não informado":
            validadas.append(startup_validada)
    
    return validadas


def processar_resposta_json(response):
    """Processa resposta da IA e extrai JSON"""
    try:
        # Limpar resposta
        cleaned = response.strip()
        
        # Remover markdown
        if cleaned.startswith('```'):
            lines = cleaned.split('\n')
            cleaned = '\n'.join(lines[1:-1] if len(lines) > 2 else lines[1:])
        
        # Encontrar JSON
        json_start = cleaned.find('[') if '[' in cleaned else cleaned.find('{')
        json_end = cleaned.rfind(']') + 1 if ']' in cleaned else cleaned.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_string = cleaned[json_start:json_end]
            return json.loads(json_string)
        
        return []
    except:
        return []