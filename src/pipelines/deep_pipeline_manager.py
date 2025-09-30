# arquivo: src/pipelines/deep_pipeline_manager.py
import os
import json
import re

def pesquisar_startups_profundo(lista_vcs: list):
    """
    Realiza pesquisa profunda em múltiplas camadas sobre startups investidas por VCs
    
    Esta função implementa a lógica do notebook Deep_Research_agents_Nvidia.ipynb,
    adaptada para o contexto do projeto.
    
    Args:
        lista_vcs (list): Lista de nomes de Venture Capitals para pesquisar
    
    Returns:
        dict: Resultado da pesquisa com dados estruturados em JSON
    """
    print(f"🔍 Iniciando pesquisa profunda para VCs: {', '.join(lista_vcs)}")
    
    # Importar funções necessárias
    try:
        from src.agents.deep_research_agent import (
            search_web_exa,
            generate_follow_up_query,
            synthesize_final_report,
            DEPENDENCIES_AVAILABLE
        )
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
    
    # Query inicial
    query_base = f"startups invested by {', '.join(lista_vcs)}"
    
    # ===== CAMADA 1: PESQUISA INICIAL =====
    print("\n📊 CAMADA 1: Pesquisa inicial...")
    initial_query = f"list of startups that received investment from {', '.join(lista_vcs)} with details about funding amount, round, and sector"
    
    try:
        initial_sources = search_web_exa(initial_query, num_results=6)
        print(f"✓ Encontradas {len(initial_sources)} fontes na pesquisa inicial")
    except Exception as e:
        print(f"❌ Erro na pesquisa inicial: {str(e)}")
        return {
            "erro": f"Erro na busca inicial: {str(e)}",
            "resultado": []
        }
    
    if not initial_sources:
        print("❌ Nenhuma fonte encontrada na pesquisa inicial")
        return {
            "erro": "Nenhuma fonte encontrada na pesquisa inicial. Tente VCs mais conhecidas.",
            "resultado": []
        }
    
    # ===== CAMADA 2: GERAR PERGUNTA DE APROFUNDAMENTO =====
    print("\n🤔 Gerando pergunta de aprofundamento...")
    try:
        follow_up_query = generate_follow_up_query(initial_sources, query_base)
        print(f"✓ Pergunta gerada: {follow_up_query}")
    except Exception as e:
        print(f"⚠️ Erro ao gerar follow-up, usando query padrão: {str(e)}")
        follow_up_query = f"detailed investment information {', '.join(lista_vcs)} startups funding amounts dates"
    
    # ===== CAMADA 2: PESQUISA DE APROFUNDAMENTO =====
    print("\n📊 CAMADA 2: Pesquisa de aprofundamento...")
    try:
        follow_up_sources = search_web_exa(follow_up_query, num_results=5)
        print(f"✓ Encontradas {len(follow_up_sources)} fontes adicionais")
    except Exception as e:
        print(f"⚠️ Erro na pesquisa de aprofundamento: {str(e)}")
        follow_up_sources = []
    
    # Marcar fontes de follow-up
    for source in follow_up_sources:
        source['title'] = f"[Aprofundamento] {source['title']}"
    
    # ===== COMBINAR TODAS AS FONTES =====
    all_sources = initial_sources + follow_up_sources
    print(f"\n📚 Total de fontes coletadas: {len(all_sources)}")
    
    if len(all_sources) < 3:
        return {
            "erro": "Poucas fontes encontradas para gerar relatório confiável",
            "resultado": []
        }
    
    # ===== SÍNTESE FINAL =====
    print("\n🧠 Sintetizando relatório final...")
    try:
        final_report = synthesize_final_report(
            all_sources,
            lista_vcs,
            query_base,
            follow_up_query
        )
    except Exception as e:
        print(f"❌ Erro na síntese: {str(e)}")
        return {
            "erro": f"Erro ao sintetizar relatório: {str(e)}",
            "resultado": []
        }
    
    # ===== PROCESSAR RESULTADO =====
    print("\n⚙️ Processando resultado...")
    try:
        # Tentar extrair JSON da resposta
        # Remover markdown se presente
        cleaned_response = final_report.strip()
        
        # Remover ```json e ``` se presente
        if cleaned_response.startswith('```'):
            lines = cleaned_response.split('\n')
            cleaned_response = '\n'.join(lines[1:-1] if len(lines) > 2 else lines[1:])
        
        # Encontrar o array JSON
        json_start = cleaned_response.find('[')
        json_end = cleaned_response.rfind(']') + 1
        
        if json_start != -1 and json_end > json_start:
            json_string = cleaned_response[json_start:json_end]
            
            # Tentar fazer parse
            dados_json = json.loads(json_string)
            
            # Validar estrutura
            if not isinstance(dados_json, list):
                raise ValueError("Resposta não é uma lista")
            
            # Validar e normalizar cada item
            dados_validados = []
            required_keys = ['nome', 'site', 'setor', 'ano_fundacao', 'valor_investimento', 
                           'rodada', 'data_investimento', 'vc_investidor', 'descricao_breve', 
                           'linkedin_fundador']
            
            for item in dados_json:
                if not isinstance(item, dict):
                    continue
                
                # Garantir que todas as chaves existem
                validated_item = {}
                for key in required_keys:
                    validated_item[key] = item.get(key, "Não informado")
                
                dados_validados.append(validated_item)
            
            if not dados_validados:
                raise ValueError("Nenhum item válido encontrado no JSON")
            
            print(f"✅ Pesquisa concluída com sucesso! {len(dados_validados)} startups encontradas")
            
            return {
                "resultado": dados_validados,
                "metadados": {
                    "vcs_pesquisadas": lista_vcs,
                    "total_fontes": len(all_sources),
                    "fontes_camada1": len(initial_sources),
                    "fontes_camada2": len(follow_up_sources),
                    "query_inicial": initial_query,
                    "query_aprofundamento": follow_up_query,
                    "total_startups": len(dados_validados)
                }
            }
        else:
            print("⚠️ Formato JSON não encontrado na resposta")
            # Tentar salvar o que foi retornado para debug
            return {
                "erro": "Formato JSON inválido na resposta da IA",
                "resposta_bruta": final_report[:500] + "..." if len(final_report) > 500 else final_report,
                "dica": "A IA retornou texto ao invés de JSON. Tente novamente ou ajuste o prompt."
            }
            
    except json.JSONDecodeError as e:
        print(f"❌ Erro ao decodificar JSON: {str(e)}")
        return {
            "erro": f"Erro ao processar JSON: {str(e)}",
            "resposta_bruta": final_report[:500] + "..." if len(final_report) > 500 else final_report,
            "dica": "Verifique se a resposta está em formato JSON válido"
        }
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return {
            "erro": f"Erro inesperado ao processar resultado: {str(e)}",
            "resposta_bruta": final_report[:500] + "..." if 'final_report' in locals() else ""
        }