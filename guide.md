# 🚀 Guide de Démarrage Rapide

## Installation

```bash
cd telerecours_scraper
pip install -r requirements.txt
```

## Utilisation Immédiate

### 1. Mode Automatique (Recommandé)

```bash
python main.py --auto
```

**Ce qui se passe** :
1. Demande vos identifiants
2. Se connecte automatiquement
3. Détecte toutes les juridictions avec notifications
4. Affiche un résumé
5. Demande confirmation
6. Extrait automatiquement tous les messages non lus
7. Télécharge tous les PDFs

**Résultat** :
```
📬 3 juridiction(s) avec notifications :
══════════════════════════════════════════════════════════════════════
   📍 TA75 - Paris                         :   5 message(s)
   📍 TA78 - Versailles                    :   2 message(s)
   📍 CA02 - Cour Administrative Douai     :   1 message(s)
══════════════════════════════════════════════════════════════════════
   TOTAL: 8 message(s) non lu(s)

❓ Extraire les messages de ces 3 juridictions ? (o/N) : o
```

### 2. Mode Interactif

```bash
python main.py
```

Menu :
- **Option 1** : Extraire toutes les juridictions
- **Option 2** : Choisir une juridiction spécifique
- **Option 0** : Quitter

### 3. Mode Juridiction Spécifique

```bash
python main.py --juridiction TA75
```

Extrait uniquement la juridiction demandée.

## Options Avancées

```bash
# Voir le navigateur en action
python main.py --auto --no-headless

# Limiter à 10 messages par juridiction
python main.py --auto --max-messages 10

# Aide
python main.py --help
```

## Résultats

Après extraction, vous trouverez :

```
./extractions/TA75/
├── messages_TA75.json          # Métadonnées de tous les messages
├── message_3217390.html        # Message 1 (HTML complet)
└── message_3216464.html        # Message 2

./pdfs/TA75/
├── 3217390_document1.pdf       # PDF du message 1
├── 3217390_document2.pdf
└── 3216464_rapport.pdf         # PDF du message 2
```

## Exemple d'Utilisation Quotidienne

Créer un script `check_notifications.sh` :

```bash
#!/bin/bash
cd /path/to/telerecours_scraper
python main.py --auto
```

Cron job (tous les jours à 9h) :
```bash
0 9 * * * /path/to/check_notifications.sh
```

## Troubleshooting

### Erreur "Module not found"
```bash
pip install -r requirements.txt
```

### Timeout
Augmenter le timeout dans `config.py` :
```python
page_timeout: int = 60000  # 60 secondes
```

### Aucune notification trouvée
C'est normal si vous n'avez pas de messages non lus !

## Architecture Simplifiée

```
┌─────────────┐
│   main.py   │ ← Point d'entrée
└──────┬──────┘
       │
       ├──► auth.py          (Connexion)
       ├──► notifs.py        (Détection notifs)
       └──► scraper_messages.py (Extraction + PDFs)
```

## Prochaines Étapes

1. ✅ Tester avec `python main.py --auto`
2. 📖 Lire `README.md` pour plus de détails
3. 🎓 Explorer `exemple_utilisation.py` pour usage avancé
4. ⚙️ Personnaliser `config.py` selon vos besoins

## Support

Pour toute question, consulter :
- `README.md` : Documentation complète
- `exemple_utilisation.py` : 4 exemples d'usage avancé
- Code source : Commenté et documenté ! :D

Bonne extraction ! 🎉