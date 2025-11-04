"""
Module de détection des notifications par juridiction
"""

import re
from typing import List, Dict
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

from config import TelecoursConfig


class JuridictionNotification:
    """Représente une juridiction avec ses notifications"""
    
    def __init__(self, code: str, nom: str, nb_notifs: int, event_target: str, event_argument: str):
        self.code = code
        self.nom = nom
        self.nb_notifs = nb_notifs
        self.event_target = event_target
        self.event_argument = event_argument
    
    def __repr__(self):
        return f"<Juridiction {self.code} ({self.nom}): {self.nb_notifs} notification(s)>"


class NotificationDetector:
    """Détecte les juridictions avec des notifications"""
    
    def __init__(self, config: TelecoursConfig):
        self.config = config
    
    async def get_juridictions_avec_notifs(
        self, 
        crawler: AsyncWebCrawler,
        html_selection: str = None
    ) -> List[JuridictionNotification]:
        """
        Extrait les juridictions avec notifications depuis la page de sélection
        
        Args:
            crawler: Instance du crawler
            html_selection: HTML de la page de sélection (optionnel)
        
        Returns:
            List[JuridictionNotification]: Liste des juridictions avec notifs
        """
        
        # Si pas d'HTML fourni, on récupère la page
        if not html_selection:
            print("🔍 Récupération de la page de sélection des juridictions...")
            config = CrawlerRunConfig(
                session_id=self.config.session_id,
                page_timeout=self.config.page_timeout,
                cache_mode=0,
                verbose=False
            )
            
            result = await crawler.arun(
                url=self.config.selection_juridiction_url,
                config=config
            )
            
            if not result.success:
                print(f"❌ Erreur: {result.error_message}")
                return []
            
            html_selection = result.html
        
        # Parser le HTML
        soup = BeautifulSoup(html_selection, 'html.parser')
        
        # Trouver toutes les juridictions avec notifications
        # Structure : <li name="TA75"><a href="...">Paris<span class="page-choixJuridiction-mail"><span>2</span></span></a></li>
        juridictions_avec_notifs = []
        
        # Chercher tous les <li> avec attribut name
        for li in soup.find_all('li', attrs={'name': True}):
            code_juridiction = li.get('name')
            
            # Trouver le lien
            link = li.find('a')
            if not link:
                continue
            
            # Extraire le nom de la juridiction (texte avant le span)
            nom_juridiction = link.get_text(strip=True)
            
            # Chercher le span avec les notifications
            span_notif = link.find('span', class_='page-choixJuridiction-mail')
            
            if span_notif:
                # Récupérer le nombre de notifications
                span_nombre = span_notif.find('span')
                nb_notifs = int(span_nombre.get_text(strip=True)) if span_nombre else 0
                
                # Le nom est avant le span de notification
                nom_parts = []
                for content in link.contents:
                    if isinstance(content, str):
                        nom_parts.append(content.strip())
                    elif content.name == 'span':
                        break
                nom_juridiction = ''.join(nom_parts).strip()
            else:
                # Pas de notification
                nb_notifs = 0
            
            # Extraire les paramètres du PostBack
            href = link.get('href', '')
            match = re.search(r"__doPostBack\('([^']+)','([^']+)'\)", href)
            
            if match:
                event_target = match.group(1)
                event_argument = match.group(2)
                
                # Créer l'objet juridiction
                juridiction = JuridictionNotification(
                    code=code_juridiction,
                    nom=nom_juridiction,
                    nb_notifs=nb_notifs,
                    event_target=event_target,
                    event_argument=event_argument
                )
                
                # Ajouter uniquement si notifications > 0
                if nb_notifs > 0:
                    juridictions_avec_notifs.append(juridiction)
        
        return juridictions_avec_notifs
    
    async def afficher_juridictions_avec_notifs(
        self, 
        juridictions: List[JuridictionNotification]
    ):
        """Affiche un résumé des juridictions avec notifications"""
        
        if not juridictions:
            print("\n📭 Aucune notification trouvée")
            return
        
        print(f"\n📬 {len(juridictions)} juridiction(s) avec notifications :")
        print("=" * 70)
        
        total_notifs = sum(j.nb_notifs for j in juridictions)
        
        for juridiction in sorted(juridictions, key=lambda x: x.nb_notifs, reverse=True):
            print(f"   📍 {juridiction.code} - {juridiction.nom:<30} : {juridiction.nb_notifs:>3} message(s)")
        
        print("=" * 70)
        print(f"   TOTAL: {total_notifs} message(s) non lu(s)")
        print()
    
    async def selectionner_juridiction(
        self,
        crawler: AsyncWebCrawler,
        juridiction: JuridictionNotification
    ) -> bool:
        """
        Sélectionne une juridiction
        
        Args:
            crawler: Instance du crawler
            juridiction: Juridiction à sélectionner
        
        Returns:
            bool: True si sélection réussie
        """
        
        if self.config.verbose:
            print(f"📋 Sélection de {juridiction.code} ({juridiction.nom})...")
        
        js_juridiction = f"__doPostBack('{juridiction.event_target}', '{juridiction.event_argument}');"
        
        config_juridiction = CrawlerRunConfig(
            session_id=self.config.session_id,
            js_code=js_juridiction,
            js_only=True,
            wait_for="css:body",
            page_timeout=self.config.page_timeout,
            cache_mode=0,
            verbose=False
        )
        
        result = await crawler.arun(
            url=self.config.selection_juridiction_url,
            config=config_juridiction
        )
        
        if not result.success:
            print(f"❌ Erreur sélection {juridiction.code}: {result.error_message}")
            return False
        
        if self.config.verbose:
            print(f"   ✅ {juridiction.code} sélectionné")
        
        return True