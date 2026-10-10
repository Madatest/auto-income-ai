#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Opportunity Engine for AUTO-INCOME AI.
Collects, deduplicates, filters, and objectively scores online income opportunities.
Integrates live RSS/public sources with a transparent fallback for offline/simulation modes.
"""

import re
import json
import logging
import xml.etree.ElementTree as ET
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from storage import StorageManager
from monetization import MonetizationAdvisor

logger = logging.getLogger("AutoIncomeAI.OpportunityEngine")


class OpportunityEngine:
    """Discovers, normalizes, and scores business opportunities without false claims."""

    # Curated baseline opportunities for demonstration and offline fallback
    DEMO_DATASET: List[Dict[str, Any]] = [
        {
            "title": "Modèle Excel & Guide Pratique : Suivi de Trésorerie pour Freelances & PME",
            "category": "digital_product",
            "description": "Fichier Excel/Sheets automatisé pour le suivi des entrées/sorties et prévisionnel financier, prêt à la vente sur Gumroad/Ko-fi.",
            "source_id": "demo_digital_products",
            "source_url": "https://gumroad.com/discover/finance",
            "is_simulated": True,
            "observable_demand_score": 21.0,
            "speed_to_sale_score": 18.0,
            "technical_difficulty_score": 14.0
        },
        {
            "title": "Service Clé en Main : Configuration de Bot Messenger & FAQ pour Vendeurs Facebook",
            "category": "microservice_gig",
            "description": "Offre prête à l'emploi pour boutiques en ligne : configuration d'assistant automatique pour réponses instantanées et commandes.",
            "source_id": "demo_freelance_gigs",
            "source_url": "https://comeup.com/categories/marketing",
            "is_simulated": True,
            "observable_demand_score": 23.0,
            "speed_to_sale_score": 19.0,
            "technical_difficulty_score": 13.0
        },
        {
            "title": "Guide SEO & Article Pilier : Top 7 Outils Gratuits d'Automatisation en 2026",
            "category": "seo_content",
            "description": "Article approfondi à fort potentiel de trafic de recherche et affiliation logicielle, structuré avec balises H2/H3 et CTA.",
            "source_id": "demo_content_marketing",
            "source_url": "https://trends.google.com",
            "is_simulated": True,
            "observable_demand_score": 19.0,
            "speed_to_sale_score": 15.0,
            "technical_difficulty_score": 14.0
        },
        {
            "title": "Base Qualifiée B2B : 100 Agences Web & E-commerces Francophones pour Prospection",
            "category": "b2b_prospects",
            "description": "Données publiques d'entreprises cibles (site, activité, email de contact public) avec proposition personnalisée sans spam.",
            "source_id": "demo_b2b_leads",
            "source_url": "https://www.societe.com",
            "is_simulated": True,
            "observable_demand_score": 22.0,
            "speed_to_sale_score": 18.0,
            "technical_difficulty_score": 13.0
        },
        {
            "title": "Micro-Outil Web : Simulateur de Taux Horaire et Marges Freelance Autonome",
            "category": "micro_tool",
            "description": "Mini-application interactive HTML/JS autonome hébergeable sur GitHub Pages avec bouton de don Ko-fi et pack payant.",
            "source_id": "demo_micro_tools",
            "source_url": "https://news.ycombinator.com/showrss",
            "is_simulated": True,
            "observable_demand_score": 20.0,
            "speed_to_sale_score": 16.0,
            "technical_difficulty_score": 12.0
        }
    ]

    def __init__(self, config: Dict[str, Any], storage: StorageManager):
        self.config = config
        self.storage = storage
        self.scoring_weights = self.config.get("scoring", {}).get("weights", {
            "observable_demand": 25,
            "zero_start_cost": 20,
            "speed_to_first_sale": 20,
            "technical_feasibility": 15,
            "madagascar_payment_readiness": 20
        })

    def fetch_rss_feed(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parses a public XML/RSS feed cleanly without external heavy dependencies."""
        url = source.get("url", "")
        source_id = source.get("id", "rss")
        default_category = source.get("category", "digital_product")
        items = []

        headers = {
            "User-Agent": "AutoIncomeAI-Bot/1.0 (+https://github.com/auto-income-ai)"
        }
        req = Request(url, headers=headers)
        timeout = self.config.get("execution", {}).get("request_timeout_seconds", 6)

        try:
            with urlopen(req, timeout=timeout) as response:
                content = response.read()
                root = ET.fromstring(content)

                # Standard RSS 2.0 <item> or Atom <entry>
                entries = root.findall(".//item")
                if not entries:
                    entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")

                for entry in entries[:6]:  # Limit per feed to prevent quota spikes
                    title_elem = entry.find("title") or entry.find("{http://www.w3.org/2005/Atom}title")
                    link_elem = entry.find("link") or entry.find("{http://www.w3.org/2005/Atom}link")
                    desc_elem = entry.find("description") or entry.find("{http://www.w3.org/2005/Atom}summary")

                    title = title_elem.text.strip() if (title_elem is not None and title_elem.text) else ""
                    link = ""
                    if link_elem is not None:
                        link = link_elem.text or link_elem.attrib.get("href", "")
                    desc = desc_elem.text.strip() if (desc_elem is not None and desc_elem.text) else ""

                    # Clean basic HTML tags from descriptions
                    desc = re.sub(r"<[^>]+>", "", desc)

                    if title and len(title) > 6:
                        items.append({
                            "title": title,
                            "category": default_category,
                            "description": desc[:300] if desc else "Opportunité issue d'un flux public temps réel.",
                            "source_id": source_id,
                            "source_url": link or url,
                            "is_simulated": False
                        })
        except (URLError, HTTPError, TimeoutError, ET.ParseError, Exception) as err:
            logger.warning(f"Could not fetch feed {source_id} ({url}): {err}")

        return items

    def score_opportunity(self, opp: Dict[str, Any]) -> Dict[str, Any]:
        """
        Computes an objective, documented score (0-100) based on 5 strict criteria:
        1. Observable demand & competition (0-25)
        2. Zero startup cost (0-20) -> Always 20 because initial budget is 0 USD
        3. Speed to first potential sale (0-20)
        4. Technical accessibility (0-15)
        5. Madagascar payment readiness (0-20)
        """
        category = opp.get("category", "digital_product")
        
        # 1. Observable demand (0-25)
        demand = float(opp.get("observable_demand_score", 18.0))
        # Boost if contains high-intent words
        title_lower = opp.get("title", "").lower()
        if any(w in title_lower for w in ["bot", "guide", "template", "lead", "prospect", "outil", "service", "argent", "vente"]):
            demand = min(25.0, demand + 2.5)

        # 2. Zero startup cost (0-20)
        # By architecture, our engine only builds zero-capital solutions
        zero_cost = 20.0

        # 3. Speed to first sale (0-20)
        # Direct microservices and ready-to-sell digital templates convert fastest
        speed_map = {
            "microservice_gig": 19.0,
            "b2b_prospects": 18.0,
            "digital_product": 17.0,
            "seo_content": 14.0,
            "micro_tool": 13.0
        }
        speed = float(opp.get("speed_to_sale_score", speed_map.get(category, 15.0)))

        # 4. Technical accessibility (0-15)
        tech_map = {
            "digital_product": 14.5,
            "seo_content": 14.0,
            "microservice_gig": 13.5,
            "b2b_prospects": 13.0,
            "micro_tool": 12.0
        }
        tech = float(opp.get("technical_difficulty_score", tech_map.get(category, 13.0)))

        # 5. Madagascar payment readiness (0-20)
        monetization_info = MonetizationAdvisor.evaluate_opportunity_monetization(category)
        payment_readiness = monetization_info.get("madagascar_readiness_score", 18.0)

        total_score = round(demand + zero_cost + speed + tech + payment_readiness, 1)

        breakdown = {
            "observable_demand": round(demand, 1),
            "zero_start_cost": round(zero_cost, 1),
            "speed_to_first_sale": round(speed, 1),
            "technical_feasibility": round(tech, 1),
            "madagascar_payment_readiness": round(payment_readiness, 1),
            "max_possible": 100.0
        }

        opp["score"] = total_score
        opp["score_breakdown"] = breakdown
        opp["hash"] = StorageManager.compute_hash(opp.get("source_id", "src"), opp.get("title", ""))
        return opp

    def collect_and_evaluate(self, force_simulation: bool = False) -> List[Dict[str, Any]]:
        """Collects opportunities from live sources, applies fallback if offline, and saves deduplicated items."""
        raw_items: List[Dict[str, Any]] = []

        if not force_simulation:
            for src in self.config.get("sources", []):
                if src.get("enabled", True):
                    feed_items = self.fetch_rss_feed(src)
                    raw_items.extend(feed_items)

        # Mode simulation / fallback : UNIQUEMENT si explicitement activé
        if force_simulation or (self.config.get("execution", {}).get("allow_offline_fallback", False) and len(raw_items) < 2):
            for demo_opp in self.DEMO_DATASET:
                raw_items.append(dict(demo_opp))

        scored_items = []
        newly_saved_count = 0

        for item in raw_items:
            scored = self.score_opportunity(item)
            is_new = self.storage.save_opportunity(scored)
            if is_new:
                newly_saved_count += 1
            scored_items.append(scored)

        # Sort by highest score
        scored_items.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return scored_items

    def select_best_opportunity(self) -> Optional[Dict[str, Any]]:
        """Selects the highest scoring pending opportunity."""
        pending = self.storage.get_pending_opportunities(limit=1)
        if pending:
            return pending[0]

        # If no pending in database, collect fresh batch
        fresh = self.collect_and_evaluate()
        if fresh:
            return fresh[0]
        return None
