from crewai import Agent, LLM
import os

openai_llm = LLM(
    model="gpt-4o-mini",
    api_key=os.environ.get("OPENAI_API_KEY")
)

cnpj_lookup_agent = Agent(
    role="Consultor de Dados Empresariais",
    goal="Enriquecer startups com informações de CNPJ",
    backstory="Você consulta APIs e bases públicas para buscar dados de CNPJs.",
    llm=openai_llm,
    verbose=True
)
