"""
Module de scraping des messages (non lus + lus)
Basé sur le code original fonctionnel
"""

import asyncio
from pathlib import Path
from typing import List, Dict
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
import re

from config import TelecoursConfig
from utils import save_json, save_html, compte_pdfs_dossier, taille_dossier_pdfs


class MessageScraper:
    """Scraper de messages Télérecours"""
    
    def __init__(self, config: TelecoursConfig, cookies: Dict[str, str]):
        self.config = config
        self.cookies = cookies
    
    async def extraire_liens_pdf(self, html: str) -> Dict:
        """Extrait tous les liens PDF d'une page HTML"""
        
        soup = BeautifulSoup(html, 'html.parser')
        
        resultats = {
            'hrefs_directs': [],
            'onclick': []
        }
        
        # 1. PDFs avec href direct
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            
            if href and '.pdf' in href.lower():
                nom_fichier = href.split('/')[-1]
                
                resultats['hrefs_directs'].append({
                    'id': link.get('id', ''),
                    'nom': nom_fichier,
                    'href': href,
                    'class': ' '.join(link.get('class', [])),
                    'text': link.get_text(strip=True)
                })
        
        # 2. PDFs avec classe hplGenFichier (accusés)
        for link in soup.find_all('a', class_='hplGenFichier'):
            link_id = link.get('id', '')
            link_text = link.get_text(strip=True)
            
            if 'accusé' in link_text.lower() or 'pdf' in link_text.lower():
                resultats['onclick'].append({
                    'id': link_id,
                    'text': link_text,
                    'nom_suggeré': f"{link_text.replace(' ', '_')}.pdf"
                })
        
        return resultats
    
    async def telecharger_pdfs_message(
        self, 
        crawler: AsyncWebCrawler,
        html_message: str,
        msg_id: str,
        dossier: str,
        url_actuelle: str
    ) -> List[Dict]:
        """Télécharge tous les PDFs d'un message"""
        
        pdfs = await self.extraire_liens_pdf(html_message)
        
        nb_total = len(pdfs['hrefs_directs']) + len(pdfs['onclick'])
        
        if nb_total == 0:
            return []
        
        print(f"      {nb_total} PDF(s) trouvé(s)")
        
        fichiers_telecharges = []
        
        # Télécharger les PDFs avec href direct
        if pdfs['hrefs_directs']:
            print(f"      Téléchargement de {len(pdfs['hrefs_directs'])} PDF(s)...")
            
            for pdf_info in pdfs['hrefs_directs']:
                href = pdf_info['href']
                if href.startswith('/'):
                    pdf_url = f"https://www.telerecours.juradm.fr{href}"
                else:
                    pdf_url = href
                
                nom_fichier = f"{msg_id}_{pdf_info['nom']}"
                
                # JavaScript fetch + blob (méthode originale qui fonctionne)
                js_download = f"""
                (async () => {{
                    try {{
                        const response = await fetch('{pdf_url}');
                        if (!response.ok) return;
                        
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.style.display = 'none';
                        a.href = url;
                        a.download = '{pdf_info['nom']}';
                        
                        document.body.appendChild(a);
                        a.click();
                        
                        await new Promise(resolve => setTimeout(resolve, 1000));
                        
                        window.URL.revokeObjectURL(url);
                        document.body.removeChild(a);
                    }} catch (error) {{
                        console.error('Erreur téléchargement:', error);
                    }}
                }})();
                """
                
                config_download = CrawlerRunConfig(
                    session_id=self.config.session_id,
                    js_code=js_download,
                    js_only=True,
                    page_timeout=15000,
                    cache_mode=0,
                    verbose=False
                )
                
                try:
                    await crawler.arun(url=url_actuelle, config=config_download)
                    await asyncio.sleep(3)
                    
                    # Les PDFs sont téléchargés dans le dossier racine pdfs/
                    # Il faut les chercher là et les déplacer vers pdfs/TA78/
                    dossier_racine = Path(dossier).parent  # pdfs/ au lieu de pdfs/TA78/
                    chemin_racine = dossier_racine / pdf_info['nom']
                    chemin_final = Path(dossier) / nom_fichier
                    
                    # Chercher dans le dossier racine et déplacer
                    if chemin_racine.exists():
                        chemin_racine.rename(chemin_final)
                        fichiers_telecharges.append({
                            'type': 'href_direct',
                            'nom_original': pdf_info['nom'],
                            'chemin': str(chemin_final)
                        })
                        print(f"         ✓ {pdf_info['nom']}")
                    elif chemin_final.exists():
                        # Déjà au bon endroit
                        fichiers_telecharges.append({
                            'type': 'href_direct',
                            'nom_original': pdf_info['nom'],
                            'chemin': str(chemin_final)
                        })
                        print(f"         ✓ {pdf_info['nom']}")
                    
                except Exception as e:
                    print(f"         ✗ Erreur: {pdf_info['nom']}")
                
                await asyncio.sleep(1)
        
        # Cliquer sur les PDFs onclick (accusés)
        if pdfs['onclick']:
            for pdf_info in pdfs['onclick']:
                js_click = f"""
                await new Promise(resolve => setTimeout(resolve, 300));
                const link = document.querySelector('#{pdf_info['id']}');
                if (link) link.click();
                """
                
                config_click = CrawlerRunConfig(
                    session_id=self.config.session_id,
                    js_code=js_click,
                    js_only=True,
                    page_timeout=5000,
                    cache_mode=0,
                    verbose=False
                )
                
                try:
                    await crawler.arun(url=url_actuelle, config=config_click)
                    await asyncio.sleep(2)
                except:
                    pass
                
                await asyncio.sleep(1)
        
        return fichiers_telecharges
    
    async def scraper_tous_messages(
        self,
        crawler: AsyncWebCrawler,
        code_juridiction: str,
        messages_non_lus_seulement: bool = True,
        max_messages: int = 100
    ) -> List[Dict]:
        """
        Scrape tous les messages d'une juridiction
        
        Args:
            crawler: Instance du crawler
            code_juridiction: Code de la juridiction
            messages_non_lus_seulement: Si True, seulement les non lus
            max_messages: Nombre maximum de messages
        
        Returns:
            List[Dict]: Liste des messages extraits
        """
        
        print(f"\n Ouverture de l'onglet Messages...")
        
        # Clic sur onglet Messages
        js_messages = """
        await new Promise(resolve => setTimeout(resolve, 1000));
        const ongletMessages = document.querySelector('td[title="Messages"]');
        if (ongletMessages) {
            if (typeof ouvrirMessage === 'function') {
                ouvrirMessage();
            } else {
                ongletMessages.click();
            }
        }
        """
        
        config_messages = CrawlerRunConfig(
            session_id=self.config.session_id,
            js_code=js_messages,
            js_only=True,
            wait_for="css:tr.tableListeTrR1,tr.tableListeTrR2",
            page_timeout=self.config.page_timeout,
            cache_mode=0,
            verbose=False
        )
        
        result_messages = await crawler.arun(
            url=self.config.selection_juridiction_url,
            config=config_messages
        )
        
        if not result_messages.success:
            print(f" Erreur ouverture Messages")
            return []
        
        print(f" Onglet Messages ouvert")
        
        # Extraire les messages
        soup_messages = BeautifulSoup(result_messages.html, 'html.parser')
        
        # Messages non lus ont la classe 'messageNonLu'
        if messages_non_lus_seulement:
            messages_tr = soup_messages.find_all('tr', class_='messageNonLu')
            print(f"   📬 {len(messages_tr)} message(s) NON LU(S) trouvé(s)")
        else:
            # Mode test : scraper UNIQUEMENT les messages lus
            all_messages = soup_messages.find_all('tr', class_='tableListeTrR2')
            messages_lus = [tr for tr in all_messages if 'messageNonLu' not in tr.get('class', [])]
            messages_tr = messages_lus
            print(f"   📖 {len(messages_lus)} message(s) LUS trouvé(s) (mode test)")
        
        if not messages_tr:
            print(" Aucun message")
            return []
        
        messages_tr = messages_tr[:max_messages]
        print(f"   Traitement de {len(messages_tr)} message(s)")
        
        # Parser les messages
        liste_messages = []
        
        for i, tr in enumerate(messages_tr, 1):
            tds = tr.find_all('td')
            
            # Structure : [0]=icône, [1]=expéditeur, [2]=dossier, [3]=objet, [4]=rapporteur, [5]=date
            if len(tds) >= 6:
                statut = 'non_lu' if 'messageNonLu' in tr.get('class', []) else 'lu'
                expediteur = tds[1].get_text(strip=True)
                dossier = tds[2].get_text(strip=True)
                
                link_msg = tds[3].find('a', class_='numMessage')
                if link_msg:
                    objet = link_msg.get_text(strip=True)
                    onclick = link_msg.get('onclick', '')
                    
                    match_msg = re.search(r"lireMessage\('([^']+)',\s*'([^']+)'\)", onclick)
                    
                    if match_msg:
                        msg_id = match_msg.group(1)
                        msg_type = match_msg.group(2)
                    else:
                        continue
                else:
                    continue
                
                rapporteur = tds[4].get_text(strip=True)
                date = tds[5].get_text(strip=True)
                
                liste_messages.append({
                    'index': i,
                    'msg_id': msg_id,
                    'msg_type': msg_type,
                    'statut': statut,
                    'expediteur': expediteur,
                    'dossier': dossier,
                    'objet': objet,
                    'rapporteur': rapporteur,
                    'date': date
                })
        
        # Lire chaque message et télécharger les PDFs
        messages_details = []
        dossier_pdfs = str(self.config.get_pdfs_dir(code_juridiction).absolute())
        
        for msg in liste_messages:
            print(f"\n Message {msg['index']}/{len(liste_messages)}: {msg['objet'][:50]}...")
            
            # Lire le message
            js_lire = f"""
            await new Promise(resolve => setTimeout(resolve, 500));
            if (typeof lireMessage === 'function') {{
                lireMessage('{msg['msg_id']}', '{msg['msg_type']}');
            }}
            """
            
            config_lire = CrawlerRunConfig(
                session_id=self.config.session_id,
                js_code=js_lire,
                js_only=True,
                wait_for="css:#divEnteteMsg",
                page_timeout=self.config.page_timeout,
                cache_mode=0,
                verbose=False
            )
            
            result_detail = await crawler.arun(url=result_messages.url, config=config_lire)
            
            if not result_detail.success:
                continue
            
            # Télécharger les PDFs
            fichiers = await self.telecharger_pdfs_message(
                crawler=crawler,
                html_message=result_detail.html,
                msg_id=msg['msg_id'],
                dossier=dossier_pdfs,
                url_actuelle=result_detail.url
            )
            
            msg['fichiers_telecharges'] = fichiers
            msg['html_complet'] = result_detail.cleaned_html
            
            messages_details.append(msg)
            
            # Retour à la liste
            js_retour = """
            await new Promise(resolve => setTimeout(resolve, 500));
            const btnRetour = document.querySelector('#btRetour');
            if (btnRetour) btnRetour.click();
            await new Promise(resolve => setTimeout(resolve, 1000));
            """
            
            config_retour = CrawlerRunConfig(
                session_id=self.config.session_id,
                js_code=js_retour,
                js_only=True,
                wait_for="js:() => document.querySelector('#divEnteteMsg') === null",
                page_timeout=15000,
                cache_mode=0,
                verbose=False
            )
            
            await crawler.arun(url=result_detail.url, config=config_retour)
            await asyncio.sleep(1)
        
        # Sauvegarde
        juridiction_dir = self.config.get_juridiction_dir(code_juridiction)
        
        # JSON
        save_json(messages_details, juridiction_dir / f"messages_{code_juridiction}.json")
        
        # HTML individuels
        for msg in messages_details:
            save_html(
                msg['html_complet'],
                juridiction_dir / f"message_{msg['msg_id']}.html"
            )
        
        # Résumé
        nb_pdfs = compte_pdfs_dossier(self.config.get_pdfs_dir(code_juridiction))
        taille_pdfs = taille_dossier_pdfs(self.config.get_pdfs_dir(code_juridiction))
        
        print(f"\n Résultats sauvegardés:")
        print(f"   Dossier: {juridiction_dir}")
        print(f"   Messages: {len(messages_details)}")
        print(f"   PDFs: {nb_pdfs} ({taille_pdfs:.1f} Mo)")
        
        return messages_details