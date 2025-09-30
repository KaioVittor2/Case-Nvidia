# Deep Research - Documentação

## 📋 Visão Geral

A funcionalidade de **Deep Research** implementa uma pesquisa em múltiplas camadas para encontrar informações detalhadas sobre startups investidas por Venture Capitals. Baseado no notebook `Deep_Research_agents_Nvidia.ipynb`, o sistema realiza:

1. **Camada 1**: Pesquisa inicial ampla
2. **Análise**: Geração de pergunta de aprofundamento
3. **Camada 2**: Pesquisa focada e detalhada
4. **Síntese**: Combinação de todas as fontes em relatório estruturado

## 🔧 Configuração

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar Chaves de API

Copie o arquivo de exemplo e adicione suas chaves:

```bash
cp keys.env.example keys.env
```

Edite `keys.env` e adicione suas chaves:

```env
EXA_API_KEY=sua_chave_exa
CEREBRAS_API_KEY=sua_chave_cerebras
```

#### Onde Obter as Chaves:

- **Exa API**: https://exa.ai/ - API de busca semântica avançada
- **Cerebras API**: https://cerebras.ai/ - Inferência de IA ultrarrápida

### 3. Estrutura de Arquivos Criados

```
src/
├── agents/
│   └── deep_research_agent.py      # Agente de pesquisa profunda
├── tasks/
│   └── deep_research_task.py       # Task de orquestração
└── pipelines/
    └── deep_pipeline_manager.py    # Gerenciador do pipeline profundo

app.py                               # Atualizado com novos endpoints
requirements.txt                     # Dependências atualizadas
keys.env.example                     # Exemplo de configuração
```

## 🚀 Uso

### Endpoint da API

**POST** `/pesquisar-profundo`

```json
{
  "vc_list": ["Sequoia Capital", "Andreessen Horowitz", "Kaszek Ventures"]
}
```

**Resposta:**

```json
{
  "resultado": [
    {
      "nome": "Startup XYZ",
      "site": "https://xyz.com",
      "setor": "Fintech",
      "ano_fundacao": "2020",
      "valor_investimento": "US$ 15 milhões",
      "rodada": "Série A",
      "data_investimento": "2023-06-15",
      "vc_investidor": "Sequoia Capital",
      "descricao_breve": "Plataforma de pagamentos digitais...",
      "linkedin_fundador": "https://linkedin.com/in/fundador"
    }
  ],
  "metadados": {
    "vcs_pesquisadas": ["Sequoia Capital", "Andreessen Horowitz"],
    "total_fontes": 11,
    "query_inicial": "startups investidas por Sequoia Capital, Andreessen Horowitz",
    "query_aprofundamento": "Detalhes de investimentos recentes...",
    "total_startups": 20
  },
  "tipo": "pesquisa_profunda"
}
```

### Uso Programático

```python
from pipelines.deep_pipeline_manager import pesquisar_startups_profundo

# Lista de VCs para pesquisar
vcs = ["Sequoia Capital", "Kaszek Ventures", "Monashees"]

# Executar pesquisa profunda
resultado = pesquisar_startups_profundo(vcs)

# Acessar dados
startups = resultado["resultado"]
metadados = resultado["metadados"]

print(f"Encontradas {len(startups)} startups")
print(f"Fontes consultadas: {metadados['total_fontes']}")
```

### Verificar Status das APIs

**GET** `/status`

Retorna informações sobre as configurações:

```json
{
  "exa_api_configurada": true,
  "cerebras_api_configurada": true,
  "openai_api_configurada": true,
  "perplexity_api_configurada": true,
  "total_pesquisas": 15,
  "pesquisas_normais": 10,
  "pesquisas_profundas": 5
}
```

## 📊 Comparação: Pesquisa Normal vs Profunda

| Característica | Pesquisa Normal | Pesquisa Profunda |
|---------------|-----------------|-------------------|
| **Camadas** | 1 | 2+ |
| **Fontes** | 5-10 | 10-15 |
| **Tempo** | ~30s | ~60-90s |
| **Precisão** | Boa | Excelente |
| **Detalhes** | Básicos | Completos |
| **Custo API** | Baixo | Médio |

## 🔍 Como Funciona

### Fluxo do Deep Research

```
1. CAMADA 1: PESQUISA INICIAL
   ├─ Query: "startups investidas por [VCs]"
   ├─ Coleta: 6 fontes iniciais
   └─ Análise: Identificar gaps de informação

2. GERAÇÃO DE FOLLOW-UP
   ├─ Análise das fontes iniciais
   ├─ Identificação de áreas não cobertas
   └─ Formulação de pergunta específica

3. CAMADA 2: APROFUNDAMENTO
   ├─ Query: Pergunta gerada automaticamente
   ├─ Coleta: 5 fontes adicionais
   └─ Marcação: [Aprofundamento] nos títulos

4. SÍNTESE FINAL
   ├─ Combinação: 11+ fontes totais
   ├─ Análise: IA processa todo contexto
   └─ Output: JSON estruturado com 10+ startups/VC
```

### Exemplo de Follow-up Gerado

**Query Inicial:**
```
"startups investidas por Sequoia Capital"
```

**Follow-up Gerado Automaticamente:**
```
"Detalhes sobre rodadas de investimento e valores específicos 
de startups da Sequoia Capital nos últimos 3 anos"
```

## 💡 Vantagens do Deep Research

1. **Maior Cobertura**: Coleta mais fontes de informação
2. **Refinamento Automático**: Identifica gaps e busca informações específicas
3. **Melhor Qualidade**: Dados mais completos e precisos
4. **Contextualização**: Entende padrões de investimento
5. **Validação Cruzada**: Múltiplas fontes confirmam informações

## 🎯 Casos de Uso

### 1. Due Diligence de VCs
```python
# Analisar portfólio completo de uma VC
resultado = pesquisar_startups_profundo(["Tiger Global"])
```

### 2. Benchmark de Mercado
```python
# Comparar investimentos de VCs concorrentes
vcs_concorrentes = ["a16z", "Sequoia Capital", "Accel"]
resultado = pesquisar_startups_profundo(vcs_concorrentes)
```

### 3. Análise de Setor
```python
# Identificar trends em setores específicos
# O sistema automaticamente identifica padrões
resultado = pesquisar_startups_profundo(["Y Combinator"])
```

## 🛠️ Troubleshooting

### Erro: "EXA_API_KEY não configurada"

**Solução:**
```bash
# Verifique se keys.env existe
ls keys.env

# Verifique o conteúdo (sem expor a chave)
cat keys.env | grep EXA_API_KEY

# Reinicie a aplicação após adicionar a chave
```

### Erro: "Nenhuma fonte encontrada"

**Possíveis causas:**
1. Query muito específica
2. VCs não encontradas nos índices
3. Limite de API atingido

**Solução:**
```python
# Simplifique a query ou use VCs mais conhecidas
vcs = ["Sequoia Capital"]  # Ao invés de nomes muito específicos
```

### Resposta sem JSON válido

**Solução:**
O sistema automaticamente tenta extrair JSON da resposta. Se falhar:
1. Verifique os logs do console
2. A resposta bruta é retornada em `resposta_bruta`
3. Ajuste o prompt se necessário

## 📈 Otimizações

### 1. Controle de Custos

```python
# No arquivo deep_research_agent.py, ajuste:
search_web_exa(query, num_results=3)  # Menos resultados = menor custo
```

### 2. Velocidade vs Qualidade

```python
# Para respostas mais rápidas:
analyze_with_cerebras(prompt, max_tokens=300, temperature=0.1)

# Para respostas mais criativas:
analyze_with_cerebras(prompt, max_tokens=800, temperature=0.5)
```

### 3. Cache de Resultados

As pesquisas são automaticamente salvas no banco SQLite:
- Reutilize resultados anteriores
- Evite pesquisas duplicadas
- Histórico completo disponível

## 🔐 Segurança

### Boas Práticas

1. **Nunca commite** o arquivo `keys.env`
2. Adicione ao `.gitignore`:
```
keys.env
*.db
__pycache__/
```

3. Use variáveis de ambiente em produção:
```bash
export EXA_API_KEY="sua_chave"
export CEREBRAS_API_KEY="sua_chave"
```

## 📝 Logs e Monitoramento

O sistema fornece logs detalhados:

```
🔍 Iniciando pesquisa profunda para VCs: Sequoia Capital, a16z
📊 CAMADA 1: Pesquisa inicial...
✓ Encontradas 6 fontes na pesquisa inicial
🤔 Gerando pergunta de aprofundamento...
✓ Pergunta gerada: Detalhes sobre...
📊 CAMADA 2: Pesquisa de aprofundamento...
✓ Encontradas 5 fontes adicionais
📚 Total de fontes coletadas: 11
🧠 Sintetizando relatório final...
⚙️ Processando resultado...
✅ Pesquisa concluída com sucesso! 23 startups encontradas
```

## 🧪 Testes

### Testar Manualmente

```bash
# Inicie o servidor
python app.py

# Em outro terminal, teste o endpoint
curl -X POST http://localhost:5000/pesquisar-profundo \
  -H "Content-Type: application/json" \
  -d '{"vc_list": ["Sequoia Capital"]}'
```

### Testar Programaticamente

```python
# Criar arquivo test_deep_research.py
from pipelines.deep_pipeline_manager import pesquisar_startups_profundo

# Teste básico
resultado = pesquisar_startups_profundo(["Kaszek Ventures"])

# Validações
assert "resultado" in resultado
assert isinstance(resultado["resultado"], list)
assert len(resultado["resultado"]) > 0

print("✅ Testes passaram!")
```

## 🆚 Quando Usar Cada Método

### Use Pesquisa Normal quando:
- Precisa de resultados rápidos
- Informações básicas são suficientes
- Orçamento de API limitado
- Testando/prototipando

### Use Pesquisa Profunda quando:
- Precisa de máxima precisão
- Due diligence importante
- Tempo não é crítico
- Informações completas necessárias
- Análise estratégica

## 🔄 Atualizações Futuras

Melhorias planejadas:
- [ ] Camada 3: Validação cruzada
- [ ] Cache inteligente de queries similares
- [ ] Exportação em PDF/Excel
- [ ] Visualizações gráficas
- [ ] API assíncrona para pesquisas longas
- [ ] Integração com mais fontes de dados

## 📚 Recursos Adicionais

- [Documentação Exa API](https://docs.exa.ai/)
- [Documentação Cerebras](https://docs.cerebras.ai/)
- [CrewAI Documentation](https://docs.crewai.com/)
- [Notebook Original](Deep_Research_agents_Nvidia.ipynb)

## 🤝 Contribuindo

Para adicionar novas funcionalidades:

1. Siga a estrutura existente
2. Adicione testes
3. Documente mudanças
4. Atualize este README

## 📄 Licença

Este projeto segue a mesma licença do projeto principal.

---

**Desenvolvido com base no notebook Deep_Research_agents_Nvidia.ipynb**