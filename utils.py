"""
Fonctions utilitaires pour le scraper Télérecours
"""

import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime


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