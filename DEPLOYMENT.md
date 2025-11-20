# Guide de Déploiement

## Option 1 : GitHub Actions (RECOMMANDÉ - GRATUIT)

### Avantages
- ✅ **Gratuit** pour repos publics (2000 min/mois pour privés)
- ✅ Pas de serveur à maintenir
- ✅ Playwright pré-installé
- ✅ Cron natif
- ✅ Logs et monitoring intégrés

### Configuration

1. **Créer un repo GitHub et pusher le code**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <votre-repo>
   git push -u origin main
   ```

2. **Ajouter les secrets dans GitHub**
   - Aller dans `Settings` > `Secrets and variables` > `Actions`
   - Ajouter :
     - `TELERECOURS_USERNAME` : votre identifiant Télérecours
     - `TELERECOURS_PASSWORD` : votre mot de passe Télérecours

3. **Le workflow se lance automatiquement**
   - 3 fois par jour : 9h, 15h, 21h (heure de Paris)
   - Ou manuellement via l'onglet "Actions"

### Modifier le planning
Éditer `.github/workflows/scraper.yml` et changer les cron :
```yaml
schedule:
  - cron: '0 8 * * *'   # 9h Paris
  - cron: '0 14 * * *'  # 15h Paris
  - cron: '0 20 * * *'  # 21h Paris
```

---

## Option 2 : Railway (PAYANT ~5-10$/mois)

### Avantages
- ✅ Supporte Docker + Playwright
- ✅ Cron jobs natifs
- ✅ Interface simple

### Configuration

1. **Installer Railway CLI**
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. **Créer un nouveau projet**
   ```bash
   railway init
   railway link
   ```

3. **Ajouter les variables d'environnement**
   ```bash
   railway variables set TELERECOURS_USERNAME="votre_username"
   railway variables set TELERECOURS_PASSWORD="votre_password"
   ```

4. **Déployer**
   ```bash
   railway up
   ```

5. **Configurer le Cron Job**
   - Aller dans le dashboard Railway
   - Créer un "Cron Job" service
   - Commande : 
     ```bash
     python main.py --juridiction TA93 --messages-lus --webhook https://primary-production-94c2e.up.railway.app/webhook-test/467a3692-94de-45bc-a532-cf9feb8ad5e4
     ```
   - Schedule : `0 8,14,20 * * *` (3 fois par jour)

### Configuration Docker pour Railway
Le `Dockerfile` utilise l'image officielle Microsoft Playwright avec :
- Python 3.11
- Chromium pré-installé
- Configuration optimale pour scraping

---

## Option 3 : Render (GRATUIT puis payant)

### Configuration

1. **Créer un compte sur Render.com**

2. **Créer un nouveau "Cron Job"**
   - Type : Docker
   - Repository : votre repo GitHub
   - Dockerfile path : `Dockerfile`

3. **Ajouter les variables d'environnement**
   - `TELERECOURS_USERNAME`
   - `TELERECOURS_PASSWORD`

4. **Configurer le schedule**
   - Schedule : `0 8,14,20 * * *`
   - Commande : 
     ```bash
     python main.py --juridiction TA93 --messages-lus --webhook https://primary-production-94c2e.up.railway.app/webhook-test/467a3692-94de-45bc-a532-cf9feb8ad5e4
     ```

---

## Comparaison des plateformes

| Plateforme | Prix | Complexité | Playwright | Cron natif | Recommandation |
|------------|------|------------|------------|------------|----------------|
| **GitHub Actions** | Gratuit | ⭐⭐ | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| **Railway** | ~5-10$/mois | ⭐⭐⭐ | ✅ | ✅ | ⭐⭐⭐ |
| **Render** | Gratuit puis payant | ⭐⭐ | ✅ | ✅ | ⭐⭐⭐⭐ |
| **Fly.io** | ~3-5$/mois | ⭐⭐⭐⭐ | ✅ | ❌ | ⭐⭐ |

---

## Tester localement avec Docker

```bash
# Build l'image
docker build -t telerecours-scraper .

# Tester
docker run -it --rm --ipc=host \
  -e TELERECOURS_USERNAME="votre_username" \
  -e TELERECOURS_PASSWORD="votre_password" \
  telerecours-scraper \
  python main.py --juridiction TA93 --messages-lus --webhook https://primary-production-94c2e.up.railway.app/webhook-test/467a3692-94de-45bc-a532-cf9feb8ad5e4
```

---

## Monitoring et Logs

### GitHub Actions
- Onglet "Actions" dans votre repo
- Logs détaillés de chaque exécution
- Notifications par email en cas d'échec

### Railway
- Dashboard Railway > Logs
- Métriques de performance
- Alertes configurables

### Render
- Dashboard Render > Logs
- Historique des exécutions
- Notifications par email
