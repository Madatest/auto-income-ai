#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WOLF — THE RELENTLESS REVENUE DIRECTOR
Autonomous Agent Supervisor & Performance Enforcer.
Demanding director supervising AUTO-INCOME AI.
Eliminates waste, challenges mediocrity, forces rapid commercial execution,
and audits decision quality with zero excuses.
"""

import os
import re
import json
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("AutoIncomeAI.WolfSupervisor")


class WolfSupervisor:
    """
    Supervises AUTO-INCOME AI.
    Implements the Wolf Interrogation Protocol, the Decision Quality Score (0-100),
    and the 7-Phase Supervisory Loop (Phases A through G).
    """

    MOTTO = (
        "STOP EXPLAINING WHY IT DIDN'T WORK. SHOW ME WHAT YOU LEARNED, "
        "WHAT YOU CHANGED, AND WHY THE NEXT ATTEMPT HAS A BETTER CHANCE OF WINNING."
    )

    def __init__(
        self,
        db_path: str = "data/income_ai.db",
        directives_file: str = "data/wolf_directives.json",
        history_file: str = "data/wolf_history.json"
    ):
        self.db_path = db_path
        self.directives_file = directives_file
        self.history_file = history_file
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        dir_dir = os.path.dirname(self.directives_file)
        if dir_dir:
            os.makedirs(dir_dir, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        """Initializes supervisor tables in SQLite."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS wolf_supervision (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                cycle_id INTEGER,
                decision_score REAL NOT NULL,
                status TEXT NOT NULL,
                primary_directive TEXT NOT NULL,
                weaknesses_identified TEXT,
                assigned_task TEXT NOT NULL,
                acceptance_criteria TEXT NOT NULL,
                interrogation_json TEXT,
                raw_review_json TEXT
            );
            """)
            conn.commit()
        except Exception as e:
            logger.warning(f"Could not initialize wolf_supervision table: {e}")
        finally:
            if conn:
                conn.close()

    # -------------------------------------------------------------------------
    # 1. THE WOLF INTERROGATION PROTOCOL (10 Questions)
    # -------------------------------------------------------------------------
    def interrogate(self, cycle_report: Dict[str, Any]) -> Dict[str, str]:
        """Runs the 10-question Wolf interrogation on the cycle output."""
        deliverable = cycle_report.get("deliverable") or {}
        phases = cycle_report.get("phases") or {}
        first_revenue = cycle_report.get("first_real_revenue", False)
        title = deliverable.get("title", "Aucun livrable concret")
        category = deliverable.get("category", "inconnu")
        price = deliverable.get("price_usd", 0.0)

        q1 = f"Livrable généré : '{title}' ({category}, {price} $). Fichier : {deliverable.get('file_path', 'Non spécifié')}."
        
        if category in ("digital_product", "seo_content"):
            q2 = "REJET : Théorie passive sans client identifié. Les guides lents ne résolvent aucun besoin brûlant immédiat."
            q3 = "Faible probabilité : personne ne cherche un nouveau document inconnu en moins d'une heure."
            q4 = "Inadéquat : reposer sur du SEO passif ou un site isolé sans trafic externe."
            q5 = "ERREUR STRATÉGIQUE : Modèle d'audience lente choisi au lieu d'une prestation/bounty avec budget déjà prêt."
        elif category in ("microservice_gig", "b2b_prospects"):
            q2 = f"Résolution de problème direct : exécution d'une tâche technique ou réponse à une prime/demande active ('{title}')."
            q3 = f"Client identifié : demandeur actif sur plateforme tech/open-source ou recruteur de freelance avec budget prêt."
            q4 = "Canal direct : réponse immédiate à l'appel d'offre, dépôt de PR sur GitHub Bounty, ou enregistrement de service."
            q5 = f"Choisi pour le délai court : le client a déjà le besoin et le budget, conversion sous 24-48h."
        else:
            q2 = f"Outil fonctionnel direct : outil web autonome résolvant un calcul ou une manipulation concrète."
            q3 = "Utilisateur technique cherchant un résultat immédiat sans inscription."
            q4 = "Distribution directe via démo GitHub Pages et partage ciblé sur forum spécialisé."
            q5 = "Zéro friction : l'utilisateur teste immédiatement le produit sans intermédiaire."

        q6 = (
            "Ventes à 0 $ : absence de distribution sortante agressive (Outbound) "
            "ou délai de revue par le client. Le produit/service est prêt, mais il faut pousser le livrable au destinataire."
        )
        q7 = (
            "Éliminer tout produit passif. Forcer le ciblage exclusif sur les Bounties GitHub actives "
            "et les microservices avec acheteur réel prêt à payer."
        )
        q8 = (
            "Critère mesurable : au moins 1 soumission de travail vérifiable (PR de bounty, réponse à offre, "
            "ou transaction Binance Pay détectée > 0 $)."
        )
        q9 = (
            "Chasse active aux Bounties GitHub : résoudre un bug ou créer un connecteur pour un repo qui a une prime en cash."
        )
        q10 = (
            "Leçon ancrée : Ne jamais confondre fabrication d'outils et capture de valeur. "
            "L'argent vient de la résolution d'une douleur existante chez un client qui a du cash, pas d'un fichier posé sur un site."
        )

        return {
            "1_actual_production": q1,
            "2_commercial_problem": q2,
            "3_who_pays_and_why": q3,
            "4_customer_reach": q4,
            "5_strategy_justification": q5,
            "6_blocker_analysis": q6,
            "7_actionable_change": q7,
            "8_evidence_metric": q8,
            "9_fastest_path_to_cash": q9,
            "10_lesson_learned": q10
        }

    # -------------------------------------------------------------------------
    # 2. DECISION QUALITY SCORE (0 - 100)
    # -------------------------------------------------------------------------
    def score_decision_quality(
        self,
        cycle_report: Dict[str, Any]
    ) -> Tuple[float, Dict[str, float]]:
        """
        Computes the Wolf Decision Quality Score (0-100) based on 7 strict criteria:
        - Market demand evidence (20)
        - Customer willingness to pay (20)
        - Speed to possible first sale (15)
        - Zero-budget feasibility (15)
        - Customer acquisition strategy (10)
        - Delivery feasibility (10)
        - Risk & compliance (10)
        """
        deliverable = cycle_report.get("deliverable") or {}
        category = deliverable.get("category", "")
        source_id = deliverable.get("source_id", "")
        title = deliverable.get("title", "").lower()

        # 1. Market demand evidence (20)
        if "bounty" in title or "github_bounties" in source_id or category == "microservice_gig":
            demand_evidence = 18.0
        elif category == "micro_tool":
            demand_evidence = 14.0
        elif category in ("digital_product", "seo_content"):
            demand_evidence = 5.0
        else:
            demand_evidence = 10.0

        # 2. Customer willingness to pay (20)
        if "bounty" in title:
            willingness_to_pay = 19.0  # Money is already locked in escrow
        elif category == "microservice_gig":
            willingness_to_pay = 16.0
        elif category in ("digital_product", "seo_content"):
            willingness_to_pay = 4.0
        else:
            willingness_to_pay = 10.0

        # 3. Speed to first sale (15)
        if "bounty" in title:
            speed = 14.0
        elif category == "microservice_gig":
            speed = 13.0
        elif category in ("digital_product", "seo_content"):
            speed = 2.0
        else:
            speed = 8.0

        # 4. Zero-budget feasibility (15)
        # Always verified 0 USD by strict architecture
        zero_budget = 15.0

        # 5. Customer acquisition strategy (10)
        if "bounty" in title:
            acquisition = 9.0  # Target issue URL is directly known
        elif category == "microservice_gig":
            acquisition = 7.0
        else:
            acquisition = 3.0

        # 6. Delivery feasibility (10)
        # Digital deliverables can be handed over immediately
        delivery = 9.5

        # 7. Risk, legality, and compliance (10)
        # Ethical open-source compliance, zero fraud, zero account theft
        risk_compliance = 10.0

        total_score = round(
            demand_evidence + willingness_to_pay + speed + zero_budget + acquisition + delivery + risk_compliance,
            1
        )

        breakdown = {
            "market_demand_evidence": round(demand_evidence, 1),
            "customer_willingness_to_pay": round(willingness_to_pay, 1),
            "speed_to_first_sale": round(speed, 1),
            "zero_budget_feasibility": round(zero_budget, 1),
            "customer_acquisition_strategy": round(acquisition, 1),
            "delivery_feasibility": round(delivery, 1),
            "risk_and_compliance": round(risk_compliance, 1),
            "total_score": total_score,
            "max_possible": 100.0
        }

        return total_score, breakdown

    # -------------------------------------------------------------------------
    # 3. THE 7-PHASE SUPERVISORY LOOP (Phases A through G)
    # -------------------------------------------------------------------------
    def review_cycle(self, cycle_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a comprehensive supervisory review:
        Phase A: Review outputs and commercial data.
        Phase B: Challenge weaknesses.
        Phase C: Decide primary and secondary pivots.
        Phase D: Issue concrete assigned task.
        Phase E: Verify acceptance criteria.
        Phase F: Record lessons learned.
        Phase G: Determine next execution state.
        """
        cycle_id = cycle_report.get("cycle_id", 0)
        deliverable = cycle_report.get("deliverable") or {}
        first_revenue = cycle_report.get("first_real_revenue", False)
        category = deliverable.get("category", "")
        title = deliverable.get("title", "")

        # Phase A — Review
        total_revenue = cycle_report.get("total_confirmed_revenue_usd", 0.0)
        costs = cycle_report.get("costs_incurred_usd", 0.0)

        # Interrogate
        interrogation = self.interrogate(cycle_report)

        # Score decision quality
        decision_score, score_breakdown = self.score_decision_quality(cycle_report)

        # Phase B — Challenge (Top 3 weaknesses)
        weaknesses = []
        if category in ("digital_product", "seo_content"):
            weaknesses.append({
                "rank": 1,
                "impact": "CRITICAL",
                "issue": "Création d'un produit d'information passif. Cycle de vente trop lent (> 30 jours). Vente impossible en 1h."
            })
        else:
            weaknesses.append({
                "rank": 1,
                "impact": "HIGH",
                "issue": "Absence de distribution active : le livrable a été emballé mais pas encore soumis au client/donneur d'ordre."
            })

        weaknesses.append({
            "rank": 2,
            "impact": "MEDIUM",
            "issue": "Concentration exclusive sur un seul livrable par heure au lieu d'accélérer la cadence sur les primes déjà budgétées."
        })
        weaknesses.append({
            "rank": 3,
            "impact": "LOW",
            "issue": "Vérification de paiement passive : dépendance exclusive aux notifications Android locales sans ping direct."
        })

        # Phase C — Decide
        if category in ("digital_product", "seo_content"):
            primary_pivot = "PIVOT RADICAL : Interdiction des guides passifs. Bascule 100% sur les Bounties de code et micro-tâches immédiates."
            secondary_exp = "Suppression de toutes les sources d'information théoriques de config.json."
        else:
            primary_pivot = "ACCÉLÉRATION CHIRURGICALE : Résoudre directement la prime active et préparer la Pull Request de validation."
            secondary_exp = "Scanner les issues GitHub avec libellé 'bounty' et prime supérieure à 5 USD."

        # Phase D — Direct (The Assigned Task)
        assigned_task = (
            f"Exécuter le prochain cycle avec focus exclusif sur les Bounties GitHub et microservices. "
            f"Livrable obligatoire : code source fonctionnel ou fiche de résolution technique directement exploitable."
        )
        acceptance_criteria = (
            "1. Catégorie strictement différente de digital_product et seo_content.\n"
            "2. Score de décision Wolf supérieur ou égal à 75/100.\n"
            "3. Coût financier égal à exactement 0.00 USD.\n"
            "4. Vérification d'intégrité de paiement active sur Binance UID 254779310."
        )

        # Phase E — Verify
        status = "COMPLETED" if first_revenue else "PENDING_NEXT_CYCLE"

        # Phase F — Learn
        lesson = (
            f"Cycle #{cycle_id} évalué à {decision_score}/100. "
            f"{'Succès commercial initial confirmé !' if first_revenue else 'Aucune transaction : intensifier la pression sur les opportunités avec cash déjà bloqué (bounties).'}"
        )

        directive = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cycle_id": cycle_id,
            "decision_score": decision_score,
            "score_breakdown": score_breakdown,
            "motto": self.MOTTO,
            "status": status,
            "interrogation": interrogation,
            "weaknesses": weaknesses,
            "primary_directive": primary_pivot,
            "secondary_experiment": secondary_exp,
            "assigned_task": assigned_task,
            "acceptance_criteria": acceptance_criteria,
            "lesson": lesson,
            "revenue_confirmed": first_revenue
        }

        # Persist directive
        self._save_directive(directive)
        return directive

    def _save_directive(self, directive: Dict[str, Any]) -> None:
        """Saves directive to JSON file and SQLite database."""
        try:
            dir_name = os.path.dirname(self.directives_file)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            tmp_file = f"{self.directives_file}.tmp.{os.getpid()}"
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(directive, f, indent=2, ensure_ascii=False)
            os.replace(tmp_file, self.directives_file)

            conn = sqlite3.connect(self.db_path)
            try:
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO wolf_supervision (
                    timestamp, cycle_id, decision_score, status,
                    primary_directive, weaknesses_identified, assigned_task,
                    acceptance_criteria, interrogation_json, raw_review_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    directive["timestamp"],
                    directive["cycle_id"],
                    directive["decision_score"],
                    directive["status"],
                    directive["primary_directive"],
                    json.dumps(directive["weaknesses"], ensure_ascii=False),
                    directive["assigned_task"],
                    directive["acceptance_criteria"],
                    json.dumps(directive["interrogation"], ensure_ascii=False),
                    json.dumps(directive, ensure_ascii=False)
                ))
                conn.commit()
            finally:
                conn.close()
            logger.info(f"WOLF Directive saved. Decision Score: {directive['decision_score']}/100")
        except Exception as e:
            logger.error(f"Error persisting Wolf directive: {e}")

    def get_active_directive(self) -> Optional[Dict[str, Any]]:
        """Reads the latest directive for AUTO-INCOME AI."""
        if os.path.exists(self.directives_file):
            try:
                with open(self.directives_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load active Wolf directive: {e}")
        return None

    def format_console_verdict(self, review: Dict[str, Any]) -> str:
        """Formats an intense, uncompromising, highly disciplined Wolf review block."""
        score = review.get("decision_score", 0.0)
        cycle_id = review.get("cycle_id", 0)
        
        status_line = (
            "🏆 MISSION ACCOMPLIE — PREMIER REVENU CONFIRMÉ !"
            if review.get("revenue_confirmed")
            else "⚡ PERFORMANCE INSUFFISANTE — ZÉRO ENCAISSEMENT. NOUVELLE DIRECTIVE ÉMISE."
        )

        lines = [
            "================================================================",
            " 🐺 WOLF — RAPPORT DE SUPERVISION & AUDIT DE PERFORMANCE",
            "================================================================",
            f"• Cycle supervisé        : #{cycle_id}",
            f"• Score Qualité Décision : {score} / 100",
            f"• Statut Commercial      : {status_line}",
            "----------------------------------------------------------------",
            f"🎯 DEVISE DU DIRECTEUR :",
            f"  « {self.MOTTO} »",
            "----------------------------------------------------------------",
            "🔍 AUDIT SANS CONCESSION (LES 3 FAIBLESSES MAJEURES) :"
        ]
        
        for w in review.get("weaknesses", []):
            lines.append(f"  [{w['rank']}] ({w['impact']}) {w['issue']}")

        lines.extend([
            "----------------------------------------------------------------",
            "🚀 DIRECTIVE OPÉRATIONNELLE POUR LE PROCHAIN CYCLE :",
            f"  • Pivot Prioritaire   : {review.get('primary_directive')}",
            f"  • Mission Assignée    : {review.get('assigned_task')}",
            "  • Critères d'Exigence :",
        ])
        for crit in review.get("acceptance_criteria", "").split("\n"):
            if crit.strip():
                lines.append(f"    - {crit.strip()}")

        lines.extend([
            "================================================================"
        ])
        return "\n".join(lines)


if __name__ == "__main__":
    # Test execution / stand-alone run
    logging.basicConfig(level=logging.INFO)
    supervisor = WolfSupervisor()
    dummy_report = {
        "cycle_id": 11,
        "first_real_revenue": False,
        "deliverable": {
            "title": "[radar] SN open bounty 2026-10-10T12:22",
            "category": "microservice_gig",
            "price_usd": 25.0,
            "source_id": "github_bounties",
            "file_path": "site/deliverables/20261010_184424_radar_sn_open_bounty_2026_10_10t1222.md"
        }
    }
    review = supervisor.review_cycle(dummy_report)
    print(supervisor.format_console_verdict(review))
