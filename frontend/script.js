// frontend/script.js (Versão Melhorada)

document.addEventListener('DOMContentLoaded', () => {

    // --- Mapeamento dos Elementos do HTML ---
    const analyzeButton = document.getElementById('analyze-button');
    const feedbacksTextarea = document.getElementById('feedbacks-textarea');
    const fileInput = document.getElementById('file-input');
    const fileLabel = document.querySelector('.file-label');
    const fileInfo = document.querySelector('.file-info');
    const loadingDiv = document.getElementById('loading');
    const errorDiv = document.getElementById('error');
    const dashboardDiv = document.getElementById('dashboard');

    // Objeto para armazenar as instâncias dos gráficos
    const chartInstances = {};

    // --- Importação de arquivo (TXT/CSV) ---
    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files && e.target.files[0];
        if (!file) {
            fileInfo.textContent = 'TXT ou CSV';
            fileInfo.classList.remove('success');
            fileLabel.classList.remove('imported');
            return;
        }

        try {
            const raw = await file.text();
            let normalized = raw;

            // Se for CSV e não tiver quebras de linha, quebrar por vírgula como fallback
            const lower = file.name.toLowerCase();
            const hasNewlines = /\r?\n/.test(raw);
            if (lower.endsWith('.csv') && !hasNewlines) {
                normalized = raw.split(',').join('\n');
            }

            // Preenche textarea e feedback de UI
            const lines = normalized.split(/\r?\n/).filter(l => l.trim()).length;
            feedbacksTextarea.value = normalized.trim();
            fileInfo.textContent = `Importado: ${file.name} (${lines} linhas)`;
            fileInfo.classList.add('success');
            fileLabel.classList.add('imported');

            // Garante que o usuário veja o conteúdo importado
            errorDiv.classList.add('hidden');
            dashboardDiv.classList.add('hidden');
            feedbacksTextarea.disabled = false;
            analyzeButton.disabled = false;
            feedbacksTextarea.focus();
        } catch (err) {
            console.error('Falha ao importar arquivo:', err);
            fileInfo.textContent = 'Falha ao importar arquivo';
            fileInfo.classList.remove('success');
            fileLabel.classList.remove('imported');
            showError('Não foi possível ler o arquivo. Envie um .txt ou .csv.');
        }
    });

    // --- Registro de Plugins do Chart.js ---
    if (window.Chart && window.ChartDataLabels) {
        Chart.register(window.ChartDataLabels);
    }
    const CenterTextPlugin = {
        id: 'centerText',
        beforeDraw(chart, args, pluginOptions) {
            const { ctx, chartArea } = chart;
            const text = chart.options?.plugins?.centerText?.text;
            if (!text) return;
            const centerX = (chartArea.left + chartArea.right) / 2;
            const centerY = (chartArea.top + chartArea.bottom) / 2;
            ctx.save();
            ctx.fillStyle = '#ffffff';
            ctx.font = '600 20px Inter, Arial, sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(text, centerX, centerY);
            ctx.restore();
        }
    };
    if (window.Chart) { Chart.register(CenterTextPlugin); }

    // --- Event Listener Principal ---
    analyzeButton.addEventListener('click', async () => {
        const text = feedbacksTextarea.value;
        if (!text.trim()) {
            showError("Por favor, insira algum texto para analisar.");
            return;
        }

        showLoading(true);

        try {
            // --- URLs DA API ---
            // Para desenvolvimento local (descomente a linha abaixo):
            // const response = await fetch('http://127.0.0.1:5001/api/index', {
            
            // Para deploy na Vercel (linha ativa):
            const response = await fetch('/api/index', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Erro do servidor: ${response.status}`);
            }

            const data = await response.json();
            updateUI(data);

        } catch (error) {
            showError(`Falha na análise: ${error.message}.`);
        } finally {
            showLoading(false);
        }
    });

    // --- Funções Auxiliares da UI ---
    function showLoading(isLoading) {
        loadingDiv.classList.toggle('hidden', !isLoading);
        errorDiv.classList.add('hidden');
        if (isLoading) {
            dashboardDiv.classList.add('hidden');
        }
        analyzeButton.disabled = isLoading;
        analyzeButton.classList.toggle('loading', isLoading);
        feedbacksTextarea.disabled = isLoading;
    }

    function showError(message) {
        errorDiv.textContent = message;
        errorDiv.classList.remove('hidden');
        dashboardDiv.classList.add('hidden');
    }

    // --- Função Principal para Atualizar a Página ---
    function updateUI(data) {
        dashboardDiv.classList.remove('hidden');

        renderSentimentChart(data);
        renderThemesChart(data.theme_frequency);
        renderWordsChart(data.top_words);

        renderExamples(data.positive_examples, 'positive-examples', 'positive');
        renderExamples(data.negative_examples, 'negative-examples', 'negative');
    }

    function renderExamples(examples, elementId, type) {
        const container = document.getElementById(elementId);
        if (examples.length > 0) {
            container.innerHTML = examples.map(fb =>
                `<div class="example-feedback ${type}">${type === 'positive' ? '✅' : '⚠️'} ${fb}</div>`
            ).join('');
        } else {
            container.innerHTML = `<p>Nenhum exemplo ${type} encontrado.</p>`;
        }
    }

    /**
     * Função genérica para destruir e criar gráficos.
     * Isso previne o bug de renderização e o vazamento de memória.
     */
    function renderChart(chartId, type, data, options) {
        if (chartInstances[chartId]) {
            chartInstances[chartId].destroy();
        }
        const ctx = document.getElementById(chartId).getContext('2d');
        chartInstances[chartId] = new Chart(ctx, { type, data, options });
    }

    // --- Funções Específicas de Renderização dos Gráficos ---

    function renderSentimentChart(data) {
        const sentimentData = data.sentiment_counts;
        const total = sentimentData.positive + sentimentData.negative + sentimentData.neutral;

        // Criar gradientes reais no canvas (Chart.js não aceita strings CSS de gradient)
        const ctx = document.getElementById('sentiment-chart').getContext('2d');
        const gradGreen = ctx.createLinearGradient(0, 0, 0, 240);
        gradGreen.addColorStop(0, '#00d4aa');
        gradGreen.addColorStop(1, '#00b894');
        const gradRed = ctx.createLinearGradient(0, 0, 0, 240);
        gradRed.addColorStop(0, '#ff6b6b');
        gradRed.addColorStop(1, '#ee5a52');
        const gradBlue = ctx.createLinearGradient(0, 0, 0, 240);
        gradBlue.addColorStop(0, '#74b9ff');
        gradBlue.addColorStop(1, '#0984e3');

        renderChart('sentiment-chart', 'doughnut',
            {
                labels: ['Positivos', 'Negativos', 'Neutros'],
                datasets: [{
                    data: [sentimentData.positive, sentimentData.negative, sentimentData.neutral],
                    backgroundColor: [gradGreen, gradRed, gradBlue],
                    borderColor: ['#00b894', '#ee5a52', '#0984e3'],
                    borderWidth: 3,
                    hoverBorderWidth: 4,
                    hoverBorderColor: '#ffffff'
                }]
            },
            {
                responsive: true,
                maintainAspectRatio: false, // ESSENCIAL para a correção do bug
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { 
                            color: '#ffffff', 
                            padding: 20,
                            font: { size: 13, weight: '500' },
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    title: {
                        display: true,
                        text: `${total} Feedbacks Analisados`,
                        position: 'top',
                        align: 'center',
                        font: { size: 16, weight: '600' },
                        color: '#ffffff',
                        padding: { top: 0, bottom: 20 }
                    },
                    centerText: { text: `${total}` },
                    datalabels: {
                        color: '#ffffff',
                        font: { size: 14, weight: 'bold' },
                        formatter: (value, ctx) => {
                            const perc = total ? Math.round((value / total) * 100) : 0;
                            return `${perc}%`;
                        }
                    }
                },
                cutout: '70%'
            }
        );
    }

    function renderThemesChart(themeData) {
        const ctx = document.getElementById('themes-chart').getContext('2d');
        
        // Gradientes vibrantes para cada barra
        const gradients = Object.keys(themeData).map((_, index) => {
            const gradient = ctx.createLinearGradient(0, 0, 400, 0);
            const colors = [
                ['#667eea', '#764ba2'], // Roxo-azul
                ['#f093fb', '#f5576c'], // Rosa-vermelho
                ['#4facfe', '#00f2fe'], // Azul-ciano
                ['#43e97b', '#38f9d7']  // Verde-turquesa
            ];
            const colorPair = colors[index % colors.length];
            gradient.addColorStop(0, colorPair[0]);
            gradient.addColorStop(1, colorPair[1]);
            return gradient;
        });

        renderChart('themes-chart', 'bar',
            {
                labels: Object.keys(themeData),
                datasets: [{
                    label: 'Nº de Menções',
                    data: Object.values(themeData),
                    backgroundColor: gradients,
                    borderColor: gradients,
                    borderWidth: 2,
                    borderRadius: 12,
                    borderSkipped: false
                }]
            },
            {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    datalabels: {
                        color: '#e0e0e0',
                        anchor: 'end',
                        align: 'right',
                        formatter: Math.round
                    }
                },
                scales: {
                    x: { ticks: { color: '#a0a0a0' }, grid: { color: 'rgba(255,255,255,0.1)' } },
                    y: { ticks: { color: '#e0e0e0' }, grid: { display: false } }
                }
            }
        );
    }

    function renderWordsChart(wordData) {
        const ctx = document.getElementById('words-chart').getContext('2d');
        
        // Gradiente verde vibrante
        const gradient = ctx.createLinearGradient(0, 0, 400, 0);
        gradient.addColorStop(0, '#00d4aa');
        gradient.addColorStop(0.5, '#00b894');
        gradient.addColorStop(1, '#00a085');

        renderChart('words-chart', 'bar',
            {
                labels: wordData.map(item => item.word),
                datasets: [{
                    label: 'Frequência',
                    data: wordData.map(item => item.count),
                    backgroundColor: gradient,
                    borderColor: '#00d4aa',
                    borderWidth: 2,
                    borderRadius: 12,
                    borderSkipped: false
                }]
            },
            {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    datalabels: {
                        color: '#e0e0e0',
                        anchor: 'end',
                        align: 'right',
                        formatter: Math.round
                    }
                },
                scales: {
                    x: { ticks: { color: '#a0a0a0' }, grid: { color: 'rgba(255,255,255,0.1)' } },
                    y: { ticks: { color: '#e0e0e0' }, grid: { display: false } }
                }
            }
        );
    }
});
