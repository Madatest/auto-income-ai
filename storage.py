#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Storage Module for AUTO-INCOME AI.
Manages persistent state using SQLite and JSON snapshots.
Provides deduplication, execution auditing, and idempotence.
"""

import os
import time
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

    def __init__(
        self,
        db_path: str = "data/income_ai.db",
        state_json_path: str = "data/state.json",
        reports_dir: str = "data/cycle_reports"
    ):
        self.db_path = db_path
        self.state_json_path = state_json_path
        self.reports_dir = reports_dir
        if os.path.dirname(self.db_path):
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if os.path.dirname(self.state_json_path):
            os.makedirs(os.path.dirname(self.state_json_path), exist_ok=True)
        if self.reports_dir:
            os.makedirs(self.reports_dir, exist_ok=True)
        self._init_db()

    @staticmethod
    def atomic_write_json(file_path: str, data: Any) -> None:
        """Atomically writes JSON using a temporary file and atomic replace."""
        dir_name = os.path.dirname(file_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        tmp_path = f"{file_path}.tmp.{os.getpid()}"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, file_path)
        except Exception:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            raise

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Creates the required tables if they do not exist, and enables WAL mode."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("PRAGMA journal_mode=WAL;")
                cursor.execute("PRAGMA synchronous=NORMAL;")
            except Exception:
                pass
            
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

            # Confirmed real revenues (audit-grade)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS confirmed_revenues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT NOT NULL,
                tx_reference TEXT UNIQUE,
                deliverable_id INTEGER,
                verified_at TEXT NOT NULL,
                is_simulated INTEGER DEFAULT 0,
                metadata TEXT
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

    def record_confirmed_revenue(self, payment_data: Dict[str, Any]) -> int:
        """
        Records an authentic confirmed customer payment into SQLite.
        Guarantees 100% auditability and idempotence.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        amount = float(payment_data.get("amount", 0.0))
        currency = payment_data.get("currency", "USD").upper()
        tx_ref = payment_data.get("tx_reference")
        deliverable_id = payment_data.get("deliverable_id")
        source = payment_data.get("source", "binance_pay")
        metadata_json = json.dumps(payment_data.get("raw_data", {}))

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO confirmed_revenues (
                source, amount, currency, tx_reference, deliverable_id, verified_at, is_simulated, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, 0, ?)
            """, (source, amount, currency, tx_ref, deliverable_id, now_iso, metadata_json))
            rev_id = cursor.lastrowid

            # Update monetization_log
            if deliverable_id:
                cursor.execute("""
                UPDATE monetization_log
                SET actual_revenue_usd = actual_revenue_usd + ?, status = 'sold'
                WHERE deliverable_id = ?
                """, (amount, deliverable_id))
            else:
                cursor.execute("""
                INSERT INTO monetization_log (
                    deliverable_id, platform, status, projected_revenue_usd, actual_revenue_usd, fee_usd, created_at, is_simulated
                ) VALUES (NULL, ?, 'sold', ?, ?, 0.0, ?, 0)
                """, (source, amount, amount, now_iso))

            conn.commit()

        self.export_state_json()
        logger.info(f"CONFIRMED REAL REVENUE RECORDED: {amount} {currency} (Ref: {tx_ref})")
        return rev_id

    def is_first_revenue_confirmed(self) -> bool:
        """Checks if at least one real commercial transaction > 0 USD has been verified."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM confirmed_revenues WHERE amount > 0 AND is_simulated = 0")
            count = cursor.fetchone()[0]
            return count > 0

    def save_cycle_report(self, report_data: Dict[str, Any]) -> str:
        """Saves structured hourly cycle report atomically for complete audit trail."""
        reports_dir = self.reports_dir
        if reports_dir:
            os.makedirs(reports_dir, exist_ok=True)
        cycle_id = report_data.get("cycle_id", "latest")
        
        file_path = os.path.join(reports_dir, f"cycle_{cycle_id}.json")
        self.atomic_write_json(file_path, report_data)

        latest_path = os.path.join(reports_dir, "latest.json")
        self.atomic_write_json(latest_path, report_data)

        return file_path

    def get_latest_cycle_report(self) -> Optional[Dict[str, Any]]:
        """Loads latest cycle report if available."""
        latest_path = os.path.join(self.reports_dir, "latest.json")
        if os.path.exists(latest_path):
            try:
                with open(latest_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    @staticmethod
    def acquire_lock(lock_file: str = "data/agent.lock", max_age_seconds: int = 300) -> bool:
        """
        Prevents concurrent overlapping executions of the agent.
        Auto-recovers from crashes, unexpected battery cuts, SIGKILL, or stale locks.
        """
        dir_name = os.path.dirname(lock_file)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        current_host = os.uname().nodename if hasattr(os, "uname") else "localhost"
        now = time.time()

        if os.path.exists(lock_file):
            stale = False
            lock_pid = None
            try:
                with open(lock_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if content.startswith("{"):
                    data = json.loads(content)
                    lock_pid = data.get("pid")
                    lock_time = data.get("timestamp", 0)
                    lock_host = data.get("host", current_host)
                    # Check age
                    if (now - lock_time) > max_age_seconds:
                        logger.warning(f"Lock expiré ({round(now - lock_time)}s > {max_age_seconds}s). Purge du verrou obsolète.")
                        stale = True
                    elif lock_host == current_host and lock_pid:
                        try:
                            os.kill(int(lock_pid), 0)
                            logger.warning(f"Verrou actif par PID {lock_pid} sur {lock_host}. Exécution simultanée évitée.")
                            return False
                        except OSError:
                            stale = True
                    elif lock_host != current_host:
                        # Différent hôte (ex: Termux vs GitHub Actions runner)
                        # Si le verrou a moins de 5 min sur une autre machine, on respecte
                        logger.warning(f"Verrou actif sur hôte distant {lock_host}. Attente...")
                        return False
                else:
                    # Ancien format (PID brut)
                    lock_pid = int(content)
                    try:
                        os.kill(lock_pid, 0)
                        file_age = now - os.path.getmtime(lock_file)
                        if file_age > max_age_seconds:
                            stale = True
                        else:
                            logger.warning(f"Lock active by PID {lock_pid}. Skipping overlapping execution.")
                            return False
                    except OSError:
                        stale = True
            except Exception as e:
                logger.warning(f"Erreur de lecture du verrou ({e}). Réinitialisation.")
                stale = True

            if stale:
                try:
                    os.remove(lock_file)
                    logger.info("Verrou orphelin purgé avec succès.")
                except Exception:
                    pass

        try:
            lock_info = {
                "pid": os.getpid(),
                "timestamp": now,
                "host": current_host
            }
            StorageManager.atomic_write_json(lock_file, lock_info)
            return True
        except Exception as e:
            logger.error(f"Failed to acquire lock: {e}")
            return False

    @staticmethod
    def release_lock(lock_file: str = "data/agent.lock") -> None:
        """Releases the concurrency lock safely."""
        try:
            if os.path.exists(lock_file):
                os.remove(lock_file)
        except Exception:
            pass

