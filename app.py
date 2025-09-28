import os
from dotenv import load_dotenv
import json


# Carrega as variáveis do arquivo keys.env para o ambiente do sistema
load_dotenv('keys.env')

from flask import Flask, request, jsonify
from utils.config_loader import load_config
from pipelines.pipeline_manager import pesquisar_startups_por_vcs

# Pega o caminho absoluto do diretório onde este script (app.py) está localizado.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Constrói o caminho completo e seguro para o arquivo config.json.
config_path = os.path.join(BASE_DIR, "config.json")

# Carrega a configuração usando o caminho completo.
config = load_config(config_path)

app = Flask(__name__)

@app.route("/pesquisar", methods=["POST"])
def pesquisar():
    data = request.json
    lista_vcs = data.get("vc_list", [])
    if not lista_vcs:
        return jsonify({"erro": "vc_list é obrigatório"}), 400

    # 1. Execute o crew e pegue o objeto de resultado
    resultado_crew = pesquisar_startups_por_vcs(lista_vcs)

    # 2. Extraia o resultado em texto bruto (raw) do objeto
    resultado_raw_string = resultado_crew.raw

    # 3. Converta a string (que deve ser um JSON) em um objeto Python (lista/dicionário)
    try:
        dados_json = json.loads(resultado_raw_string)
    except json.JSONDecodeError:
        # Medida de segurança caso o LLM retorne um texto que não seja um JSON válido
        dados_json = {
            "erro": "A resposta do agente não é um JSON válido.",
            "saida_bruta": resultado_raw_string
        }

    # 4. Agora sim, retorne o objeto Python que o jsonify consegue processar
    return jsonify({"resultado": dados_json})

if __name__ == "__main__":
    app.run(host=config["flask"]["host"], port=config["flask"]["port"], debug=config["flask"]["debug"])