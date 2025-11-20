# 🚂 Déploiement sur Railway - Guide Complet

## 📋 Prérequis
- Compte Railway (gratuit pour commencer)
- Repo Git (GitHub, GitLab, ou Bitbucket)

---

## 🚀 Étape 1 : Préparer le code

Tout est déjà prêt ! Les fichiers suivants sont configurés :
- ✅ `Dockerfile` - Image Playwright optimisée
- ✅ `railway.json` - Configuration Railway
- ✅ `.dockerignore` - Optimisation du build

---

## 🔧 Étape 2 : Créer le projet Railway

### Option A : Via l'interface web (RECOMMANDÉ)

1. **Aller sur [railway.app](https://railway.app)**

2. **Créer un nouveau projet**
   - Cliquer sur "New Project"
   - Choisir "Deploy from GitHub repo"
   - Sélectionner ton repo

3. **Railway détectera automatiquement le Dockerfile**

### Option B : Via CLI

```bash
# Installer Railway CLI
npm install -g @railway/cli

# Login
railway login

# Créer et lier le projet
railway init
railway link
```

---

## 🔐 Étape 3 : Configurer les variables d'environnement

Dans le dashboard Railway, aller dans **Variables** et ajouter :

```bash
TELERECOURS_USERNAME=ton_identifiant
TELERECOURS_PASSWORD=ton_mot_de_passe
```

**Important :** Ne jamais commiter ces identifiants dans le code !

---

## ⏰ Étape 4 : Configurer le Cron Job

Railway ne supporte pas directement les cron jobs dans le même service. Il faut créer un **service séparé** :

### Méthode 1 : Utiliser Railway Cron (RECOMMANDÉ)

1. **Dans ton projet Railway, ajouter un nouveau service**
   - Cliquer sur "+ New"
   - Choisir "Empty Service"
   - Nommer : "Scraper Cron"

2. **Configurer le service**
   - Aller dans **Settings** > **Service**
   - **Start Command** :
     ```bash
     python main.py --juridiction TA93 --messages-lus --webhook https://primary-production-94c2e.up.railway.app/webhook-test/467a3692-94de-45bc-a532-cf9feb8ad5e4
     ```
   - **Cron Schedule** : `0 8,14,20 * * *` (3 fois/jour : 8h, 14h, 20h UTC)

3. **Partager les variables d'environnement**
   - Dans Variables, référencer les mêmes variables du service principal

### Méthode 2 : Utiliser un service externe (Alternative)

Si Railway Cron ne fonctionne pas, utiliser **cron-job.org** (gratuit) :

1. Créer un compte sur [cron-job.org](https://cron-job.org)
2. Créer un nouveau cron job qui appelle un endpoint Railway
3. Créer un endpoint dans ton app qui lance le scraper

---

## 🏗️ Étape 5 : Déployer

### Via l'interface web
Railway déploie automatiquement à chaque push sur la branche principale.

### Via CLI
```bash
railway up
```

---

## 📊 Étape 6 : Vérifier le déploiement

1. **Voir les logs**
   ```bash
   railway logs
   ```
   Ou dans le dashboard : **Deployments** > **View Logs**

2. **Tester manuellement**
   Dans le dashboard, aller dans **Settings** et cliquer sur "Trigger Deploy"

---

## 🔍 Configuration optimale Railway

### Variables d'environnement recommandées

```bash
# Identifiants (REQUIS)
TELERECOURS_USERNAME=ton_identifiant
TELERECOURS_PASSWORD=ton_mot_de_passe

# Configuration Playwright (optionnel, déjà dans Dockerfile)
PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
PLAYWRIGHT_CHROMIUM_ARGS=--no-sandbox --disable-setuid-sandbox

# Webhook (optionnel si passé en argument)
WEBHOOK_URL=https://primary-production-94c2e.up.railway.app/webhook-test/467a3692-94de-45bc-a532-cf9feb8ad5e4
```

### Ressources recommandées

Pour un scraper qui tourne 3x/jour :
- **RAM** : 1 GB minimum (2 GB recommandé)
- **CPU** : 1 vCPU suffit
- **Région** : Choisir la plus proche (Europe West pour la France)

---

## 💰 Estimation des coûts

Railway facture à l'usage :
- **Build time** : ~2-3 min par déploiement
- **Runtime** : ~5-10 min par exécution
- **Total/mois** : ~90 min d'exécution (3x/jour × 30 jours × 1 min)

**Coût estimé : 5-10$/mois** (selon les ressources)

---

## 🐛 Troubleshooting

### Erreur : "Chromium executable not found"
**Solution :** Vérifier que le Dockerfile utilise bien l'image Playwright :
```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.48.0-noble
```

### Erreur : "Worker timeout" ou "Out of memory"
**Solution :** Augmenter la RAM dans Railway Settings > Resources

### Erreur : "Permission denied" pour Chromium
**Solution :** Déjà géré dans le Dockerfile avec :
```bash
ENV PLAYWRIGHT_CHROMIUM_ARGS="--no-sandbox --disable-setuid-sandbox"
```

### Le cron ne se lance pas
**Solution :** Vérifier le format du cron schedule :
- `0 8,14,20 * * *` = 8h, 14h, 20h UTC (9h, 15h, 21h Paris)
- Utiliser [crontab.guru](https://crontab.guru) pour vérifier

---

## 📝 Commandes utiles

```bash
# Voir les logs en temps réel
railway logs --follow

# Redéployer
railway up

# Voir les variables
railway variables

# Ajouter une variable
railway variables set KEY=value

# Ouvrir le dashboard
railway open
```

---

## ✅ Checklist finale

- [ ] Code pushé sur GitHub/GitLab
- [ ] Projet créé sur Railway
- [ ] Variables d'environnement configurées
- [ ] Cron job configuré (3x/jour)
- [ ] Premier déploiement réussi
- [ ] Logs vérifiés
- [ ] Webhook testé

---

## 🎯 Commande finale du Cron

```bash
python main.py --juridiction TA93 --messages-lus --webhook https://primary-production-94c2e.up.railway.app/webhook-test/467a3692-94de-45bc-a532-cf9feb8ad5e4
```

**Schedule cron :** `0 8,14,20 * * *`

---

## 📞 Support

- [Documentation Railway](https://docs.railway.app)
- [Discord Railway](https://discord.gg/railway)
- [Status Railway](https://status.railway.app)
