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

# Léxico PT-BR customizado para VADER (inclui variantes sem acento).
# Observação: o VADER funciona melhor em inglês; este dicionário amplia
# a cobertura para português com termos comuns em feedbacks.
custom_pt_lexicon = {
    # Negativos fortes
    "odiei": -3.2, "odeio": -3.2, "odiar": -2.8,
    "horrível": -3.0, "horrivel": -3.0,
    "péssimo": -3.0, "pessimo": -3.0, "péssima": -3.0, "pessima": -3.0,
    "terrível": -2.8, "terrivel": -2.8,
    "pior": -2.6, "lixo": -2.6,
    "decepcionado": -2.4, "decepcionada": -2.4, "decepção": -2.4, "decepcao": -2.4,
    "insatisfeito": -2.3, "insatisfeita": -2.3, "insatisfação": -2.3, "insatisfacao": -2.3,
    "frustrado": -2.3, "frustrada": -2.3, "frustração": -2.3, "frustracao": -2.3,
    "ruim": -2.2, "horrendo": -2.2, "horrenda": -2.2,
    "caro": -1.8, "caríssima": -2.0, "carissimo": -2.0, "carissima": -2.0, "caríssima": -2.0,
    "lento": -2.0, "lenta": -2.0, "lentidão": -2.0, "lentidao": -2.0,
    "demora": -1.8, "demorado": -1.9, "demorada": -1.9, "atraso": -1.9, "atrasado": -1.9, "atrasada": -1.9,
    "defeito": -2.4, "defeituoso": -2.4, "defeituosa": -2.4, "quebrado": -2.4, "quebrada": -2.4,
    "falha": -2.0, "falhou": -2.2, "erro": -2.0, "erros": -2.0, "bug": -2.0, "bugado": -2.2, "bugada": -2.2,
    "horripilante": -2.6, "inaceitável": -2.6, "inaceitavel": -2.6,
    "enganoso": -2.4, "enganosa": -2.4, "mentiroso": -2.4, "mentirosa": -2.4,
    "não funciona": -2.6, "nao funciona": -2.6, "não funcionou": -2.6, "nao funcionou": -2.6,
    "péssimo atendimento": -2.8, "pessimo atendimento": -2.8,

    # Negativos moderados
    "ruins": -1.8, "chato": -1.5, "chata": -1.5, "triste": -1.6,
    "complicado": -1.5, "complicada": -1.5, "confuso": -1.5, "confusa": -1.5,
    "demasiado caro": -1.8, "caríssimo": -2.0, "carissima": -2.0,

    # Positivos fortes
    "amei": 3.2, "amamos": 3.0, "adoro": 2.8, "adorei": 3.0,
    "ótimo": 3.0, "otimo": 3.0, "ótima": 3.0, "otima": 3.0,
    "excelente": 3.2, "maravilhoso": 3.2, "maravilhosa": 3.2,
    "perfeito": 3.1, "perfeita": 3.1, "impecável": 3.0, "impecavel": 3.0,
    "incrível": 3.0, "incrivel": 3.0, "sensacional": 3.1, "fantástico": 3.1, "fantastico": 3.1,
    "recomendo": 2.6, "recomendei": 2.4, "recomendado": 2.4,
    "satisfeito": 2.4, "satisfeita": 2.4, "surpreendente": 2.6, "surpreendido": 2.4, "surpreendida": 2.4,
    "rápido": 2.2, "rapido": 2.2, "rápida": 2.2, "rapida": 2.2, "agil": 2.0, "ágil": 2.0,
    "barato": 2.0, "barata": 2.0, "bom": 2.0, "boa": 2.0, "ótimos": 2.6, "otimos": 2.6,
    "eficiente": 2.2, "eficaz": 2.2, "funciona": 2.0, "funcionou": 2.0,
    "top": 2.2, "show": 2.0, "maravilha": 2.4,

    # Positivos moderados
    "legal": 1.6, "bacana": 1.6, "agradável": 1.8, "agradavel": 1.8,
    "útil": 1.8, "util": 1.8, "bem feito": 1.8, "bem-feito": 1.8,
}

# Aplica o léxico customizado
analyzer.lexicon.update(custom_pt_lexicon)

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
