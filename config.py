"""
Configuration globale du scraper Télérecours
"""

from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class TelecoursConfig:
    """Configuration du scraper"""
    
    # Authentification
    username: Optional[str] = None
    password: Optional[str] = None
    
    # URLs
    base_url: str = "https://www.telerecours.juradm.fr"
    login_url: str = "https://www.telerecours.juradm.fr/AuthentifierUtilisateur/Login.aspx"
    selection_juridiction_url: str = "https://www.telerecours.juradm.fr/AuthentifierUtilisateur/SelectionJuridiction.aspx"
    
    # Dossiers de sortie
    output_dir: Path = Path("./extractions")
    pdfs_dir: Path = Path("./pdfs")
    
    # Options de scraping
    max_messages_par_juridiction: int = 100
    scraper_messages_lus: bool = False  # Par défaut, seulement les non lus
    messages_lus: bool = False  # Si True, scrape les messages lus au lieu des non lus
    verbose: bool = True
    
    # Configuration navigateur
    headless: bool = True
    page_timeout: int = 30000
    
    # Session
    session_id: str = "telerecours_session"
    
    # Webhook
    webhook_url: Optional[str] = None
    
    def __post_init__(self):
        """Créer les dossiers si nécessaire"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.pdfs_dir.mkdir(parents=True, exist_ok=True)
    
    def get_juridiction_dir(self, code_juridiction: str) -> Path:
        """Retourne le dossier pour une juridiction spécifique"""
        juridiction_dir = self.output_dir / code_juridiction
        juridiction_dir.mkdir(parents=True, exist_ok=True)
        return juridiction_dir
    
    def get_pdfs_dir(self, code_juridiction: str) -> Path:
        """Retourne le dossier PDFs pour une juridiction"""
        pdfs_dir = self.pdfs_dir / code_juridiction
        pdfs_dir.mkdir(parents=True, exist_ok=True)
        return pdfs_dir


# Configuration par défaut
DEFAULT_CONFIG = TelecoursConfig()