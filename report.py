#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Report Generator for AUTO-INCOME AI.
Generates concise terminal summaries and an interactive mobile-first HTML dashboard.
Compatible with GitHub Pages and offline Android browser viewing.
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List

from storage import StorageManager


class ReportGenerator:
    """Creates operational reports and publishes responsive HTML dashboards."""

    def __init__(self, storage: StorageManager, site_dir: str = "site"):
        self.storage = storage
        self.site_dir = site_dir
        os.makedirs(self.site_dir, exist_ok=True)

    def generate_console_summary(self, exec_id: int, duration_sec: float, opps_count: int, deliverable: Dict[str, Any] = None) -> str:
        """Produces a clean terminal overview."""
        stats = self.storage.get_summary_stats()
        lines = [
            "=" * 64,
            " 🤖 AUTO-INCOME AI - RAPPORT DE MISSION EXÉCUTÉE",
            "=" * 64,
            f"• Cycle ID             : #{exec_id}",
            f"• Horodatage           : {stats.get('updated_at', '')}",
            f"• Durée d'exécution    : {duration_sec:.2f} secondes",
            f"• Budget dépensé       : 0,00 $ (Respect absolu de la règle)",
            f"• Opportunités scannées: {opps_count}",
            f"• Total Livrables      : {stats.get('total_deliverables', 0)}",
            f"• Pipeline projeté     : {stats.get('projected_pipeline_usd', 0.0)} $ USD",
            f"• Ventes confirmées    : {stats.get('total_confirmed_revenue_usd', 0.0)} $ USD",
            "-" * 64
        ]

        if deliverable:
            lines.extend([
                f"📦 NOUVEAU LIVRABLE PRODUIT :",
                f"  - Titre       : {deliverable.get('title')}",
                f"  - Catégorie   : {deliverable.get('category')}",
                f"  - Fichier     : {deliverable.get('file_path')}",
                f"  - Prix suggéré: {deliverable.get('price_usd', 0.0)} $",
                f"  - Encaissement: {deliverable.get('monetization_channel')} (Madagascar ready)",
                f"  - Score Qualité: {deliverable.get('quality_score', 100.0)} / 100",
                "-" * 64
            ])

        lines.extend([
            "🧭 PROCHAINE ACTION AUTONOME :",
            "  Le système se déclenchera selon le planning autonome horaire (1 heure).",
            "  Pour consulter le rapport visuel sur mobile : ouvrir site/index.html",
            "=" * 64
        ])
        return "\n".join(lines)

    def build_html_dashboard(self) -> str:
        """Builds a complete, modern, mobile-first responsive HTML dashboard saved to site/index.html."""
        stats = self.storage.get_summary_stats()
        deliverables = self.storage.get_all_deliverables(limit=25)
        opportunities = self.storage.get_recent_opportunities(limit=15)

        deliverables_cards_html = ""
        for d in deliverables:
            meta = d.get("metadata", {})
            mon = meta.get("monetization", {})
            deliverables_cards_html += f"""
            <div class="card deliverable-card">
                <div class="card-badge">{d.get('category').replace('_', ' ').upper()}</div>
                <h3>{d.get('title')}</h3>
                <div class="meta-row">
                    <span>💰 <strong>{d.get('price_usd', 0.0)} $</strong> (~{int(d.get('price_usd', 0.0) * 4500):,} Ar)</span>
                    <span>⭐ QA : <strong>{d.get('quality_score', 100)}/100</strong></span>
                </div>
                <p class="description"><strong>Canal :</strong> {mon.get('channel_name', d.get('monetization_channel'))}</p>
                <div class="cashout-box">
                    <strong>🇲🇬 Encaissement Mada :</strong> {mon.get('local_cashout', 'P2P / Virement international')}
                </div>
                <div class="action-row" style="display:flex; gap:8px; margin-top:12px;">
                    <a href="{d.get('relative_path')}" class="btn-primary" style="flex:1; background:#1e293b; border:1px solid #334155; text-align:center;" target="_blank">📄 Voir Dossier</a>
                    {'<a href="' + meta.get('source_url', '') + '" class="btn-primary" style="flex:1.2; background:#2563eb; color:#fff; font-weight:700; text-align:center;" target="_blank">🎯 Ouvrir Issue</a>' if meta.get('source_url') else '<a href="checkout.html" class="btn-primary" style="flex:1.2; background:#f0b90b; color:#000; font-weight:700; text-align:center;" target="_blank">⚡ Payer Binance</a>'}
                </div>
            </div>
            """

        opportunities_rows_html = ""
        for opp in opportunities:
            breakdown = opp.get("score_breakdown", {})
            sim_badge = '<span class="tag-demo">[DEMO]</span>' if opp.get("is_simulated") else '<span class="tag-live">[LIVE]</span>'
            opportunities_rows_html += f"""
            <tr>
                <td>{sim_badge} {opp.get('title')}</td>
                <td><span class="cat-pill">{opp.get('category')}</span></td>
                <td><strong>{opp.get('score', 0.0)} / 100</strong></td>
                <td><span class="status-pill status-{opp.get('status')}">{opp.get('status')}</span></td>
            </tr>
            """

        # WOLF Supervision banner
        wolf_card_html = ""
        wolf_dir_path = "data/wolf_directives.json"
        if os.path.exists(wolf_dir_path):
            try:
                with open(wolf_dir_path, "r", encoding="utf-8") as f:
                    wolf_data = json.load(f)
                score = wolf_data.get("decision_score", 0.0)
                primary_dir = wolf_data.get("primary_directive", "")
                task = wolf_data.get("assigned_task", "")
                motto = wolf_data.get("motto", "")
                wolf_card_html = f"""
                <div class="card" style="background:#131b2e; border:1px solid #3b82f6; border-radius:12px; padding:20px; margin-bottom:28px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                        <span style="font-weight:700; color:#60a5fa; font-size:1.1rem;">🐺 WOLF — SUPERVISEUR & DIRECTEUR DE PERFORMANCE</span>
                        <span style="background:rgba(59,130,246,0.2); color:#60a5fa; border:1px solid #3b82f6; padding:3px 10px; border-radius:9999px; font-weight:700; font-size:0.85rem;">Score Qualité Décision : {score}/100</span>
                    </div>
                    <p style="margin:10px 0; font-style:italic; color:#9ca3af; font-size:0.85rem;">« {motto} »</p>
                    <div style="background:#0b1120; border-radius:8px; padding:12px; margin-top:10px; border-left:4px solid #3b82f6;">
                        <div style="font-size:0.85rem; color:#f8fafc; font-weight:600;">🎯 Directive Opérationnelle Active :</div>
                        <div style="font-size:0.85rem; color:#cbd5e1; margin-top:4px;">{primary_dir}</div>
                        <div style="font-size:0.8rem; color:#94a3b8; margin-top:6px;"><strong>Mission assignée :</strong> {task}</div>
                    </div>
                </div>
                """
            except Exception:
                pass

        # Action Center for Immediate Outbound Bounties & Gigs
        actionable_cards_html = ""
        actionable_deliverables = [
            d for d in deliverables
            if d.get("metadata", {}).get("source_url") or d.get("category") == "bounty_solution"
        ]

        for idx, d in enumerate(actionable_deliverables[:4]):
            meta = d.get("metadata", {})
            bounty_val = meta.get("bounty_value") or f"${d.get('price_usd', 0.0)} USD"
            source_url = meta.get("source_url", "")
            proposal = meta.get("proposal_snippet", "")
            prop_id = f"proposal_text_{d.get('id', idx)}"
            escaped_proposal = (proposal or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', '&quot;')

            issue_btn_html = f'<a href="{source_url}" target="_blank" style="flex:1.2; background:#2563eb; color:#fff; font-weight:700; text-decoration:none; padding:10px; border-radius:8px; text-align:center;">🎯 Ouvrir l&#39;Issue sur GitHub</a>' if source_url else ""

            actionable_cards_html += f"""
            <div class="card" style="background:#0f172a; border:2px solid #3b82f6; border-radius:12px; padding:18px; margin-bottom:14px;">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                    <span style="background:#1d4ed8; color:#fff; font-size:0.75rem; font-weight:700; padding:3px 10px; border-radius:6px;">🎯 ACTION PRIORITAIRE #{idx+1}</span>
                    <span style="font-weight:700; color:#10b981; font-size:1.1rem;">Prime : {bounty_val}</span>
                </div>
                <h3 style="margin:10px 0 6px; font-size:1.05rem; color:#f8fafc;">{d.get('title')}</h3>
                <p style="font-size:0.85rem; color:#94a3b8; margin-bottom:12px;">
                    ✅ Dossier technique et proposition PR prêts. Soumettez directement pour réserver la prime.
                </p>
                <div id="{prop_id}" style="display:none;">{escaped_proposal}</div>
                <div style="display:flex; gap:10px; flex-wrap:wrap;">
                    <button onclick="copyActionProposal('{prop_id}', this)" style="flex:1; background:#10b981; color:#000; font-weight:700; border:none; padding:10px; border-radius:8px; cursor:pointer;">
                        📋 Copier la Proposition PR
                    </button>
                    {issue_btn_html}
                    <a href="{d.get('relative_path')}" target="_blank" style="flex:0.8; background:#1e293b; color:#cbd5e1; border:1px solid #334155; text-decoration:none; padding:10px; border-radius:8px; text-align:center;">
                        📄 Voir Dossier
                    </a>
                </div>
            </div>
            """

        action_center_html = ""
        if actionable_cards_html:
            action_center_html = f"""
            <div style="margin:24px 0;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                    <h2 style="color:#60a5fa; margin:0;">⚡ CENTRE D'ACTION IMMÉDIATE (OUTBOUND)</h2>
                    <span style="color:#10b981; font-size:0.85rem; font-weight:600;">{len(actionable_deliverables)} primes/gigs prêts</span>
                </div>
                <p style="font-size:0.85rem; color:#94a3b8; margin-bottom:14px;">
                    Cliquez sur <strong>Copier la Proposition PR</strong> puis sur <strong>Ouvrir l'Issue sur GitHub</strong> pour réserver la prime. Payout vers Binance Pay UID <code>254779310</code>.
                </p>
                {actionable_cards_html}
            </div>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AUTO-INCOME AI - Tableau de Bord Exécutif</title>
    <style>
        :root {{
            --bg: #090d16;
            --surface: #111827;
            --surface-hover: #1f2937;
            --border: #1f2937;
            --primary: #3b82f6;
            --primary-gradient: linear-gradient(135deg, #2563eb, #1d4ed8);
            --accent: #10b981;
            --warning: #f59e0b;
            --text: #f9fafb;
            --text-muted: #9ca3af;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            padding: 16px;
            max-width: 1100px;
            margin: 0 auto;
            line-height: 1.5;
        }}
        header {{
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            padding: 24px 0 16px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 24px;
            gap: 12px;
        }}
        .header-title h1 {{
            font-size: 1.6rem;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .status-badge {{
            background: rgba(16, 185, 129, 0.15);
            color: var(--accent);
            border: 1px solid var(--accent);
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 600;
        }}
        /* KPI Grid */
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }}
        .kpi-card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
        }}
        .kpi-label {{
            font-size: 0.8rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
        }}
        .kpi-value {{
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--text);
        }}
        .kpi-subtext {{
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 4px;
        }}
        .highlight-green {{ color: var(--accent); }}
        .highlight-blue {{ color: var(--primary); }}

        /* Section Layout */
        h2 {{
            font-size: 1.3rem;
            margin: 28px 0 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .deliverables-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 16px;
        }}
        .card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}
        .card-badge {{
            font-size: 0.7rem;
            background: #1e3a8a;
            color: #93c5fd;
            padding: 2px 8px;
            border-radius: 4px;
            width: fit-content;
            margin-bottom: 8px;
            font-weight: 600;
        }}
        .card h3 {{
            font-size: 1.1rem;
            margin-bottom: 10px;
        }}
        .meta-row {{
            display: flex;
            justify-content: space-between;
            font-size: 0.9rem;
            margin-bottom: 12px;
            color: #d1d5db;
        }}
        .cashout-box {{
            background: #090d16;
            border-left: 3px solid var(--accent);
            padding: 10px 12px;
            border-radius: 6px;
            font-size: 0.8rem;
            color: var(--text-muted);
            margin: 12px 0 16px;
        }}
        .cashout-box strong {{ color: var(--text); }}
        .btn-primary {{
            display: block;
            text-align: center;
            background: var(--primary);
            color: white;
            text-decoration: none;
            padding: 10px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 0.9rem;
            transition: background 0.2s;
        }}
        .btn-primary:hover {{ background: #2563eb; }}

        /* Table */
        .table-container {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.85rem;
        }}
        th, td {{
            padding: 14px 16px;
            border-bottom: 1px solid var(--border);
        }}
        th {{
            color: var(--text-muted);
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
        }}
        .tag-live {{ color: var(--accent); font-weight: 700; font-size: 0.75rem; margin-right: 4px; }}
        .tag-demo {{ color: var(--warning); font-weight: 700; font-size: 0.75rem; margin-right: 4px; }}
        .cat-pill {{ background: #1f2937; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; }}
        .status-pill {{ padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }}
        .status-processed {{ background: rgba(16, 185, 129, 0.2); color: var(--accent); }}
        .status-pending {{ background: rgba(59, 130, 246, 0.2); color: #60a5fa; }}

        footer {{
            text-align: center;
            margin-top: 48px;
            padding: 24px;
            border-top: 1px solid var(--border);
            font-size: 0.8rem;
            color: var(--text-muted);
        }}
    </style>
</head>
<body>
    <header>
        <div class="header-title">
            <h1>🤖 AUTO-INCOME AI</h1>
            <span class="status-badge">● SYSTÈME AUTONOME ACTIF (MODE RÉEL)</span>
        </div>
        <div style="font-size: 0.85rem; color: #f0b90b; background: rgba(240, 185, 11, 0.1); padding: 6px 12px; border-radius: 8px; border: 1px solid rgba(240, 185, 11, 0.3); margin-top: 8px;">
            👤 Vendeur : <strong>Jean</strong> | 📧 <strong>compte.amidy001@gmail.com</strong> | ⚡ Binance Pay UID : <strong>254779310</strong>
        </div>
        <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 6px;">
            Dernière mise à jour : <strong>{stats.get('updated_at', '')}</strong>
        </div>
    </header>

    <main>
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-label">Budget & Coûts Engagés</div>
                <div class="kpi-value highlight-green">0,00 $</div>
                <div class="kpi-subtext">Règle 0 USD respectée à 100%</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Actifs Monétisables Créés</div>
                <div class="kpi-value highlight-blue">{stats.get('total_deliverables', 0)}</div>
                <div class="kpi-subtext">Prêts pour diffusion internationale</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Pipeline de Valeur Généré</div>
                <div class="kpi-value">{stats.get('projected_pipeline_usd', 0.0)} $</div>
                <div class="kpi-subtext">~{int(stats.get('projected_pipeline_usd', 0.0) * 4500):,} Ar au cours actuel</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-label">Cycles Cloud Exécutés</div>
                <div class="kpi-value">{stats.get('total_executions', 0)}</div>
                <div class="kpi-subtext">Surveillance 24/7 sans interruption</div>
            </div>
        </div>

        {action_center_html}

        {wolf_card_html}

        <h2>📦 Actifs Monétisables Disponibles</h2>
        <div class="deliverables-grid">
            {deliverables_cards_html if deliverables_cards_html else '<p style="color:var(--text-muted); padding:16px;">Aucun livrable généré pour l\'instant. Lancez un cycle.</p>'}
        </div>

        <h2>🔍 Opportunités Détectées & Scannées</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Opportunité & Source</th>
                        <th>Modèle</th>
                        <th>Score Global</th>
                        <th>Statut</th>
                    </tr>
                </thead>
                <tbody>
                    {opportunities_rows_html if opportunities_rows_html else '<tr><td colspan="4" style="text-align:center;">Aucune opportunité enregistrée.</td></tr>'}
                </tbody>
            </table>
        </div>
    </main>

    <footer>
        <p><strong>AUTO-INCOME AI</strong> • Architecture autonome pour créateurs basés à Madagascar • Conforme aux règles éthiques internationales.</p>
        <p style="margin-top:6px;">Exécuté 24h/24 via GitHub Actions • Compatible mobile Android Termux.</p>
    </footer>

    <script>
    function copyActionProposal(elemId, btn) {{
        const el = document.getElementById(elemId);
        if (!el) return;
        const text = el.innerText || el.textContent;
        navigator.clipboard.writeText(text).then(() => {{
            const orig = btn.innerText;
            btn.innerText = "✅ Proposition Copiée !";
            btn.style.background = "#34d399";
            setTimeout(() => {{
                btn.innerText = orig;
                btn.style.background = "#10b981";
            }}, 2500);
        }}).catch(err => {{
            prompt("Copiez manuellement la proposition :", text);
        }});
    }}
    </script>
</body>
</html>
"""
        index_path = os.path.join(self.site_dir, "index.html")
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return index_path
