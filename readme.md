# 🚀 Scraper Télérecours Modulaire

Extraction automatique des messages Télérecours avec **détection intelligente des notifications**.

## ✨ Fonctionnalités

- ✅ **Détection automatique** des juridictions avec notifications
- ✅ **Extraction optimisée** des messages non lus (priorité)
- ✅ **Téléchargement automatique** des PDFs
- ✅ **Architecture modulaire** et maintenable
- ✅ **3 modes d'utilisation** : automatique, interactif, juridiction spécifique
- ✅ **Organisation par juridiction** des résultats

## 📁 Structure du Projet

```
telerecours_scraper/
├── config.py              # Configuration globale
├── auth.py                # Authentification et session
├── notifs.py              # Détection des notifications
├── scraper_messages.py    # Scraping des messages et PDFs
├── utils.py               # Fonctions utilitaires
├── main.py                # Script principal
└── README.md              # Ce fichier
```

## 🎯 Modes d'Utilisation

### 1. Mode Automatique (Recommandé)

Extrait automatiquement **toutes** les juridictions avec notifications :

```bash
python main.py --auto
```

**Workflow** :
1. Connexion automatique
2. Détection des juridictions avec notifs
3. Affichage du résumé
4. Demande de confirmation
5. Extraction automatique de toutes les juridictions

### 2. Mode Interactif

Menu interactif pour choisir :

```bash
python main.py
```

**Options** :
- Extraire toutes les juridictions
- Choisir une juridiction spécifique
- Quitter

### 3. Mode Juridiction Spécifique

Extraction d'une seule juridiction :

```bash
python main.py --juridiction TA78
```

## 🔧 Options Avancées

```bash
# Mode non-headless (voir le navigateur)
python main.py --auto --no-headless

# Limiter le nombre de messages par juridiction
python main.py --auto --max-messages 50
```

## 📊 Résultats

### Structure des Dossiers

```
./extractions/           # Résultats par juridiction
├── TA75/
│   ├── messages_TA75.json        # Tous les messages (métadonnées)
│   ├── message_3217390.html      # Message individuel
│   └── message_3216464.html
├── TA78/
│   └── ...

./pdfs/                  # PDFs par juridiction
├── TA75/
│   ├── 3217390_document.pdf
│   └── 3216464_rapport.pdf
├── TA78/
│   └── ...
```

### Format JSON des Messages

```json
[
  {
    "index": 1,
    "msg_id": "3217390",
    "msg_type": "1",
    "statut": "non_lu",
    "expediteur": "Corinne DELANNOY",
    "dossier": "2401234",
    "objet": "Communication de la procédure",
    "rapporteur": "M. DUPONT",
    "date": "03/11/2025 16:28",
    "fichiers_telecharges": [
      {
        "type": "href_direct",
        "nom_original": "document.pdf",
        "chemin": "./pdfs/TA75/3217390_document.pdf"
      }
    ]
  }
]
```

## 🎓 Exemples d'Utilisation

### Exemple 1 : Extraction Automatique Quotidienne

```bash
# Cron job : tous les jours à 9h
0 9 * * * cd /path/to/scraper && python main.py --auto
```

### Exemple 2 : Extraction Ciblée

```bash
# Extraire uniquement Paris (TA75)
python main.py --juridiction TA75
```

### Exemple 3 : Script Personnalisé

```python
import asyncio
from config import TelecoursConfig
from auth import TelecoursAuth
from notifs import NotificationDetector
from crawl4ai import AsyncWebCrawler, BrowserConfig

async def mon_script():
    config = TelecoursConfig(
        username="mon_id",
        password="mon_pass"
    )
    
    browser_config = BrowserConfig(headless=True)
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Authentification
        auth = TelecoursAuth(config)
        await auth.setup_cookie_hook(crawler)
        await auth.login(crawler)
        
        # Détecter les notifs
        detector = NotificationDetector(config)
        juridictions = await detector.get_juridictions_avec_notifs(crawler)
        
        # Afficher
        for j in juridictions:
            print(f"{j.code}: {j.nb_notifs} notification(s)")

asyncio.run(mon_script())
```

## 🔍 Détails Techniques

### Détection des Notifications

Le module `notifs.py` parse le HTML de la page de sélection :

```html
<li name="TA75">
  <a href="javascript:__doPostBack('ctl00$cphBody$lstTA2','3')">
    Paris
    <span class="page-choixJuridiction-mail">
      <span>2</span>
    </span>
  </a>
</li>
```

Extraction :
- Code : `TA75`
- Nom : `Paris`
- Notifications : `2`
- PostBack : `ctl00$cphBody$lstTA2`, `3`

### Téléchargement des PDFs

Utilise la méthode `fetch()` + `Blob` (testée et fonctionnelle) :

```javascript
const response = await fetch(pdf_url);
const blob = await response.blob();
const url = window.URL.createObjectURL(blob);
const a = document.createElement('a');
a.download = filename;
a.href = url;
a.click();
```

### Gestion de Session

- Session Playwright persistante via `session_id`
- Cookies capturés via hook `after_goto`
- Réutilisation de la session pour toutes les juridictions

## ⚙️ Configuration

Modifier `config.py` pour personnaliser :

```python
@dataclass
class TelecoursConfig:
    # Dossiers
    output_dir: Path = Path("./mes_extractions")
    pdfs_dir: Path = Path("./mes_pdfs")
    
    # Options
    max_messages_par_juridiction: int = 200
    scraper_messages_lus: bool = False  # Seulement non lus
    
    # Navigateur
    headless: bool = True
    page_timeout: int = 60000  # 60 secondes
```

## 🐛 Dépannage

### Erreur de connexion
```bash
❌ Erreur connexion: ...
```
→ Vérifier identifiants

### Aucune notification trouvée
```bash
📭 Aucune notification trouvée
```
→ Normal si aucun message non lu

### Timeout
```bash
❌ Erreur: Timeout
```
→ Augmenter `page_timeout` dans `config.py`

## 📈 Performance

- **Juridiction unique** : ~30s - 2 min (selon nb de messages)
- **Mode automatique (5 juridictions)** : ~5-10 min
- **Téléchargement PDF** : ~2-3s par fichier

## 🎯 Avantages de l'Architecture Modulaire

| Aspect | Avant (Monolithique) | Après (Modulaire) |
|--------|---------------------|-------------------|
| Maintenabilité | ❌ Code difficile à modifier | ✅ Modules indépendants |
| Réutilisabilité | ❌ Copier-coller du code | ✅ Import de modules |
| Testabilité | ❌ Difficile à tester | ✅ Tests par module |
| Lisibilité | ❌ 500+ lignes | ✅ ~100 lignes/module |
| Extensibilité | ❌ Modifications risquées | ✅ Ajout de fonctionnalités facile |

## 🚀 Évolutions Futures

- [ ] Interface web (Flask/Django)
- [ ] API REST
- [ ] Notifications par email/Slack
- [ ] Dashboard de statistiques
- [ ] Export Excel/CSV
- [ ] Filtres avancés (date, expéditeur, etc.)

## 📝 Licence

Code basé sur le scraper original fonctionnel, optimisé et modularisé.

## 🙏 Crédits

Architecture modulaire créée pour améliorer la maintenabilité et l'extensibilité du scraper Télérecours.