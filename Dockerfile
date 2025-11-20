# Utiliser l'image officielle Playwright avec Python
FROM mcr.microsoft.com/playwright/python:v1.48.0-noble

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python (crawl4ai installera la version de Playwright dont il a besoin)
RUN pip install --no-cache-dir -r requirements.txt

# Installer les navigateurs Playwright pour la version installée par crawl4ai
RUN playwright install chromium
RUN playwright install-deps chromium

# Copier le code source
COPY . .

# Créer les dossiers nécessaires
RUN mkdir -p extractions pdfs

# Configuration recommandée pour Playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Désactiver le mode headless pour éviter les problèmes de sandbox
# Railway utilise --ipc=host automatiquement
ENV PLAYWRIGHT_CHROMIUM_ARGS="--no-sandbox --disable-setuid-sandbox"

# Commande par défaut
CMD ["python", "main.py", "--juridiction", "TA93", "--messages-lus", "--max-messages", "2", "--webhook", "https://primary-production-94c2e.up.railway.app/webhook-test/467a3692-94de-45bc-a532-cf9feb8ad5e4"]
