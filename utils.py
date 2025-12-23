"""
Fonctions utilitaires pour le scraper Télérecours
"""

import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import requests


def save_json(data: dict, filepath: Path):
    """Sauvegarde des données en JSON"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_html(html: str, filepath: Path):
    """Sauvegarde du HTML"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)


def format_timestamp() -> str:
    """Retourne un timestamp formaté"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def print_header(text: str, char: str = "="):
    """Affiche un en-tête formaté"""
    print()
    print(char * 70)
    print(text.center(70))
    print(char * 70)


def print_section(text: str):
    """Affiche une section"""
    print(f"\n{text}")
    print("-" * 70)


def print_summary(
    juridictions_traitees: int,
    total_messages: int,
    total_pdfs: int,
    duration_seconds: float
):
    """Affiche un résumé de l'extraction"""
    
    print_header("📊 RÉSUMÉ DE L'EXTRACTION")
    print(f"Juridictions traitées: {juridictions_traitees}")
    print(f"Messages extraits: {total_messages}")
    print(f"PDFs téléchargés: {total_pdfs}")
    print(f"Durée: {duration_seconds:.1f}s")
    print("=" * 70)


def compte_pdfs_dossier(dossier: Path) -> int:
    """Compte le nombre de PDFs dans un dossier"""
    if not dossier.exists():
        return 0
    return len(list(dossier.glob("*.pdf")))


def taille_dossier_pdfs(dossier: Path) -> float:
    """Retourne la taille totale des PDFs en Mo"""
    if not dossier.exists():
        return 0.0
    
    total = sum(f.stat().st_size for f in dossier.glob("*.pdf"))
    return total / (1024 * 1024)  # Convertir en Mo


def extraire_nom_client(dossier: str) -> str:
    """Extrait le nom du client depuis le champ dossier
    
    Args:
        dossier: Champ dossier (ex: '2501568 - Monsieur DIARRA Bouh / PRÉFET DE POLICE')
    
    Returns:
        str: Nom du client formaté (ex: 'DIARRA-Bouh')
    """
    try:
        # Format: "Numéro - Titre Nom Prénom / Partie adverse"
        if ' - ' in dossier and ' / ' in dossier:
            # Extraire la partie entre " - " et " / "
            partie_client = dossier.split(' - ')[1].split(' / ')[0].strip()
            
            # Retirer les titres courants
            titres = ['Monsieur', 'Madame', 'Mademoiselle', 'M.', 'Mme', 'Mlle']
            for titre in titres:
                partie_client = partie_client.replace(titre, '').strip()
            
            # Remplacer les espaces par des tirets
            nom_client = partie_client.replace(' ', '-')
            
            return nom_client
        
        return "Client-Inconnu"
    except:
        return "Client-Inconnu"


def formater_date_fichier(date_str: str) -> str:
    """Formate la date pour le nom de fichier
    
    Args:
        date_str: Date au format 'DD/MM/YYYY HH:MM' (ex: '10/11/2025 13:21')
    
    Returns:
        str: Date au format 'MM-YYYY' (ex: '11-2025')
    """
    try:
        # Extraire la date (avant l'espace)
        date_part = date_str.split(' ')[0]
        jour, mois, annee = date_part.split('/')
        return f"{mois}-{annee}"
    except:
        return "00-0000"


def generer_nom_fichier_courrier(objet_normalise: str, dossier: str, date: str, nom_fichier_original: str = "") -> str:
    """Génère le nom du fichier pour le courrier envoyé selon les règles métier
    
    Args:
        objet_normalise: Objet normalisé (ex: 'Accusé de réception (AR)')
        dossier: Champ dossier complet
        date: Date du message
        nom_fichier_original: Nom original du fichier PDF (pour certaines catégories)
    
    Returns:
        str: Nom du fichier formaté selon la catégorie
    """
    nom_client = extraire_nom_client(dossier)
    date_formatee = formater_date_fichier(date)
    
    # Extraire le titre initial (sans extension)
    titre_initial = nom_fichier_original.replace('.pdf', '') if nom_fichier_original else "courrier de notification"
    
    # Règles de nomenclature par catégorie
    if objet_normalise == "Accusé de réception (AR)":
        return f"AR_type de démarche_{nom_client}_{date_formatee}.pdf"
    
    elif objet_normalise == "Avis d'audience":
        return f"{titre_initial}_{nom_client}.pdf"
    
    elif objet_normalise == "Mémoire en défense":
        return f"{titre_initial}_{nom_client}.pdf"
    
    elif objet_normalise == "Ordonnance de clôture d'instruction (OCI)":
        return f"{titre_initial}_{nom_client}.pdf"
    
    elif objet_normalise in ["Encombrement du rôle", "Décision", "Demande de régularisation", 
                              "Moyen d'ordre Public", "Dossiers DALO", "Ordonnance de renvoi",
                              "Ordonnance Autre"]:
        return f"{titre_initial}_{nom_client}.pdf"
    
    else:
        # Objet inconnu ou autre
        return f"{titre_initial}_{nom_client}.pdf"


def normaliser_objet(objet: str) -> str:
    """Normalise l'objet d'un message selon les règles métier
    
    Args:
        objet: Objet original du message
    
    Returns:
        str: Objet normalisé
    """
    objet_lower = objet.lower()
    
    # Règle 1: Dossiers DALO
    if objet_lower == "accusé de réception de la requête (dalo)":
        return "Dossiers DALO"
    
    # Règle 2: Accusé de réception (AR)
    ar_patterns = [
        "accusé de réception d'une requête en référé",
        "accusé de réception de la requête",
        "accusé de réception d'une requête",
        "accusé de réception requête et demande de régularisation",
        "exe - accusé réception demande exécution décision",
        "1 - exe - accuse reception demande execution decision"
    ]
    if objet_lower in ar_patterns:
        return "Accusé de réception (AR)"
    
    # Règle 3: Ordonnance de renvoi
    ordonnance_patterns = [
        "notification ordonnance de renvoi"
    ]
    if objet_lower in ordonnance_patterns:
        return "Ordonnance de renvoi"
    
    # Règle 3bis: Ordonnance Autre
    ordonnance_autre_patterns = [
        "notification d'ordonnance",
        "notification d'une ordonnance"
    ]
    if objet_lower in ordonnance_autre_patterns:
        return "Ordonnance Autre"
    
    # Règle 4: Avis d'audience
    audience_patterns = [
        "avis de renvoi à une autre audience",
        "Avis d'audience (requête en référé)",
        "accusé de réception référé et avis d'audience (urgence)",
        "accusé de réception requête en référé et avis d'audience",
        "avis d'audience",
        "avis d'audience (éloignement)"
    ]
    if objet_lower in audience_patterns:
        return "Avis d'audience"
    
    # Règle 5: Mémoire en défense
    memoire_patterns = [
        "communication d'un mémoire et invitation à se désister (dnl)",
        "communication de pièces et invitation à se désister (dnl)",
        "communication d'un mémoire en défense (référé)",
        "communication d'un mémoire en défense",
        "communication d'un mémoire"
    ]
    if objet_lower in memoire_patterns:
        return "Mémoire en défense"
    
    # Règle 6: Ordonnance de clôture d'instruction (OCI)
    oci_patterns = [
        "notification d'ordonnance d'instruction",
        "notification d'ordonnance de clôture d'instruction",
        "notification d'ordonnance de report de cloture d'instruction",
        "notification ordonnance de ci (dès l'enregistrement)"
    ]
    if objet_lower in oci_patterns:
        return "Ordonnance de clôture d'instruction (OCI)"
    
    # Règle 7: Moyen d'ordre Public
    mop_patterns = [
        "communication réponse à un(des) moyen(s) d'ordre public",
        "communication moyen(s) d'ordre public"
    ]
    if objet_lower in mop_patterns:
        return "Moyen d'ordre Public"
    
    # Règle 8: Décision
    decision_patterns = [
        "notification d'une ordonnance de référé",
        "notification de jugement",
        "Notification ordonnance L. 522-3 rejet référé d’urgence"
    ]
    if objet_lower in decision_patterns:
        return "Décision"
    
    # Règle 9: Encombrement du rôle
    encombrement_patterns = [
        "encombrement du rôle",
        "enrôlement vraisemblable d'une affaire"
    ]
    if objet_lower in encombrement_patterns:
        return "Encombrement du rôle"
    
    # Règle 10: Demande de régularisation
    regularisation_patterns = [
        "notification d'un arrêt",
        "demande de régularisation (après ar de la requête)",
        "communication de pièces complémentaires",
        "demande de maintien de la requête",
        "communication pour production de la réplique",
        "exe - classement",
        "lettre du greffier",
        "demande de pièces pour complèter l'instruction",
        "lettre de demande de désistement explicite",
        "lettre d'information r.611-11-1 cja"
    ]
    if objet_lower in regularisation_patterns:
        return "Demande de régularisation"
    
    # Si aucune règle ne correspond, retourner "Objet inconnu"
    return "Objet inconnu"


def send_webhook(webhook_url: str, data: dict) -> bool:
    """Envoie les données JSON vers un webhook
    
    Args:
        webhook_url: URL du webhook
        data: Données à envoyer (dict ou list)
    
    Returns:
        bool: True si succès, False sinon
    """
    try:
        response = requests.post(
            webhook_url,
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code in [200, 201, 202, 204]:
            print(f"\n✅ Webhook envoyé avec succès ({response.status_code})")
            return True
        else:
            print(f"\n⚠️  Webhook erreur: {response.status_code} - {response.text[:100]}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n❌ Webhook timeout (>30s)")
        return False
    except Exception as e:
        print(f"\n❌ Erreur webhook: {str(e)}")
        return False