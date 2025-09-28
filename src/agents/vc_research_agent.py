# arquivo: src/agents/vc_research_agent.py
from crewai import Agent

vc_research_agent = Agent(
    role="Especialista em Venture Capital",
    goal="Identificar startups investidas por venture capitals específicas",
    backstory=(
        "Você é um especialista em venture capital com acesso a dados atualizados "
        "sobre investimentos e portfólios de fundos de investimento."
    ),
    verbose=True,
    allow_delegation=False
)