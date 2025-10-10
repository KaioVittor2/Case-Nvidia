from crewai import Task
from agents.cnpj_lookup_agent import cnpj_lookup_agent

cnpj_lookup_task = Task(
    description=(
        "Receba uma lista de startups em JSON e enriqueça cada uma com os dados do CNPJ, "
        "consultando APIs externas e retornando o resultado no mesmo formato JSON enriquecido."
    ),
    expected_output="Lista JSON de startups com chave adicional 'cnpj_dados'.",
    agent=cnpj_lookup_agent,
    output_file=None
)
