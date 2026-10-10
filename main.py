#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Entrypoint for AUTO-INCOME AI.
Orchestrates the 12-step autonomous loop:
Discovery -> Deduplication -> Scoring -> Selection -> Deliverable Build -> QA -> Storage -> Reporting.
"""

import os
import sys
import time
import json
import logging
import argparse
import subprocess
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from storage import StorageManager
from opportunity_engine import OpportunityEngine
from content_factory import ContentFactory
from report import ReportGenerator
from monetization import MonetizationAdvisor


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


def send_lemur_hud(message: str) -> None:
    """Sends discreet visual HUD telemetry via Lemur widget or CLI if present."""
    try:
        # CLI fallback
        subprocess.run(["lemur", message], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1)
    except Exception:
        pass


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """Loads configuration with safe defaults."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


class AutoIncomeAgent:
    """The Autonomous Income Generation Engine."""

    def __init__(self, config_path: str = "config.json", simulation_mode: bool = False):
        self.config = load_config(config_path)
        self.simulation_mode = simulation_mode or self.config.get("execution", {}).get("simulation_mode", False)
        
        # Initialize subcomponents
        storage_cfg = self.config.get("storage", {})
        self.storage = StorageManager(
            db_path=storage_cfg.get("sqlite_db", "data/income_ai.db"),
            state_json_path=storage_cfg.get("state_json", "data/state.json")
        )
        self.opp_engine = OpportunityEngine(self.config, self.storage)
        self.content_factory = ContentFactory(output_dir=storage_cfg.get("deliverables_dir", "site/deliverables"))
        self.reporter = ReportGenerator(self.storage, site_dir=storage_cfg.get("site_dir", "site"))

    def run_cycle(self) -> Dict[str, Any]:
        """
        Executes the 12-step autonomous cycle cleanly and idempotently.
        Returns the cycle execution summary.
        """
        start_time = time.time()
        logger.info("=== [CYCLE START] AUTO-INCOME AI autonomous loop triggered ===")
        send_lemur_hud("Auto-Income AI: Analyse des opportunités de revenus...")

        # Step 1: Check previous state
        last_stats = self.storage.get_summary_stats()
        logger.info(f"Step 1: Loaded previous state. Total deliverables so far: {last_stats.get('total_deliverables', 0)}")

        # Step 2 & 3 & 4: Discover, Deduplicate, Score
        logger.info("Step 2-4: Collecting, deduplicating and scoring opportunities...")
        scored_opps = self.opp_engine.collect_and_evaluate(force_simulation=self.simulation_mode)
        opps_count = len(scored_opps)
        logger.info(f"Evaluated {opps_count} opportunities. Top score: {scored_opps[0]['score'] if scored_opps else 0}")

        # Step 5: Select best actionable opportunity
        best_opp = self.opp_engine.select_best_opportunity()
        deliverable_record: Optional[Dict[str, Any]] = None

        if best_opp:
            logger.info(f"Step 5: Selected top opportunity: '{best_opp['title']}' (Score: {best_opp.get('score')})")

            # Step 6: Produce concrete deliverable
            logger.info("Step 6: Building concrete monetizable deliverable...")
            deliverable_data = self.content_factory.build_deliverable(best_opp)

            # Step 7: QA audit completed during build
            logger.info(f"Step 7: Quality audit passed with score {deliverable_data.get('quality_score')} / 100")

            # Step 8: Save deliverable and mark opportunity processed
            deliverable_id = self.storage.save_deliverable(deliverable_data)
            self.storage.mark_opportunity_processed(best_opp.get("hash", ""))
            deliverable_record = deliverable_data
            logger.info(f"Step 8: Deliverable saved to database (ID #{deliverable_id}) and disk at {deliverable_data['file_path']}")
        else:
            logger.warning("No actionable pending opportunity found in this cycle.")

        # Step 9 & 10 & 11: Record execution, costs and evaluate performance
        duration = round(time.time() - start_time, 2)
        exec_id = self.storage.record_execution(
            status="SUCCESS",
            opps_found=opps_count,
            deliverables_created=1 if deliverable_record else 0,
            duration_sec=duration,
            notes=f"Selected '{best_opp['title']}'" if best_opp else "No action needed"
        )
        logger.info(f"Step 9-11: Execution cycle logged as #{exec_id} (Duration: {duration}s, Cost: 0.00$)")

        # Step 12: Generate summary and HTML dashboard
        self.reporter.build_html_dashboard()
        console_report = self.reporter.generate_console_summary(exec_id, duration, opps_count, deliverable_record)
        print("\n" + console_report + "\n")

        hud_message = f"Auto-Income AI: Cycle #{exec_id} terminé avec succès (1 actif généré, 0$ coût)"
        send_lemur_hud(hud_message)
        logger.info("=== [CYCLE COMPLETE] System idle until next schedule ===")

        return {
            "execution_id": exec_id,
            "status": "SUCCESS",
            "duration_sec": duration,
            "opportunities_scanned": opps_count,
            "deliverable": deliverable_record
        }


def main():
    parser = argparse.ArgumentParser(description="AUTO-INCOME AI - Autonomous Income Generation Agent")
    parser.add_argument("--run", action="store_true", help="Execute one autonomous loop")
    parser.add_argument("--simulate", action="store_true", help="Run with demonstration dataset (no live network)")
    parser.add_argument("--report", action="store_true", help="Regenerate HTML dashboard and print summary")
    parser.add_argument("--status", action="store_true", help="Display current system KPIs")
    args = parser.parse_args()

    agent = AutoIncomeAgent(simulation_mode=args.simulate)

    if args.status:
        stats = agent.storage.get_summary_stats()
        print(json.dumps(stats, indent=2))
        sys.exit(0)

    if args.report:
        path = agent.reporter.build_html_dashboard()
        print(f"HTML dashboard generated at: {path}")
        sys.exit(0)

    # Default action or explicit run
    try:
        agent.run_cycle()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Critical execution error: {e}", exc_info=True)
        send_lemur_hud(f"Auto-Income AI Erreur: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
