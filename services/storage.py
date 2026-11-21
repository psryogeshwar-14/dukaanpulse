"""
DukaanPulse SQLite Storage Engine
Thread-safe, parameterized persistence for research runs, evidence, experiments, and outcomes.
"""
import sqlite3
import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from services.models import (
    ResearchRequest, ResearchReport, EvidenceItem, ResearchResponse,
    ExperimentRecord, OutcomeInput, OutcomeRecord
)


class Storage:
    def __init__(self, db_path: str = "dukaanpulse.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS research_runs (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                locality TEXT NOT NULL,
                question TEXT NOT NULL,
                budget REAL NOT NULL,
                constraints TEXT,
                report_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS evidence_items (
                id TEXT PRIMARY KEY,
                research_id TEXT NOT NULL,
                evidence_id TEXT NOT NULL,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                snippet TEXT NOT NULL,
                query TEXT NOT NULL,
                retrieved_at TEXT NOT NULL,
                domain TEXT,
                source_date TEXT,
                locality_match TEXT,
                FOREIGN KEY (research_id) REFERENCES research_runs(id) ON DELETE CASCADE
            );
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                id TEXT PRIMARY KEY,
                research_id TEXT NOT NULL,
                category TEXT NOT NULL,
                locality TEXT NOT NULL,
                title TEXT NOT NULL,
                hypothesis TEXT,
                steps_json TEXT NOT NULL,
                validation_step TEXT DEFAULT '',
                duration_days INTEGER DEFAULT 3,
                budget_ceiling REAL NOT NULL,
                cost_note TEXT NOT NULL,
                success_criterion TEXT NOT NULL,
                stop_conditions_json TEXT DEFAULT '[]',
                assumptions_json TEXT DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL,
                FOREIGN KEY (research_id) REFERENCES research_runs(id) ON DELETE RESTRICT
            );
            """)

            # Gracefully handle adding new columns to existing SQLite table if needed
            existing_cols = {col["name"] for col in cursor.execute("PRAGMA table_info(experiments);").fetchall()}
            for col_name, col_def in [
                ("hypothesis", "TEXT"),
                ("validation_step", "TEXT DEFAULT ''"),
                ("duration_days", "INTEGER DEFAULT 3"),
                ("stop_conditions_json", "TEXT DEFAULT '[]'"),
                ("assumptions_json", "TEXT DEFAULT '{}'")
            ]:
                if col_name not in existing_cols:
                    try:
                        cursor.execute(f"ALTER TABLE experiments ADD COLUMN {col_name} {col_def};")
                    except sqlite3.OperationalError:
                        pass

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS outcomes (
                id TEXT PRIMARY KEY,
                experiment_id TEXT NOT NULL,
                date TEXT NOT NULL,
                orders INTEGER NOT NULL,
                revenue REAL NOT NULL,
                variable_cost REAL NOT NULL,
                contribution REAL NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
            );
            """)
            conn.commit()

    def save_research(
        self,
        request: ResearchRequest,
        report: ResearchReport,
        evidence: List[EvidenceItem]
    ) -> str:
        research_id = f"res_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat() + "Z"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO research_runs (id, category, locality, question, budget, constraints, report_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    research_id,
                    request.category,
                    request.locality,
                    request.question,
                    request.budget,
                    request.constraints or "",
                    report.model_dump_json(),
                    now,
                ),
            )

            for item in evidence:
                item_pk = f"evi_{uuid.uuid4().hex[:12]}"
                cursor.execute(
                    """
                    INSERT INTO evidence_items (
                        id, research_id, evidence_id, url, title, snippet, query, retrieved_at, domain, source_date, locality_match
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item_pk,
                        research_id,
                        item.evidence_id,
                        item.url,
                        item.title,
                        item.snippet,
                        item.query,
                        item.retrieved_at,
                        item.domain,
                        item.source_date,
                        item.locality_match,
                    ),
                )
            conn.commit()

        return research_id

    def get_research(self, research_id: str) -> Optional[ResearchResponse]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM research_runs WHERE id = ?", (research_id,))
            row = cursor.fetchone()
            if not row:
                return None

            cursor.execute(
                "SELECT * FROM evidence_items WHERE research_id = ? ORDER BY evidence_id ASC",
                (research_id,),
            )
            evidence_rows = cursor.fetchall()
            evidence = [
                EvidenceItem(
                    evidence_id=er["evidence_id"],
                    url=er["url"],
                    title=er["title"],
                    snippet=er["snippet"],
                    query=er["query"],
                    retrieved_at=er["retrieved_at"],
                    domain=er["domain"],
                    source_date=er["source_date"],
                    locality_match=er["locality_match"],
                )
                for er in evidence_rows
            ]

            report_data = json.loads(row["report_json"])
            report = ResearchReport.model_validate(report_data)

            return ResearchResponse(
                research_id=row["id"],
                category=row["category"],
                locality=row["locality"],
                question=row["question"],
                budget=row["budget"],
                constraints=row["constraints"],
                created_at=row["created_at"],
                report=report,
                evidence=evidence,
            )

    def create_experiment(self, research_id: str) -> Optional[ExperimentRecord]:
        research = self.get_research(research_id)
        if not research:
            return None
        if not research.report.experiment or research.report.status != "ready":
            return None

        exp = research.report.experiment
        exp_id = f"exp_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat() + "Z"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO experiments (
                    id, research_id, category, locality, title, hypothesis, steps_json,
                    validation_step, duration_days, budget_ceiling, cost_note, success_criterion,
                    stop_conditions_json, assumptions_json, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
                """,
                (
                    exp_id,
                    research_id,
                    research.category,
                    research.locality,
                    exp.title,
                    exp.hypothesis or research.report.hypothesis,
                    json.dumps(exp.steps),
                    exp.validation_step or "",
                    exp.duration_days or 3,
                    exp.budget_ceiling,
                    exp.cost_note,
                    exp.success_criterion,
                    json.dumps(exp.stop_conditions or []),
                    json.dumps(exp.assumptions_snapshot or {}),
                    now,
                ),
            )
            conn.commit()

        return self.get_experiment(exp_id)

    def get_experiment(self, experiment_id: str) -> Optional[ExperimentRecord]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,))
            row = cursor.fetchone()
            if not row:
                return None

            cursor.execute(
                "SELECT * FROM outcomes WHERE experiment_id = ? ORDER BY date ASC, created_at ASC",
                (experiment_id,),
            )
            outcome_rows = cursor.fetchall()
            outcomes = [
                OutcomeRecord(
                    id=out["id"],
                    experiment_id=out["experiment_id"],
                    date=out["date"],
                    orders=out["orders"],
                    revenue=out["revenue"],
                    variable_cost=out["variable_cost"],
                    contribution=out["contribution"],
                    notes=out["notes"] or "",
                    created_at=out["created_at"],
                )
                for out in outcome_rows
            ]

            total_orders = sum(o.orders for o in outcomes)
            total_rev = sum(o.revenue for o in outcomes)
            total_cost = sum(o.variable_cost for o in outcomes)
            total_contrib = total_rev - total_cost
            gross_margin = (total_contrib / total_rev * 100) if total_rev > 0 else None

            # Parse optional JSON columns with backwards compatibility
            keys = row.keys()
            hypothesis = row["hypothesis"] if "hypothesis" in keys else None
            validation_step = row["validation_step"] if "validation_step" in keys and row["validation_step"] else ""
            duration_days = row["duration_days"] if "duration_days" in keys and row["duration_days"] else 3
            stop_conditions = (
                json.loads(row["stop_conditions_json"])
                if "stop_conditions_json" in keys and row["stop_conditions_json"]
                else []
            )
            assumptions = (
                json.loads(row["assumptions_json"])
                if "assumptions_json" in keys and row["assumptions_json"]
                else None
            )

            return ExperimentRecord(
                id=row["id"],
                research_id=row["research_id"],
                category=row["category"],
                locality=row["locality"],
                title=row["title"],
                hypothesis=hypothesis,
                steps=json.loads(row["steps_json"]),
                validation_step=validation_step,
                duration_days=duration_days,
                budget_ceiling=row["budget_ceiling"],
                cost_note=row["cost_note"],
                success_criterion=row["success_criterion"],
                stop_conditions=stop_conditions,
                assumptions_snapshot=assumptions,
                created_at=row["created_at"],
                status=row["status"],
                measurements=outcomes,
                total_orders=total_orders,
                total_revenue=round(total_rev, 2),
                total_variable_cost=round(total_cost, 2),
                total_contribution=round(total_contrib, 2),
                gross_margin_pct=round(gross_margin, 2) if gross_margin is not None else None,
            )

    def list_experiments(self) -> List[ExperimentRecord]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM experiments ORDER BY created_at DESC")
            rows = cursor.fetchall()

        results = []
        for r in rows:
            exp = self.get_experiment(r["id"])
            if exp:
                results.append(exp)
        return results

    def add_outcome(self, experiment_id: str, outcome: OutcomeInput) -> Optional[OutcomeRecord]:
        exp = self.get_experiment(experiment_id)
        if not exp:
            return None

        # Managerial calculation: contribution = revenue - variable_cost
        contribution = round(outcome.revenue - outcome.variable_cost, 2)
        outcome_id = f"out_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat() + "Z"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO outcomes (
                    id, experiment_id, date, orders, revenue, variable_cost, contribution, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    outcome_id,
                    experiment_id,
                    outcome.date,
                    outcome.orders,
                    outcome.revenue,
                    outcome.variable_cost,
                    contribution,
                    outcome.notes or "",
                    now,
                ),
            )
            conn.commit()

        return OutcomeRecord(
            id=outcome_id,
            experiment_id=experiment_id,
            date=outcome.date,
            orders=outcome.orders,
            revenue=outcome.revenue,
            variable_cost=outcome.variable_cost,
            contribution=contribution,
            notes=outcome.notes or "",
            created_at=now,
        )
