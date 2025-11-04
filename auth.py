"""
Module d'authentification Télérecours
"""

import asyncio
from typing import Dict, Optional
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from bs4 import BeautifulSoup

from config import TelecoursConfig


class TelecoursAuth:
    """Gestion de l'authentification Télérecours"""
    
    def __init__(self, config: TelecoursConfig):
        self.config = config
        self.cookies: Dict[str, str] = {}
        self.is_authenticated = False
    
    async def login(self, crawler: AsyncWebCrawler) -> bool:
        """
        Connexion à Télérecours
        
        Returns:
            bool: True si connexion réussie
        """
        if not self.config.username or not self.config.password:
            print("❌ Identifiant et mot de passe requis")
            return False
        
        print("🌐 Connexion à Télérecours...")
        
        # Ouvrir la page de connexion
        config_login = CrawlerRunConfig(
            session_id=self.config.session_id,
            page_timeout=self.config.page_timeout,
            cache_mode=0,
            verbose=False
        )
        
        result_login = await crawler.arun(
            url=self.config.login_url,
            config=config_login
        )
        
        if not result_login.success:
            print(f"❌ Erreur ouverture page login: {result_login.error_message}")
            return False
        
        print("   ✅ Page de connexion ouverte")
        
        # Remplir et soumettre le formulaire
        js_login = f"""
        await new Promise(resolve => setTimeout(resolve, 500));
        
        const usernameField = document.querySelector('#Username');
        if (usernameField) {{
            usernameField.value = '{self.config.username}';
        }}
        
        const passwordField = document.querySelector('#password-field');
        if (passwordField) {{
            passwordField.value = '{self.config.password}';
        }}
        
        await new Promise(resolve => setTimeout(resolve, 300));
        
        const submitButton = document.querySelector('#login-submit');
        if (submitButton) {{
            submitButton.click();
        }}
        """
        
        config_submit = CrawlerRunConfig(
            session_id=self.config.session_id,
            js_code=js_login,
            js_only=True,
            wait_for="css:li[name^='TA']",  # Attendre la page de sélection
            page_timeout=self.config.page_timeout,
            cache_mode=0,
            verbose=False
        )
        
        result_submit = await crawler.arun(
            url=result_login.url,
            config=config_submit
        )
        
        if not result_submit.success:
            print(f"❌ Erreur connexion: {result_submit.error_message}")
            return False
        
        self.is_authenticated = True
        print("   ✅ Connexion réussie")
        
        return True
    
    async def setup_cookie_hook(self, crawler: AsyncWebCrawler):
        """Configure le hook pour capturer les cookies"""
        
        async def hook_after_goto(page, context, url, response, **kwargs):
            """Hook pour capturer les cookies"""
            try:
                cookies_playwright = await context.cookies()
                self.cookies = {
                    cookie['name']: cookie['value'] 
                    for cookie in cookies_playwright
                }
                
                if self.config.verbose and len(self.cookies) > 0 and url and "Login" in url:
                    print(f"   🍪 Session établie ({len(self.cookies)} cookies)")
                
            except Exception as e:
                print(f"   ⚠️  Erreur capture cookies: {e}")
            
            return page
        
        crawler.crawler_strategy.set_hook("after_goto", hook_after_goto)