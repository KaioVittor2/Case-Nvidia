# Descobrir Investimentos de VCs

Uma plataforma web avançada para pesquisa e análise de startups investidas por Venture Capitals, com capacidade de pesquisa profunda em múltiplas camadas usando inteligência artificial.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Visão Geral

Este sistema permite descobrir e analisar startups que receberam investimentos de fundos de Venture Capital específicos. Oferece dois modos de pesquisa:

- **Pesquisa Normal**: Busca rápida usando Perplexity AI (~30 segundos)
- **Pesquisa Profunda**: Busca em múltiplas camadas com análise detalhada usando Exa + Cerebras AI (~60-90 segundos)

## Funcionalidades Principais

### Core Features
- Pesquisa por múltiplos VCs simultaneamente
- Visualização em cards modernos e responsivos
- Filtros avançados (ano, setor, valor de investimento)
- Exportação para CSV
- Geração de PDF
- Histórico de pesquisas persistente
- Sistema de favoritos

### Deep Research
- Busca em 2 camadas para maior precisão
- Geração automática de queries de aprofundamento
- Coleta de 10-15+ fontes por pesquisa
- Metadados detalhados sobre o processo
- Validação e normalização de dados

### Analytics
- Estatísticas agregadas (total investido, número de startups)
- Gráfico de distribuição por setor
- Comparação entre startups
- Detalhamento completo por startup

---

## Arquitetura

```
projeto/
├── src/
│   ├── agents/           # Agentes de IA
│   │   ├── vc_research_agent.py      # Pesquisa normal
│   │   └── deep_research_agent.py    # Pesquisa profunda
│   ├── tasks/            # Tarefas e workflows
│   │   ├── search.py
│   │   └── deep_research_task.py
│   └── pipelines/        # Orquestração
│       ├── pipeline_manager.py
│       └── deep_pipeline_manager.py
├── static/
│   ├── script.js         # Lógica do frontend
│   └── style.css         # Estilos modernos
├── templates/
│   └── index.html        # Interface web
├── app.py                # Servidor Flask
├── requirements.txt      # Dependências Python
└── config.json           # Configurações
```

### Tecnologias Utilizadas

**Backend:**
- Flask (servidor web)
- CrewAI (orquestração de agentes)
- SQLite (persistência de dados)
- Python 3.11+

**APIs de IA:**
- Perplexity AI (pesquisa normal)
- Exa API (busca web semântica para Deep Research)
- Cerebras AI (análise ultrarrápida para Deep Research)

**Frontend:**
- HTML5 + CSS3 moderno
- JavaScript vanilla (sem frameworks)
- Design responsivo
- Animações suaves

---

## Instalação

### Pré-requisitos

- Python 3.11 ou superior
- pip (gerenciador de pacotes Python)
- Chaves de API (veja seção de Configuração)

### Instalação Padrão

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/vc-research.git
cd vc-research

# Construa as imagens do Docker
# dentro da pasta da aplicação.
docker build -t nvidia-inception-search .

# Edite keys.env com suas chaves
cp keys.env.example keys.env

# Inicie o servidor
docker run -p 8000:8000 nvidia-inception

# Acesse http://localhost:8000
```

### Docker

```bash
# Build da imagem
docker build -t vc-research .

# Execute o container
docker run -p 8000:8000 vc-research

# Acesse http://localhost:8000
```

---

## Configuração

### API Keys

Crie/edite o arquivo `keys.env` na raiz do projeto:

```env
# Obrigatórias (Pesquisa Normal)
OPENAI_API_KEY=sk-...
PERPLEXITY_API_KEY=pplx-...

# Obrigatórias (Deep Research)
EXA_API_KEY=...
CEREBRAS_API_KEY=csk-...
```

Edite a chave também na src\pipelines\pipeline_manager.py, na linha 14 onde está:

```env
perplexity_llm = LLM(
    model="sonar-pro", # Você confirmou que este modelo funciona para você
    base_url="https://api.perplexity.ai/", # Manter para garantir
    api_key="" # Digite sua chave de API aqui
)
```

**Onde conseguir:**

| API | URL | Propósito |
|-----|-----|-----------|
| OpenAI | https://platform.openai.com/api-keys | Agentes de IA |
| Perplexity | https://www.perplexity.ai/settings/api | Pesquisa web |
| Exa | https://exa.ai/ | Busca semântica (Deep) |
| Cerebras | https://cloud.cerebras.ai/ | Inferência rápida (Deep) |

### Configuração Avançada

Edite `config.json`:

```json
{
  "flask": {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false
  },
  "api_keys": {}
}
```

---

## Uso

### Interface Web

1. Acesse `http://localhost:5000`
2. Digite os nomes dos VCs separados por vírgula
   - Exemplo: `Sequoia Capital, a16z, Kaszek Ventures`
3. Escolha o tipo de pesquisa:
   - **Pesquisar**: Busca rápida e eficiente
   - **Pesquisa Profunda**: Análise detalhada em camadas
4. Explore os resultados:
   - Filtre por ano, setor ou valor
   - Compare startups
   - Exporte para CSV
   - Salve favoritos

### API REST

#### Pesquisa Normal

```bash
POST /pesquisar
Content-Type: application/json

{
  "vc_list": ["Sequoia Capital", "a16z"]
}
```

**Resposta:**
```json
{
  "resultado": [
    {
      "nome": "Airbnb",
      "site": "https://www.airbnb.com",
      "setor": "Marketplace",
      "ano_fundacao": "2008",
      "valor_investimento": "US$ 20 milhões",
      "rodada": "Série A",
      "data_investimento": "2010-11-16",
      "vc_investidor": "Sequoia Capital",
      "descricao_breve": "Plataforma de hospedagem...",
      "linkedin_fundador": "https://linkedin.com/in/..."
    }
  ]
}
```

#### Pesquisa Profunda

```bash
POST /pesquisar-profundo
Content-Type: application/json

{
  "vc_list": ["Kaszek Ventures"]
}
```

**Resposta:**
```json
{
  "resultado": [...],
  "metadados": {
    "vcs_pesquisadas": ["Kaszek Ventures"],
    "total_fontes": 11,
    "fontes_camada1": 6,
    "fontes_camada2": 5,
    "query_inicial": "list of startups...",
    "query_aprofundamento": "detailed funding...",
    "total_startups": 15
  },
  "tipo": "pesquisa_profunda"
}
```

#### Outros Endpoints

```bash
# Verificar status das APIs
GET /status

# Histórico de pesquisas
GET /historico
```

---

## Comparação: Normal vs Profunda

| Característica | Normal | Profunda |
|----------------|--------|----------|
| **Tempo** | 30s | 60-90s |
| **Camadas** | 1 | 2+ |
| **Fontes** | 5-10 | 10-15 |
| **Precisão** | Boa (85%) | Excelente (95%) |
| **APIs** | Perplexity | Exa + Cerebras |
| **Custo/pesquisa** | ~$0.02 | ~$0.05-0.07 |
| **Ideal para** | Pesquisas rápidas, testes | Due diligence, análises estratégicas |

---


## Estrutura de Dados

### Objeto Startup

```javascript
{
  "nome": string,              // Nome da startup
  "site": string,              // URL do website
  "setor": string,             // Setor/indústria
  "ano_fundacao": string,      // Ano de fundação
  "valor_investimento": string,// Valor formatado (ex: "US$ 10 milhões")
  "rodada": string,            // Tipo de rodada (Seed, Série A, etc)
  "data_investimento": string, // Data no formato YYYY-MM-DD
  "vc_investidor": string,     // Nome da VC investidora
  "descricao_breve": string,   // Descrição da startup
  "linkedin_fundador": string  // URL do LinkedIn do fundador
}
```

---

## Troubleshooting

### Problemas Comuns

**Erro: "No module named 'src'"**
```bash
# Criar arquivos __init__.py
touch src/__init__.py
touch src/agents/__init__.py
touch src/tasks/__init__.py
touch src/pipelines/__init__.py
```

**Erro: "table pesquisa has no column named tipo_pesquisa"**
```bash
# Migrar banco de dados
python migrate_database.py
```

**Deep Research não disponível**
```bash
# Instalar dependências
pip install exa-py cerebras-cloud-sdk

# Configurar API keys no keys.env
```

**Botão "Pesquisa Profunda" não aparece**
```bash
# Limpar cache do navegador
Ctrl + Shift + R (Windows/Linux)
Cmd + Shift + R (Mac)
```

### Logs e Debugging

```bash
# Ver logs detalhados
python app.py  # Console mostra todos os logs

# Verificar status das APIs
curl http://localhost:5000/status
```



**Nunca commite arquivos contendo:**
- `keys.env`
- `*.db` (bancos de dados)
- Logs com informações sensíveis

---

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## Suporte

Qualquer necessidade de suporte pode entrar em contato com o desenvolvedor desse repositório: kaio.silva@sou.inteli.edu.br

---

**Aviso Legal**: Este sistema é fornecido apenas para fins informativos e educacionais. Os dados retornados dependem da disponibilidade e precisão das APIs externas. Sempre valide informações críticas com fontes oficiais antes de tomar decisões de investimento.