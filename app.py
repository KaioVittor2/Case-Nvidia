import os
from dotenv import load_dotenv
import json
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, jsonify, render_template

# Carrega as variáveis do arquivo keys.env para o ambiente do sistema
load_dotenv('keys.env')

from utils.config_loader import load_config
from pipelines.pipeline_manager import pesquisar_startups_por_vcs

# Pega o caminho absoluto do diretório onde este script (app.py) está localizado.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Constrói o caminho completo e seguro para o arquivo config.json.
config_path = os.path.join(BASE_DIR, "config.json")

# Carrega a configuração usando o caminho completo.
config = load_config(config_path)

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

# -------------------------------
# Configuração do SQLite persistente
# -------------------------------
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)  # cria a pasta se não existir

db_path = os.path.join(BASE_DIR, "pesquisas.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# Modelo
class Pesquisa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vc_list = db.Column(db.String, nullable=False)
    resultado = db.Column(db.Text, nullable=False)

# Cria o banco na primeira execução
with app.app_context():
    db.create_all()

@app.route("/pesquisar", methods=["POST"])
def pesquisar():
    try:
        data = request.json
        lista_vcs = data.get("vc_list", [])
        if not lista_vcs:
            return jsonify({"erro": "vc_list é obrigatório"}), 400

        # Executa o pipeline
        resultado_crew = pesquisar_startups_por_vcs(lista_vcs)

        # Garante que temos uma string para processar
        resultado_raw_string = getattr(resultado_crew, "raw", None)
        if not resultado_raw_string:
            return jsonify({
                "erro": "Não foi possível obter resultado do agente.",
                "saida_bruta": str(resultado_crew)
            }), 500

        # Tenta transformar em JSON
        try:
            dados_json = json.loads(resultado_raw_string)
        except json.JSONDecodeError:
            dados_json = {
                "erro": "A resposta do agente não é um JSON válido.",
                "saida_bruta": resultado_raw_string
            }

        # Salvar no banco
        pesquisa = Pesquisa(
            vc_list=",".join(lista_vcs),
            resultado=json.dumps(dados_json, ensure_ascii=False)
        )
        db.session.add(pesquisa)
        db.session.commit()

        return jsonify({"resultado": dados_json})

    except Exception as e:
        # Captura erros inesperados
        return jsonify({"erro": f"Ocorreu um erro interno: {str(e)}"}), 500

@app.route("/historico", methods=["GET"])
def historico():
    pesquisas = Pesquisa.query.all()
    historico = []
    for p in pesquisas:
        historico.append({
            "id": p.id,
            "vc_list": p.vc_list,
            "resultado": json.loads(p.resultado)
        })
    return jsonify(historico)

if __name__ == "__main__":
    app.run(host=config["flask"]["host"], port=config["flask"]["port"], debug=config["flask"]["debug"])