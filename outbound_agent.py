#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Autonomous Outbound Submitter for AUTO-INCOME AI.
Submits Pull Requests and comments to bounty issues 100% autonomously without human intervention,
provided a GitHub Personal Access Token (GH_TOKEN or GITHUB_TOKEN) is configured in environment.
"""

import os
import re
import json
import logging
from typing import Dict, Any, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

logger = logging.getLogger("AutoIncomeAI.OutboundSubmitter")


class OutboundSubmitter:
    """Executes automated remote submission of bounty solutions and PR proposals."""

    @staticmethod
    def extract_github_issue_info(issue_url: str) -> Optional[Dict[str, Any]]:
        """Extracts owner, repo, and issue_number from a GitHub issue URL."""
        match = re.search(r"https?://github\.com/([^/]+)/([^/]+)/issues/(\d+)", issue_url)
        if not match:
            return None
        return {
            "owner": match.group(1),
            "repo": match.group(2),
            "issue_number": int(match.group(3))
        }

    @classmethod
    def submit_issue_comment(cls, issue_url: str, comment_body: str) -> Dict[str, Any]:
        """
        Posts a resolution proposal comment directly to a GitHub issue.
        Operates completely autonomously when GH_TOKEN or GITHUB_TOKEN is available.
        """
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token:
            logger.info("Soumission autonome différée : GH_TOKEN non configuré dans .env.")
            return {
                "success": False,
                "status": "awaiting_token",
                "message": "GH_TOKEN absent dans l'environnement. Token requis pour poster sans intervention."
            }

        info = cls.extract_github_issue_info(issue_url)
        if not info:
            logger.warning(f"URL d'issue non reconnue : {issue_url}")
            return {
                "success": False,
                "status": "invalid_url",
                "message": f"URL invalide : {issue_url}"
            }

        api_url = f"https://api.github.com/repos/{info['owner']}/{info['repo']}/issues/{info['issue_number']}/comments"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "AutoIncomeAI-AutonomousBot",
            "Content-Type": "application/json"
        }

        payload = {"body": comment_body}
        req = Request(api_url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

        try:
            with urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                comment_html_url = data.get("html_url", "")
                logger.info(f"🚀 [SOUMISSION AUTONOME RÉUSSIE] Commentaire posté sur GitHub : {comment_html_url}")
                return {
                    "success": True,
                    "status": "submitted_live",
                    "comment_url": comment_html_url
                }
        except HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="ignore")
            logger.warning(f"Échec de l'appel GitHub API ({e.code}): {err_msg}")
            return {
                "success": False,
                "status": "http_error",
                "code": e.code,
                "message": err_msg
            }
        except Exception as e:
            logger.warning(f"Erreur réseau lors de la soumission GitHub : {e}")
            return {
                "success": False,
                "status": "network_error",
                "message": str(e)
            }
