# api/index.py

# Importação das bibliotecas necessárias
from flask import Flask, request, jsonify
from flask_cors import CORS
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from collections import Counter
import nltk
import os  # Importe o módulo 'os'

# --- Bloco de Inicialização NLTK (Corrigido para Vercel) ---
# Define um diretório gravável no ambiente Vercel
nltk_data_dir = os.path.join('/tmp', 'nltk_data')

# Cria o diretório se ele não existir
if not os.path.exists(nltk_data_dir):
    os.makedirs(nltk_data_dir)

# Adiciona o caminho temporário ao path de dados do NLTK
if nltk_data_dir not in nltk.data.path:
    nltk.data.path.append(nltk_data_dir)

# Baixa os pacotes para o diretório /tmp, se ainda não tiverem sido baixados
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    print("Baixando 'punkt' para /tmp/nltk_data...")
    nltk.download('punkt', download_dir=nltk_data_dir, quiet=True)
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    print("Baixando 'stopwords' para /tmp/nltk_data...")
    nltk.download('stopwords', download_dir=nltk_data_dir, quiet=True)

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize


# --- Configuração da Aplicação Flask ---
# A Vercel vai transformar este 'app' em uma função sem servidor.
app = Flask(__name__)
# Habilita o CORS para todas as origens, o que é seguro neste ambiente sem servidor.
CORS(app)

# Instancia o analisador de sentimento uma única vez para reutilização.
analyzer = SentimentIntensityAnalyzer()

# Prepara a lista de palavras a serem ignoradas (stopwords) em português e inglês.
stop_words = set(stopwords.words('portuguese')).union(set(stopwords.words('english')))

# Define os temas que queremos rastrear.
THEMES = ["entrega", "produto", "atendimento", "preço"]

# --- Endpoint da API ---
# A Vercel vai direcionar requisições para /api/index para esta função.
@app.route('/api/index', methods=['POST'])
def analyze_feedbacks_endpoint():
    # Pega os dados JSON enviados na requisição.
    data = request.get_json()
    
    # Validação para garantir que os dados e o texto foram enviados.
    if not data or 'text' not in data:
        return jsonify({"error": "O campo 'text' não foi encontrado no corpo da requisição."}), 400
        
    text = data.get('text', '')
    if not text.strip():
        return jsonify({"error": "O campo de texto não pode ser vazio."}), 400

    # 1. Separa os feedbacks por linha, ignorando linhas em branco.
    feedbacks = [f.strip() for f in text.split('\n') if f.strip()]
    
    # 2. Inicializa os contadores e listas para armazenar os resultados.
    sentiment_counts = {'positive': 0, 'neutral': 0, 'negative': 0}
    theme_counts = {theme: 0 for theme in THEMES}
    positive_examples = []
    negative_examples = []

    # 3. Itera sobre cada feedback para analisá-lo individualmente.
    for feedback in feedbacks:
        # Análise de sentimento com VADER.
        score = analyzer.polarity_scores(feedback)['compound']
        
        if score >= 0.05:
            sentiment_counts['positive'] += 1
            if len(positive_examples) < 3: positive_examples.append(feedback)
        elif score <= -0.05:
            sentiment_counts['negative'] += 1
            if len(negative_examples) < 3: negative_examples.append(feedback)
        else:
            sentiment_counts['neutral'] += 1
        
        # Identificação de temas (case-insensitive).
        feedback_lower = feedback.lower()
        for theme in THEMES:
            if theme in feedback_lower:
                theme_counts[theme] += 1
    
    # 4. Análise de frequência de palavras no texto completo.
    words = word_tokenize(text.lower())
    # Filtra palavras que não são alfabéticas e que estão na lista de stopwords.
    filtered_words = [word for word in words if word.isalpha() and word not in stop_words]
    # Conta e pega as 10 palavras mais comuns.
    top_words = [{"word": item[0], "count": item[1]} for item in Counter(filtered_words).most_common(10)]

    # 5. Monta o dicionário de resultados final.
    result = {
        "total_feedbacks": len(feedbacks),
        "sentiment_counts": sentiment_counts,
        "theme_frequency": theme_counts,
        "top_words": top_words,
        "positive_examples": positive_examples,
        "negative_examples": negative_examples,
    }

    # Converte o dicionário para o formato JSON e o envia como resposta.
    return jsonify(result)

# O bloco 'if __name__ == "__main__":' foi removido porque a Vercel gerencia o servidor.
