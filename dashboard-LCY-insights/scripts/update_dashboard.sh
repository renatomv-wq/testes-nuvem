#!/bin/bash

# Script para atualizar o dashboard com novos dados
# Uso: ./update_dashboard.sh

echo "🔄 Atualizando Dashboard de Webinars..."
echo ""

# Verificar se o Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado. Por favor, instale o Python3."
    exit 1
fi

# Verificar se o pandas está instalado
if ! python3 -c "import pandas" &> /dev/null; then
    echo "📦 Instalando pandas..."
    pip3 install pandas
fi

# Executar o script de geração
echo "📊 Gerando dashboard..."
python3 generate_dashboard.py

# Copiar para a raiz do projeto
if [ -f "/Users/renatovieira/Downloads/dashboard_webinar_insights_v2.html" ]; then
    cp /Users/renatovieira/Downloads/dashboard_webinar_insights_v2.html ../index.html
    echo ""
    echo "✅ Dashboard atualizado com sucesso!"
    echo "📁 Arquivo: ../index.html"
    echo ""
    echo "Próximos passos:"
    echo "  1. git add ."
    echo "  2. git commit -m 'Atualização dos dados do dashboard'"
    echo "  3. git push"
    echo ""
    echo "O Vercel fará o redeploy automaticamente."
else
    echo "❌ Erro ao gerar o dashboard. Verifique os arquivos de entrada."
    exit 1
fi
