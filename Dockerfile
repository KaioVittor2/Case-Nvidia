# Use uma imagem base com Python (escolha a versão apropriada)
FROM python:3.11-slim

# Defina o diretório de trabalho dentro do container
WORKDIR /app

# Adiciona o diretório /app/src ao caminho de busca de módulos do Python
ENV PYTHONPATH="/app/src"

# Copie os arquivos de requisitos e instale dependências primeiro
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copie todo o código da aplicação
COPY . .

# Exponha portas se necessário (por exemplo para APIs ou dashboards)
EXPOSE 8000

# Comando padrão para rodar (ajuste para seu script principal)
CMD ["python", "app.py"]
