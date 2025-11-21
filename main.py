#!/usr/bin/env python3
"""
Script principal - Extraction automatique des notifications Télérecours

Usage:
    python main.py                    # Mode interactif
    python main.py --auto             # Mode automatique (toutes les juridictions avec notifs)
    python main.py --juridiction TA78 # Une juridiction spécifique
"""

import asyncio
import argparse
import getpass
import time
import os
import json
from pathlib import Path
from crawl4ai import AsyncWebCrawler, BrowserConfig

from config import TelecoursConfig
from auth import TelecoursAuth
from notifs import NotificationDetector
from scraper_messages import MessageScraper
from utils import print_header, print_summary, compte_pdfs_dossier, send_webhook


async def envoyer_resultats_webhook(config: TelecoursConfig, juridictions: list):
    """Envoie les résultats de toutes les juridictions vers le webhook"""
    
    print("\n📤 Envoi des résultats vers le webhook...")
    
    tous_les_messages = []
    
    for juridiction in juridictions:
        json_file = config.get_juridiction_dir(juridiction.code) / f"messages_{juridiction.code}.json"
        
        if json_file.exists():
            with open(json_file, 'r', encoding='utf-8') as f:
                messages = json.load(f)
                
                # Ajouter le code juridiction à chaque message
                for msg in messages:
                    msg['code_juridiction'] = juridiction.code
                    msg['nom_juridiction'] = juridiction.nom
                
                tous_les_messages.extend(messages)
    
    if tous_les_messages:
        payload = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'nb_juridictions': len(juridictions),
            'nb_messages_total': len(tous_les_messages),
            'messages': tous_les_messages
        }
        
        send_webhook(config.webhook_url, payload)
    else:
        print("⚠️  Aucun message à envoyer")


async def main_auto(config: TelecoursConfig):
    """
    Mode automatique : extrait tous les messages de toutes les juridictions avec notifs
    """
    
    print_header("🤖 MODE AUTOMATIQUE - EXTRACTION COMPLÈTE")
    
    # Configuration du navigateur
    browser_config = BrowserConfig(
        headless=config.headless,
        verbose=False,
        viewport_width=1920,
        viewport_height=1080,
        accept_downloads=True,
        downloads_path=str(config.pdfs_dir.absolute())
    )
    
    start_time = time.time()
    total_messages = 0
    total_pdfs = 0
    juridictions_traitees = 0
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        
        # Authentification
        auth = TelecoursAuth(config)
        await auth.setup_cookie_hook(crawler)
        
        if not await auth.login(crawler):
            return
        
        # Détection des notifications
        detector = NotificationDetector(config)
        juridictions = await detector.get_juridictions_avec_notifs(crawler)
        
        if not juridictions:
            print("\n📭 Aucune notification trouvée")
            return
        
        await detector.afficher_juridictions_avec_notifs(juridictions)
        
        # Demander confirmation
        reponse = input(f"\n❓ Extraire les messages de ces {len(juridictions)} juridictions ? (o/N) : ")
        if reponse.lower() != 'o':
            print("❌ Extraction annulée")
            return
        
        # Traiter chaque juridiction
        scraper = MessageScraper(config, auth.cookies)
        
        for i, juridiction in enumerate(juridictions, 1):
            print(f"\n{'='*70}")
            print(f"📍 Juridiction {i}/{len(juridictions)}: {juridiction.code} ({juridiction.nom})")
            print(f"   {juridiction.nb_notifs} message(s) non lu(s)")
            print(f"{'='*70}")
            
            # Sélectionner la juridiction
            if not await detector.selectionner_juridiction(crawler, juridiction):
                print(f"⚠️  Impossible de sélectionner {juridiction.code}, on passe à la suivante")
                continue
            
            # Scraper les messages NON LUS
            messages = await scraper.scraper_tous_messages(
                crawler=crawler,
                code_juridiction=juridiction.code,
                messages_non_lus_seulement=not config.scraper_messages_lus,
                max_messages=config.max_messages_par_juridiction
            )
            
            if messages:
                total_messages += len(messages)
                juridictions_traitees += 1
                
                # Compter les PDFs
                pdfs_dir = config.get_pdfs_dir(juridiction.code)
                nb_pdfs = compte_pdfs_dossier(pdfs_dir)
                total_pdfs += nb_pdfs
                
                print(f"\n   ✅ {len(messages)} message(s) extrait(s)")
                print(f"   📥 {nb_pdfs} PDF(s) téléchargé(s)")
        
        # Résumé final
        duration = time.time() - start_time
        print_summary(juridictions_traitees, total_messages, total_pdfs, duration)
        
        # Les messages ont déjà été envoyés individuellement au webhook pendant le scraping
        print("\n✅ Tous les messages ont été envoyés au webhook individuellement")
        
        await crawler.crawler_strategy.kill_session(config.session_id)


async def main_juridiction(config: TelecoursConfig, code_juridiction: str):
    """
    Mode juridiction spécifique
    """
    
    print_header(f"📍 EXTRACTION - {code_juridiction}")
    
    browser_config = BrowserConfig(
        headless=config.headless,
        verbose=False,
        viewport_width=1920,
        viewport_height=1080,
        accept_downloads=True,
        downloads_path=str(config.pdfs_dir.absolute())
    )
    
    start_time = time.time()
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        
        # Authentification
        auth = TelecoursAuth(config)
        await auth.setup_cookie_hook(crawler)
        
        if not await auth.login(crawler):
            return
        
        # Détection des notifications
        detector = NotificationDetector(config)
        juridictions = await detector.get_juridictions_avec_notifs(crawler)
        
        # Chercher la juridiction demandée
        juridiction_cible = next(
            (j for j in juridictions if j.code == code_juridiction),
            None
        )
        
        if not juridiction_cible:
            print(f"\n⚠️  Juridiction {code_juridiction} non trouvée ou sans notification")
            return
        
        print(f"\n📍 {juridiction_cible.code} - {juridiction_cible.nom}")
        print(f"   {juridiction_cible.nb_notifs} message(s) non lu(s)")
        
        # Sélectionner la juridiction
        if not await detector.selectionner_juridiction(crawler, juridiction_cible):
            return
        
        # Scraper les messages
        scraper = MessageScraper(config, auth.cookies)
        messages = await scraper.scraper_tous_messages(
            crawler=crawler,
            code_juridiction=code_juridiction,
            messages_non_lus_seulement=not config.scraper_messages_lus,
            max_messages=config.max_messages_par_juridiction
        )
        
        # Résumé
        duration = time.time() - start_time
        nb_pdfs = compte_pdfs_dossier(config.get_pdfs_dir(code_juridiction))
        
        print_summary(1, len(messages) if messages else 0, nb_pdfs, duration)
        
        # Les messages ont déjà été envoyés individuellement au webhook pendant le scraping
        if config.webhook_url and messages:
            print(f"\n✅ {len(messages)} message(s) envoyé(s) au webhook individuellement")
        
        await crawler.crawler_strategy.kill_session(config.session_id)


async def main_interactif(config: TelecoursConfig):
    """
    Mode interactif : affiche les juridictions et laisse l'utilisateur choisir
    """
    
    print_header("💬 MODE INTERACTIF")
    
    browser_config = BrowserConfig(
        headless=config.headless,
        verbose=False,
        viewport_width=1920,
        viewport_height=1080,
        accept_downloads=True,
        downloads_path=str(config.pdfs_dir.absolute())
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        
        # Authentification
        auth = TelecoursAuth(config)
        await auth.setup_cookie_hook(crawler)
        
        if not await auth.login(crawler):
            return
        
        # Détection des notifications
        detector = NotificationDetector(config)
        juridictions = await detector.get_juridictions_avec_notifs(crawler)
        
        if not juridictions:
            print("\n📭 Aucune notification trouvée")
            return
        
        await detector.afficher_juridictions_avec_notifs(juridictions)
        
        # Menu de choix
        print("Options:")
        print("  1. Extraire TOUTES les juridictions")
        print("  2. Choisir UNE juridiction spécifique")
        print("  0. Quitter")
        
        choix = input("\nVotre choix : ").strip()
        
        if choix == "0":
            print("👋 Au revoir !")
            return
        
        elif choix == "1":
            # Extraire toutes
            scraper = MessageScraper(config, auth.cookies)
            start_time = time.time()
            total_messages = 0
            total_pdfs = 0
            
            for i, juridiction in enumerate(juridictions, 1):
                print(f"\n{'='*70}")
                print(f"📍 Juridiction {i}/{len(juridictions)}: {juridiction.code}")
                print(f"{'='*70}")
                
                if not await detector.selectionner_juridiction(crawler, juridiction):
                    continue
                
                messages = await scraper.scraper_tous_messages(
                    crawler=crawler,
                    code_juridiction=juridiction.code,
                    messages_non_lus_seulement=not config.scraper_messages_lus,
                    max_messages=config.max_messages_par_juridiction
                )
                
                if messages:
                    total_messages += len(messages)
                    nb_pdfs = compte_pdfs_dossier(config.get_pdfs_dir(juridiction.code))
                    total_pdfs += nb_pdfs
            
            duration = time.time() - start_time
            print_summary(len(juridictions), total_messages, total_pdfs, duration)
        
        elif choix == "2":
            # Choisir une juridiction
            print("\nCodes disponibles:")
            for j in juridictions:
                print(f"  - {j.code} ({j.nom})")
            
            code = input("\nCode juridiction : ").strip().upper()
            
            juridiction_cible = next((j for j in juridictions if j.code == code), None)
            
            if not juridiction_cible:
                print(f"❌ Juridiction {code} non trouvée")
                return
            
            if not await detector.selectionner_juridiction(crawler, juridiction_cible):
                return
            
            scraper = MessageScraper(config, auth.cookies)
            start_time = time.time()
            
            messages = await scraper.scraper_tous_messages(
                crawler=crawler,
                code_juridiction=code,
                messages_non_lus_seulement=not config.scraper_messages_lus,
                max_messages=config.max_messages_par_juridiction
            )
            
            duration = time.time() - start_time
            nb_pdfs = compte_pdfs_dossier(config.get_pdfs_dir(code))
            
            print_summary(1, len(messages) if messages else 0, nb_pdfs, duration)
            
            # Envoyer webhook si configuré
            if config.webhook_url:
                await envoyer_resultats_webhook(config, [juridiction_cible])
        
        await crawler.crawler_strategy.kill_session(config.session_id)


def main():
    """Point d'entrée"""
    
    parser = argparse.ArgumentParser(
        description="Extracteur de messages Télérecours avec détection automatique des notifications"
    )
    parser.add_argument(
        '--auto',
        action='store_true',
        help="Mode automatique : extrait toutes les juridictions avec notifications"
    )
    parser.add_argument(
        '--juridiction',
        type=str,
        help="Code d'une juridiction spécifique (ex: TA78)"
    )
    parser.add_argument(
        '--no-headless',
        action='store_true',
        help="Désactiver le mode headless (afficher le navigateur)"
    )
    parser.add_argument(
        '--messages-lus',
        action='store_true',
        help="Scraper les messages lus au lieu des non lus (pour tests)"
    )
    parser.add_argument(
        '--max-messages',
        type=int,
        default=None,
        help="Nombre maximum de messages par juridiction (sera demandé si non spécifié)"
    )
    parser.add_argument(
        '--username',
        type=str,
        help="Identifiant Télérecours (sinon lu depuis TELERECOURS_USERNAME ou demandé)"
    )
    parser.add_argument(
        '--password',
        type=str,
        help="Mot de passe Télérecours (sinon lu depuis TELERECOURS_PASSWORD ou demandé)"
    )
    parser.add_argument(
        '--webhook',
        type=str,
        help="URL du webhook pour envoyer les résultats JSON"
    )
    
    args = parser.parse_args()
    
    # Configuration
    config = TelecoursConfig(
        headless=not args.no_headless,  # headless par défaut, sauf si --no-headless
        max_messages_par_juridiction=args.max_messages,
        scraper_messages_lus=args.messages_lus,
        webhook_url=args.webhook
    )
    
    # Demander les identifiants
    print("=" * 70)
    print("🔐 IDENTIFIANTS TÉLÉRECOURS")
    print("=" * 70)
    
    # Priorité : argument CLI > variable d'environnement > input interactif
    config.username = args.username or os.environ.get('TELERECOURS_USERNAME')
    if not config.username:
        config.username = input("Identifiant: ").strip()
    else:
        source = "argument CLI" if args.username else "variable d'environnement"
        print(f"Identifiant: {config.username} (depuis {source})")
    
    if not config.username:
        print("❌ Identifiant requis")
        return
    
    config.password = args.password or os.environ.get('TELERECOURS_PASSWORD')
    if not config.password:
        config.password = getpass.getpass("Mot de passe: ").strip()
    else:
        source = "argument CLI" if args.password else "variable d'environnement"
        print(f"Mot de passe: *** (depuis {source})")
    
    if not config.password:
        print("❌ Mot de passe requis")
        return
    
    # Demander le nombre de messages si non spécifié
    if args.max_messages is None:
        try:
            nb_messages = input("Nombre de messages à scraper (défaut: 10) : ").strip()
            args.max_messages = int(nb_messages) if nb_messages else 10
        except ValueError:
            args.max_messages = 10
    
    config.max_messages_par_juridiction = args.max_messages
    
    if args.messages_lus:
        print(f"⚠️  Mode TEST : scraping des messages LUS (pas de désactivation des notifs)")
    
    # Lancer le mode approprié
    if args.auto:
        asyncio.run(main_auto(config))
    elif args.juridiction:
        asyncio.run(main_juridiction(config, args.juridiction.upper()))
    else:
        asyncio.run(main_interactif(config))


if __name__ == "__main__":
    main()