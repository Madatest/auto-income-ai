#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Daemon Autonome 24h/24 pour AUTO-INCOME AI.
Fonctionne en arrière-plan permanent sur Android Termux sans intervention humaine.
Maintient le wake-lock, exécute les cycles toutes les 6h et sert la boutique locale sur :8080.
"""

import os
import sys
import time
import signal
import logging
import threading
import subprocess
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime, timezone

from main import AutoIncomeAgent, send_lemur_hud

# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/daemon.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("AutoIncomeAI.Daemon")

RUNNING = True
INTERVAL_SECONDS = 3600  # 1 heure entre chaque cycle autonome (conforme Objectif_per_hour.txt)
HTTP_PORT = 8080


def signal_handler(signum, frame):
    global RUNNING
    logger.info("Signal d'arrêt reçu. Arrêt propre du démon...")
    RUNNING = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def acquire_wake_lock():
    """Empêche la mise en veille profonde du CPU Android."""
    try:
        subprocess.run(["termux-wake-lock"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info("Termux Wake-Lock activé (Fonctionnement 24h/24 garanti).")
    except Exception as e:
        logger.warning(f"Impossible d'activer le wake-lock Termux: {e}")


def run_http_server(directory: str = "site", port: int = HTTP_PORT):
    """Sert le catalogue et le tableau de bord localement en arrière-plan."""
    import functools
    handler = functools.partial(SimpleHTTPRequestHandler, directory=directory)
    try:
        server = HTTPServer(("0.0.0.0", port), handler)
        logger.info(f"Serveur Web de la boutique actif sur http://localhost:{port}")
        server.serve_forever()
    except Exception as err:
        logger.warning(f"Serveur HTTP non démarré sur :{port}: {err}")


def main():
    logger.info("=======================================================")
    logger.info("🚀 DÉMARRAGE DU DÉMON AUTONOME 24H/24 AUTO-INCOME AI")
    logger.info("=======================================================")

    acquire_wake_lock()
    send_lemur_hud("Auto-Income AI: Démon 24h/24 activé sur votre téléphone.")

    # Démarrage du serveur web local en tâche de fond
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    agent = AutoIncomeAgent(config_path="config.json", simulation_mode=False)

    from main import safe_git_sync

    while RUNNING:
        try:
            logger.info("Synchronisation préalable avec GitHub...")
            safe_git_sync(logger)

            logger.info("Exécution du cycle autonome planifié...")
            cycle_result = agent.run_cycle()
            logger.info(f"Cycle terminé avec succès (ID #{cycle_result.get('execution_id')}).")
        except Exception as err:
            logger.error(f"Erreur lors de l'exécution du cycle : {err}", exc_info=True)
            send_lemur_hud(f"Auto-Income AI: Avertissement - {err}")

        # Attente jusqu'au prochain cycle avec vérifications régulières
        logger.info(f"Mise en veille active pour {INTERVAL_SECONDS // 3600} heures...")
        sleep_elapsed = 0
        while sleep_elapsed < INTERVAL_SECONDS and RUNNING:
            time.sleep(30)
            sleep_elapsed += 30

    logger.info("Démon AUTO-INCOME AI arrêté.")


if __name__ == "__main__":
    main()
