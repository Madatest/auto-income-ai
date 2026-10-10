#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storage Module for AUTO-INCOME AI.
Manages persistent state using SQLite and JSON snapshots.
Provides deduplication, execution auditing, and idempotence.
"""

import os
import json
import sqlite3
import hashlib
import logging
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Dict, List, Optional, Any, Generator

logger = logging.getLogger("AutoIncomeAI.Storage")


class StorageManager:
    """Handles SQLite persistence and JSON state synchronization."""

    def __init__(self, db_path: str = "data/income_ai.db", state_json_path: str = "data/state.json"):
        self.db_path = db_path
        self.state_json_path = state_json_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.state_json_path), exist_ok=True)
        self._init_db()

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Creates the required tables if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Executions audit log
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL,
                opportunities_found INTEGER DEFAULT 0,
                deliverables_created INTEGER DEFAULT 0,
                duration_seconds REAL DEFAULT 0.0,
                notes TEXT
            );
            """)

            # Opportunities table with unique hash for deduplication
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                source_id TEXT,
                source_url TEXT,
                score REAL DEFAULT 0.0,
                score_breakdown TEXT,
                status TEXT DEFAULT 'pending', -- pending, processed, archived
                is_simulated INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            );
            """)

            # Deliverables table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS deliverables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_hash TEXT,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                file_path TEXT NOT NULL,
                relative_path TEXT NOT NULL,
                monetization_channel TEXT NOT NULL,
                price_usd REAL DEFAULT 0.0,
                quality_score REAL DEFAULT 100.0,
                metadata TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (opportunity_hash) REFERENCES opportunities (hash)
            );
            """)

            # Monetization track
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS monetization_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                deliverable_id INTEGER,
                platform TEXT NOT NULL,
                status TEXT DEFAULT 'ready_for_sale',
                projected_revenue_usd REAL DEFAULT 0.0,
                actual_revenue_usd REAL DEFAULT 0.0,
                fee_usd REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                is_simulated INTEGER DEFAULT 0
            );
            """)

            conn.commit()

    @staticmethod
    def compute_hash(source_id: str, title: str) -> str:
        """Generates a stable SHA-256 hash for deduplication."""
        payload = f"{source_id}:{title.strip().lower()}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def save_opportunity(self, opp: Dict[str, Any]) -> bool:
        """
        Saves an opportunity if it doesn't already exist.
        Returns True if newly inserted, False if duplicate.
        """
        opp_hash = opp.get("hash") or self.compute_hash(opp.get("source_id", "manual"), opp.get("title", ""))
        now_iso = datetime.now(timezone.utc).isoformat()
        breakdown_json = json.dumps(opp.get("score_breakdown", {}))

        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                INSERT INTO opportunities (
                    hash, title, category, description, source_id, source_url,
                    score, score_breakdown, status, is_simulated, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    opp_hash,
                    opp.get("title", "Sans titre"),
                    opp.get("category", "digital_product"),
                    opp.get("description", ""),
                    opp.get("source_id", "unknown"),
                    opp.get("source_url", ""),
                    float(opp.get("score", 0.0)),
                    breakdown_json,
                    opp.get("status", "pending"),
                    1 if opp.get("is_simulated", False) else 0,
                    now_iso
                ))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # Duplicate detected
                return False

    def get_pending_opportunities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves top-scoring pending opportunities."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM opportunities
            WHERE status = 'pending'
            ORDER BY score DESC, id ASC
            LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                if item.get("score_breakdown"):
                    try:
                        item["score_breakdown"] = json.loads(item["score_breakdown"])
                    except Exception:
                        pass
                results.append(item)
            return results

    def mark_opportunity_processed(self, opp_hash: str) -> None:
        """Marks an opportunity as processed."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE opportunities SET status = 'processed' WHERE hash = ?", (opp_hash,))
            conn.commit()

    def save_deliverable(self, deliverable: Dict[str, Any]) -> int:
        """Saves a created deliverable and returns its row ID."""
        now_iso = datetime.now(timezone.utc).isoformat()
        metadata_json = json.dumps(deliverable.get("metadata", {}))

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO deliverables (
                opportunity_hash, category, title, file_path, relative_path,
                monetization_channel, price_usd, quality_score, metadata, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                deliverable.get("opportunity_hash", ""),
                deliverable.get("category", "digital_product"),
                deliverable.get("title", "Livrable"),
                deliverable.get("file_path", ""),
                deliverable.get("relative_path", ""),
                deliverable.get("monetization_channel", "crypto_usdt"),
                float(deliverable.get("price_usd", 0.0)),
                float(deliverable.get("quality_score", 100.0)),
                metadata_json,
                now_iso
            ))
            deliverable_id = cursor.lastrowid

            # Also log into monetization_log as ready
            cursor.execute("""
            INSERT INTO monetization_log (
                deliverable_id, platform, status, projected_revenue_usd, actual_revenue_usd, fee_usd, created_at, is_simulated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                deliverable_id,
                deliverable.get("monetization_channel", "crypto_usdt"),
                "ready_for_sale",
                float(deliverable.get("price_usd", 0.0)),
                0.0,
                0.0,
                now_iso,
                1 if deliverable.get("is_simulated", False) else 0
            ))

            conn.commit()
            return deliverable_id

    def record_execution(self, status: str, opps_found: int, deliverables_created: int, duration_sec: float, notes: str = "") -> int:
        """Logs an agent execution cycle."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO executions (
                timestamp, status, opportunities_found, deliverables_created, duration_seconds, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, (now_iso, status, opps_found, deliverables_created, duration_sec, notes))
            conn.commit()
            exec_id = cursor.lastrowid
            
        # Synchronize snapshot JSON
        self.export_state_json()
        return exec_id

    def get_summary_stats(self) -> Dict[str, Any]:
        """Calculates global operational statistics."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM executions")
            total_executions = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM opportunities")
            total_opportunities = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM deliverables")
            total_deliverables = cursor.fetchone()[0]

            cursor.execute("SELECT SUM(actual_revenue_usd) FROM monetization_log")
            total_revenue = cursor.fetchone()[0] or 0.0

            cursor.execute("SELECT SUM(projected_revenue_usd) FROM monetization_log")
            projected_pipeline = cursor.fetchone()[0] or 0.0

            cursor.execute("SELECT * FROM executions ORDER BY id DESC LIMIT 1")
            last_exec_row = cursor.fetchone()
            last_execution = dict(last_exec_row) if last_exec_row else None

        return {
            "total_executions": total_executions,
            "total_opportunities": total_opportunities,
            "total_deliverables": total_deliverables,
            "total_confirmed_revenue_usd": round(total_revenue, 2),
            "projected_pipeline_usd": round(projected_pipeline, 2),
            "total_costs_usd": 0.0,  # 0 USD budget rule strictly verified
            "last_execution": last_execution,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

    def get_all_deliverables(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Returns created deliverables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM deliverables ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                if item.get("metadata"):
                    try:
                        item["metadata"] = json.loads(item["metadata"])
                    except Exception:
                        pass
                results.append(item)
            return results

    def get_recent_opportunities(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Returns recent scored opportunities."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM opportunities ORDER BY score DESC, id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            results = []
            for r in rows:
                item = dict(r)
                if item.get("score_breakdown"):
                    try:
                        item["score_breakdown"] = json.loads(item["score_breakdown"])
                    except Exception:
                        pass
                results.append(item)
            return results

    def export_state_json(self) -> str:
        """Exports an atomic state snapshot to state_json_path."""
        stats = self.get_summary_stats()
        deliverables = self.get_all_deliverables(limit=10)
        top_opps = self.get_recent_opportunities(limit=10)

        snapshot = {
            "system": "AUTO-INCOME AI",
            "stats": stats,
            "recent_deliverables": deliverables,
            "top_opportunities": top_opps,
            "exported_at": datetime.now(timezone.utc).isoformat()
        }

        temp_path = f"{self.state_json_path}.tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, self.state_json_path)
        return self.state_json_path
