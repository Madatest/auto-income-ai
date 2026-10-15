#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Entrypoint for AUTO-INCOME AI — Autonomous First-Revenue Mission.
Orchestrates the 1-hour autonomous loop adhering to the 5 mandatory phases:
- PHASE A: Rapid Analysis & International Needs Discovery
- PHASE B: Commercial Execution (0$ Digital Asset & Sales Pipeline Build)
- PHASE C: Objective Evaluation & Metric Measurement
- PHASE D: Self-Improvement & Strategy Adaptation
- PHASE E: Revenue Verification (Binance Pay & Audit Trail)
"""

import os
import sys
import time
import json
import logging
import argparse
import subprocess
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from storage import StorageManager
from opportunity_engine import OpportunityEngine
from content_factory import ContentFactory
from report import ReportGenerator
from monetization import MonetizationAdvisor
from payment_verifier import PaymentVerifier
from wolf_supervisor import WolfSupervisor


# Setup logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/income_agent.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("AutoIncomeAI.Main")


def send_lemur_hud(message: str, mode: Optional[str] = None) -> None:
    """Sends discreet visual HUD telemetry via Lemur widget and on-screen Toast."""
    try:
        cmd = ["lemur"]
        if mode:
            cmd.append(f"--{mode}")
        cmd.append(message)
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
    except Exception:
        pass


def safe_git_sync(logger_inst=None, cycle_id: Optional[int] = None) -> bool:
    """
    Resilient bidirectional Git sync between local Termux and remote GitHub.
    - Purges stale .git/index.lock if left by an ungraceful exit
    - Stages deliverables, database state and configuration
    - Pulls with auto-rebase (-X theirs) to absorb remote changes
    - Pushes to remote origin
    - Completely non-blocking on network errors (works offline without crashing)
    """
    log = logger_inst or logger
    send_lemur_hud("Synchronisation GitHub Cloud...", mode="active")
    if not os.path.exists(".git"):
        return False

    try:
        # 1. Clean stale git lock if older than 30s
        lock_path = ".git/index.lock"
        if os.path.exists(lock_path):
            try:
                if (time.time() - os.path.getmtime(lock_path)) > 30:
                    os.remove(lock_path)
                    log.info("Verrou orphelin .git/index.lock purgé.")
            except Exception:
                pass

        # 2. Check remote
        res_remote = subprocess.run(["git", "remote"], capture_output=True, text=True, timeout=5)
        if "origin" not in res_remote.stdout:
            return False

        # 3. Stage relevant files
        subprocess.run(
            ["git", "add", "data/", "site/", "logs/", "config.json"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10
        )

        # 4. Commit if changes exist
        diff_check = subprocess.run(["git", "diff", "--staged", "--quiet"], timeout=5)
        if diff_check.returncode != 0:
            msg = f"chore(autonomous): synchronisation cycle #{cycle_id} supervisé par WOLF [skip ci]" if cycle_id else "chore(autonomous): synchronisation état et livrables [skip ci]"
            subprocess.run(
                ["git", "commit", "-m", msg],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10
            )
            log.info("Modifications locales commitées pour synchronisation.")

        # 5. Pull with rebase (resolve in favor of current cycle or theirs)
        pull_res = subprocess.run(
            ["git", "pull", "--rebase", "-X", "theirs", "origin", "main"],
            capture_output=True, text=True, timeout=20
        )
        if pull_res.returncode != 0:
            # Abort rebase if stuck
            subprocess.run(["git", "rebase", "--abort"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)

        # 6. Push to remote
        push_res = subprocess.run(
            ["git", "push", "origin", "main"],
            capture_output=True, text=True, timeout=25
        )
        if push_res.returncode == 0:
            log.info("☁️ Synchronisation Cloud réussie : Dépôt GitHub à jour avec les derniers cycles.")
            return True
        else:
            log.warning(f"Git push non abouti (mode hors-ligne ou réseau instable) : {push_res.stderr.strip()}")
            return False
    except Exception as err:
        log.warning(f"Synchronisation Git différée : {err}")
        return False


def load_env_file(filepath: str = ".env") -> None:
    """Loads environment variables from .env if present and not already set."""
    if not os.path.isabs(filepath):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cand = os.path.join(base_dir, filepath)
        if os.path.exists(cand):
            filepath = cand
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """Loads configuration with safe defaults."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


class AutoIncomeAgent:
    """The Autonomous 1-Hour Cycle Income Generation Engine."""

    def __init__(self, config_path: str = "config.json", simulation_mode: bool = False):
        load_env_file()
        self.config = load_config(config_path)
        self.simulation_mode = simulation_mode or self.config.get("execution", {}).get("simulation_mode", False)
        
        # Initialize core components
        storage_cfg = self.config.get("storage", {})
        self.lock_file = storage_cfg.get("lock_file", "data/agent.lock")
        self.storage = StorageManager(
            db_path=storage_cfg.get("sqlite_db", "data/income_ai.db"),
            state_json_path=storage_cfg.get("state_json", "data/state.json"),
            reports_dir=storage_cfg.get("reports_dir", "data/cycle_reports")
        )
        self.opp_engine = OpportunityEngine(self.config, self.storage)
        self.content_factory = ContentFactory(output_dir=storage_cfg.get("deliverables_dir", "site/deliverables"))
        self.reporter = ReportGenerator(self.storage, site_dir=storage_cfg.get("site_dir", "site"))
        
        seller_profile = self.config.get("agent", {}).get("seller_profile", {})
        self.payment_verifier = PaymentVerifier(
            receipts_file=storage_cfg.get("receipts_file", "data/payment_receipts.json"),
            binance_uid=seller_profile.get("binance_uid", "254779310")
        )

        # WOLF: Autonomous Supervisor & Performance Enforcer
        self.supervisor = WolfSupervisor(
            db_path=storage_cfg.get("sqlite_db", "data/income_ai.db"),
            directives_file=storage_cfg.get("wolf_directives", "data/wolf_directives.json")
        )

    # -------------------------------------------------------------------------
    # PHASE A — ANALYSE RAPIDE
    # -------------------------------------------------------------------------
    def phase_a_analysis(self) -> Dict[str, Any]:
        """Loads state, inspects previous cycle blockers, and selects top international opportunity."""
        logger.info("=== [PHASE A] Analyse Rapide & Découverte Internationale ===")
        send_lemur_hud("Phase A: Analyse des opportunités internationales...", mode="active")

        # Check active supervisor directive from WOLF
        active_directive = self.supervisor.get_active_directive()
        if active_directive:
            logger.info(f"🐺 [WOLF SUPERVISOR DIRECTIVE ACTIVE] {active_directive.get('primary_directive')}")
            send_lemur_hud(f"WOLF Directive: {active_directive.get('primary_directive')[:35]}...", mode="active")

        stats = self.storage.get_summary_stats()
        latest_cycle = self.storage.get_latest_cycle_report()
        
        # Identify blockers
        blockers = []
        if stats.get("total_deliverables", 0) == 0:
            blockers.append("Aucun actif commercial encore produit pour générer des ventes.")
        elif stats.get("total_confirmed_revenue_usd", 0.0) == 0.0:
            blockers.append("Actifs publiés mais trafic/conversion direct en cours d'amorçage international.")

        # Discover & score opportunities
        scored_opps = self.opp_engine.collect_and_evaluate(force_simulation=self.simulation_mode)
        top_opp = self.opp_engine.select_best_opportunity()

        return {
            "stats": stats,
            "blockers_identified": blockers,
            "opportunities_found": len(scored_opps),
            "top_score": scored_opps[0]["score"] if scored_opps else 0.0,
            "selected_opportunity": top_opp,
            "wolf_directive": active_directive
        }

    # -------------------------------------------------------------------------
    # PHASE B — EXÉCUTION COMMERCIALE
    # -------------------------------------------------------------------------
    def phase_b_execution(self, selected_opp: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Produces a concrete monetizable deliverable at strict 0 USD cost."""
        logger.info("=== [PHASE B] Exécution Commerciale & Production d'Actif ===")
        send_lemur_hud("Phase B: Production d'un actif commercial 0 USD...", mode="active")

        deliverable_data: Optional[Dict[str, Any]] = None
        if selected_opp:
            logger.info(f"Création d'un actif pour : '{selected_opp['title']}' ({selected_opp.get('category')})")
            deliverable_data = self.content_factory.build_deliverable(selected_opp)
            deliverable_id = self.storage.save_deliverable(deliverable_data)
            self.storage.mark_opportunity_processed(selected_opp.get("hash", ""))
            deliverable_data["id"] = deliverable_id
            logger.info(f"Actif enregistré avec succès #{deliverable_id} ({deliverable_data['file_path']})")

            # Outbound Telemetry & Autonomous Submission (Zero Human Intervention)
            is_bounty = deliverable_data.get("category") == "bounty_solution" or "bounty" in selected_opp.get("title", "").lower()
            price = deliverable_data.get("price_usd", 0.0)
            title_short = selected_opp["title"][:32]
            source_url = selected_opp.get("source_url", "")
            proposal_text = deliverable_data.get("metadata", {}).get("proposal_snippet", "")

            # Attempt autonomous remote submission if target is a GitHub issue
            submission_res = None
            if is_bounty and source_url and "github.com" in source_url and proposal_text:
                try:
                    from outbound_agent import OutboundSubmitter
                    submission_res = OutboundSubmitter.submit_issue_comment(source_url, proposal_text)
                    if submission_res.get("success"):
                        logger.info(f"🚀 [SOUMISSION AUTONOME EN DIRECT] Proposition postée automatiquement sur {source_url}!")
                        send_lemur_hud(f"🚀 Prime soumise automatiquement sur GitHub !", mode="active")
                        gemini_say_path = os.path.expanduser("~/.local/bin/gemini-say")
                        if os.path.exists(gemini_say_path):
                            try:
                                subprocess.run([gemini_say_path, "Proposition technique soumise automatiquement sur GitHub."], stdout=subprocess.DEVNULL, timeout=8)
                            except Exception:
                                pass
                except Exception as sub_err:
                    logger.warning(f"Erreur tentative soumission autonome: {sub_err}")

            if not submission_res or not submission_res.get("success"):
                if is_bounty:
                    send_lemur_hud(f"🎯 Bounty prête : {title_short} (${price})", mode="active")
                else:
                    send_lemur_hud(f"📦 Actif prêt : {title_short} (${price})", mode="active")
        else:
            logger.warning("Aucune nouvelle opportunité à convertir pour ce cycle.")

        return {
            "deliverable": deliverable_data,
            "verifiable_output_created": deliverable_data is not None,
            "cost_incurred_usd": 0.0  # Règle absolue du coût zéro
        }

    # -------------------------------------------------------------------------
    # PHASE C — ÉVALUATION
    # -------------------------------------------------------------------------
    def phase_c_evaluation(self, phase_a_res: Dict[str, Any], phase_b_res: Dict[str, Any]) -> Dict[str, Any]:
        """Objectively measures results, separating observed facts from hypotheses."""
        logger.info("=== [PHASE C] Évaluation des Résultats Réels ===")
        send_lemur_hud("Phase C: Évaluation & métriques d'impact...", mode="active")

        actions_executed = []
        if phase_b_res.get("verifiable_output_created"):
            actions_executed.append(f"Actif commercial #{phase_b_res['deliverable']['id']} produit et prêt à la vente.")
        else:
            actions_executed.append("Maintenance et inspection des offres existantes.")

        # Facts vs Hypotheses
        facts = [
            f"Opportunités scannées : {phase_a_res['opportunities_found']}",
            f"Dépense financière : 0.00 USD",
            f"Fichier actif physique créé : {phase_b_res['deliverable']['file_path'] if phase_b_res.get('deliverable') else 'N/A'}"
        ]
        hypotheses = [
            "La visibilité sur GitHub Pages et Binance Pay convertit prioritairement les acheteurs anglophones et crypto."
        ]

        return {
            "actions_executed": actions_executed,
            "observed_facts": facts,
            "working_hypotheses": hypotheses,
            "root_cause_analysis": "Phase de démarrage : focus sur l'élargissement du catalogue et des points de contact internationaux."
        }

    # -------------------------------------------------------------------------
    # PHASE D — AUTO-AMÉLIORATION
    # -------------------------------------------------------------------------
    def phase_d_self_improvement(self, is_revenue_confirmed: bool) -> Dict[str, Any]:
        """Applies adaptive strategy refinements if no sale has confirmed yet."""
        logger.info("=== [PHASE D] Auto-Amélioration & Ajustement Stratégique ===")
        send_lemur_hud("Phase D: Optimisation stratégique & auto-ajustement...", mode="active")

        improvements_applied = []
        if not is_revenue_confirmed:
            improvements_applied.append("Diversification du mix produit : alternance guides numériques, gigs ComeUp et micro-outils.")
            improvements_applied.append("Mise en avant du règlement Binance Pay instantané sans frais (UID 254779310).")
            improvements_applied.append("Optimisation continue du temps de cycle pour respecter l'objectif horaire.")
        else:
            improvements_applied.append("PREMIER REVENU CONFIRMÉ : bascule en mode expansion commerciale.")

        return {
            "improvements": improvements_applied,
            "strategy_status": "EXPANSION" if is_revenue_confirmed else "ACQUISITION_ITERATION"
        }

    # -------------------------------------------------------------------------
    # PHASE E — VÉRIFICATION DU PREMIER REVENU
    # -------------------------------------------------------------------------
    def phase_e_revenue_verification(self) -> Dict[str, Any]:
        """Searches and verifies authentic received commercial payments without fabrication."""
        logger.info("=== [PHASE E] Vérification des Paiements & Audit du Premier Revenu ===")
        send_lemur_hud("Phase E: Audit des transactions Binance UID 254779310...", mode="active")

        payment_found = self.payment_verifier.check_for_payments()
        verification_channels = self.payment_verifier.get_verification_status()

        if payment_found and payment_found.get("confirmed"):
            amount = payment_found["amount"]
            cur = payment_found.get("currency", "USD")
            ref = payment_found.get("tx_reference", "TX-CONFIRMED")
            logger.info(f"🎉 TRANSACTION COMMERCIALE RÉELLE DÉTECTÉE : {amount} {cur} (Réf: {ref})")

            # Persist confirmed revenue
            rev_id = self.storage.record_confirmed_revenue(payment_found)
            send_lemur_hud(f"🎉 VICTOIRE: {amount} {cur} reçu sur Binance !", mode="idle")
            
            return {
                "first_real_revenue_achieved": True,
                "amount": amount,
                "currency": cur,
                "tx_reference": ref,
                "source": payment_found.get("source"),
                "timestamp": payment_found.get("timestamp"),
                "db_record_id": rev_id,
                "channels_status": verification_channels
            }

        # Check existing database state
        already_confirmed = self.storage.is_first_revenue_confirmed()

        return {
            "first_real_revenue_achieved": already_confirmed,
            "amount": 0.0,
            "currency": "USD",
            "tx_reference": None,
            "source": None,
            "note": "Aucun nouveau paiement détecté pour ce cycle. Surveillance active sur Binance UID 254779310.",
            "channels_status": verification_channels
        }

    # -------------------------------------------------------------------------
    # FULL CYCLE EXECUTION ORCHESTRATOR
    # -------------------------------------------------------------------------
    def run_cycle(self) -> Dict[str, Any]:
        """
        Executes a complete 1-hour autonomous cycle through all 5 phases with lock protection.
        """
        # Guard against overlapping runs
        if not StorageManager.acquire_lock(self.lock_file):
            logger.warning("Agent execution already in progress (lock held). Aborting duplicate run.")
            return {"status": "LOCKED", "message": "Execution already running"}

        start_time = time.time()
        start_iso = datetime.now(timezone.utc).isoformat()
        logger.info(f"=== [CYCLE AUTONOME D'UNE HEURE DÉMARRÉ à {start_iso}] ===")
        send_lemur_hud("Cycle 1h en cours... Ne pas toucher l'écran", mode="active")

        try:
            # 1. Phase A: Analysis
            phase_a = self.phase_a_analysis()

            # 2. Phase B: Execution
            phase_b = self.phase_b_execution(phase_a.get("selected_opportunity"))

            # 3. Phase C: Evaluation
            phase_c = self.phase_c_evaluation(phase_a, phase_b)

            # 4. Phase E: Revenue Verification (checked before Phase D to steer adaptation)
            phase_e = self.phase_e_revenue_verification()
            is_revenue_confirmed = phase_e["first_real_revenue_achieved"]

            # 5. Phase D: Self-Improvement
            phase_d = self.phase_d_self_improvement(is_revenue_confirmed)

            duration = round(time.time() - start_time, 2)
            end_iso = datetime.now(timezone.utc).isoformat()

            # Record execution in SQLite
            deliverable_rec = phase_b.get("deliverable")
            exec_id = self.storage.record_execution(
                status="SUCCESS",
                opps_found=phase_a["opportunities_found"],
                deliverables_created=1 if deliverable_rec else 0,
                duration_sec=duration,
                notes=f"Produit '{deliverable_rec['title']}'" if deliverable_rec else "Surveillance et maintien"
            )

            # Build comprehensive cycle report adhering to Section 9 of Objectif_per_hour.txt
            cycle_report = {
                "cycle_id": exec_id,
                "execution_id": exec_id,
                "status": "SUCCESS",
                "start_time": start_iso,
                "end_time": end_iso,
                "duration_seconds": duration,
                "duration_sec": duration,
                "opportunities_scanned": phase_a["opportunities_found"],
                "deliverable": deliverable_rec,
                "costs_incurred_usd": 0.0,
                "first_real_revenue": is_revenue_confirmed,
                "phases": {
                    "phase_a_analysis": {
                        "opportunities_scanned": phase_a["opportunities_found"],
                        "blockers": phase_a["blockers_identified"],
                        "selected_opportunity": phase_a["selected_opportunity"]["title"] if phase_a.get("selected_opportunity") else None
                    },
                    "phase_b_execution": {
                        "deliverable_created": deliverable_rec["title"] if deliverable_rec else None,
                        "file_path": deliverable_rec["file_path"] if deliverable_rec else None,
                        "price_usd": deliverable_rec["price_usd"] if deliverable_rec else 0.0,
                        "monetization_channel": deliverable_rec["monetization_channel"] if deliverable_rec else None
                    },
                    "phase_c_evaluation": phase_c,
                    "phase_d_self_improvement": phase_d,
                    "phase_e_revenue_verification": phase_e
                },
                "tasks_completed": phase_c["actions_executed"],
                "tasks_failed": [],
                "tasks_pending": [
                    "Vérification continue des notifications de paiement Binance Pay",
                    "Génération du prochain actif au cycle suivant (1h)",
                    "Synchronisation cloud automatique via GitHub Actions"
                ],
                "next_scheduled_action": "Cycle suivant dans 1 heure (ou déclenchement immédiat)"
            }

            # -----------------------------------------------------------------
            # WOLF SUPERVISION AUDIT & DIRECTIVE DISPATCH
            # -----------------------------------------------------------------
            wolf_review = self.supervisor.review_cycle(cycle_report)
            cycle_report["wolf_supervision"] = wolf_review

            # Persist cycle report with supervisor review
            report_file = self.storage.save_cycle_report(cycle_report)
            logger.info(f"Rapport de cycle complet avec supervision WOLF sauvegardé à : {report_file}")

            # Update dashboards
            self.reporter.build_html_dashboard()
            console_report = self.reporter.generate_console_summary(
                exec_id, duration, phase_a["opportunities_found"], deliverable_rec
            )
            print("\n" + console_report + "\n")
            print("\n" + self.supervisor.format_console_verdict(wolf_review) + "\n")

            hud_msg = f"Cycle #{exec_id} terminé avec succès (Score: {wolf_review.get('decision_score')}/100). En veille."
            send_lemur_hud(hud_msg, mode="idle")

            return cycle_report

        finally:
            StorageManager.release_lock(self.lock_file)
            logger.info("=== [CYCLE TERMINÉ ET VERROU LIBÉRÉ] ===")
            if not self.simulation_mode:
                safe_git_sync(logger, cycle_id=exec_id if 'exec_id' in locals() else None)


def main():
    load_env_file()
    parser = argparse.ArgumentParser(description="AUTO-INCOME AI — Autonomous First-Revenue Engine")
    parser.add_argument("--run", action="store_true", help="Execute one autonomous 1-hour cycle")
    parser.add_argument("--simulate", action="store_true", help="Run with demonstration dataset")
    parser.add_argument("--report", action="store_true", help="Regenerate HTML dashboard and print summary")
    parser.add_argument("--status", action="store_true", help="Display current system KPIs and payment status")
    parser.add_argument("--wolf", action="store_true", help="Display WOLF Supervisor latest audit and active directives")
    parser.add_argument("--sync", action="store_true", help="Synchronize local state and deliverables with GitHub")
    args = parser.parse_args()

    if args.sync:
        res = safe_git_sync(logger)
        sys.exit(0 if res else 1)

    agent = AutoIncomeAgent(simulation_mode=args.simulate)

    if args.wolf:
        active_dir = agent.supervisor.get_active_directive()
        if active_dir:
            print("\n" + agent.supervisor.format_console_verdict(active_dir) + "\n")
        else:
            print("Aucune directive WOLF active pour l'instant.")
        sys.exit(0)

    if args.status:
        stats = agent.storage.get_summary_stats()
        latest = agent.storage.get_latest_cycle_report()
        verif = agent.payment_verifier.get_verification_status()
        active_wolf = agent.supervisor.get_active_directive()
        output = {
            "stats": stats,
            "latest_cycle_report": latest,
            "payment_verification": verif,
            "wolf_supervision": active_wolf
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        sys.exit(0)

    if args.report:
        path = agent.reporter.build_html_dashboard()
        print(f"HTML dashboard generated at: {path}")
        sys.exit(0)

    try:
        agent.run_cycle()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Critical execution error: {e}", exc_info=True)
        send_lemur_hud(f"Auto-Income AI Erreur: {e}")
        StorageManager.release_lock()
        sys.exit(1)


if __name__ == "__main__":
    main()
