"""Unit tests for DukaanPulse SQLite Storage"""
import os
import tempfile
import pytest
from services.storage import Storage
from services.models import (
    ResearchRequest, ResearchReport, Observation, SupportingQuote,
    Experiment, EvidenceItem, OutcomeInput
)


@pytest.fixture
def temp_storage():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    storage = Storage(db_path=path)
    yield storage
    if os.path.exists(path):
        os.remove(path)


def test_save_and_retrieve_research(temp_storage):
    req = ResearchRequest(
        category="Cafe",
        locality="HSR Layout, Bengaluru",
        question="Which weekday breakfast offer to test?",
        budget=2000.0,
        constraints="No new equipment"
    )
    evi = [
        EvidenceItem(
            evidence_id="E1",
            url="https://example.com/hsr-cafe",
            title="HSR Cafe Morning Guide",
            snippet="Local cafes in Sector 1 offer cold brew combos around 199 INR.",
            query="cafe HSR Layout Bengaluru breakfast menu",
            retrieved_at="2026-11-21T10:00:00Z",
            domain="example.com"
        )
    ]
    report = ResearchReport(
        status="ready",
        observations=[
            Observation(
                claim="Local cafes bundle cold brew for weekday breakfast",
                evidence_ids=["E1"],
                supporting_quotes=[
                    SupportingQuote(evidence_id="E1", quote="cold brew combos around 199 INR")
                ]
            )
        ],
        unknowns=["Exact footfall before 9:00 AM"],
        hypothesis="A cold brew plus sandwich combo under ₹200 will attract tech workers on weekdays.",
        experiment=Experiment(
            title="Cold Brew Breakfast Combo Test",
            steps=["Prep 15 cold brew bottles", "Display chalkboard offer ₹199", "Track orders 8-11am"],
            budget_ceiling=2000.0,
            estimated_cost=1200.0,
            cost_note="Bottling and coffee beans cost",
            success_criterion="10 combo orders daily for 3 days",
            metrics=["orders", "revenue", "variable_cost"]
        ),
        limitations=["Online prices may exclude delivery platform markups"]
    )

    research_id = temp_storage.save_research(req, report, evi)
    assert research_id.startswith("res_")

    res = temp_storage.get_research(research_id)
    assert res is not None
    assert res.category == "Cafe"
    assert res.budget == 2000.0
    assert len(res.evidence) == 1
    assert res.evidence[0].evidence_id == "E1"
    assert res.report.status == "ready"
    assert len(res.report.observations) == 1


def test_experiment_and_outcome_tracking(temp_storage):
    req = ResearchRequest(
        category="Bakery",
        locality="Indiranagar, Bengaluru",
        question="Which snack box to test?",
        budget=1500.0
    )
    report = ResearchReport(
        status="ready",
        observations=[],
        unknowns=[],
        hypothesis="Mini croissant pack",
        experiment=Experiment(
            title="Mini Croissant Trial",
            steps=["Bake mini batches", "Package in 4s"],
            budget_ceiling=1500.0,
            cost_note="Flour and butter",
            success_criterion="Sell 20 boxes"
        ),
        limitations=[]
    )
    research_id = temp_storage.save_research(req, report, [])
    
    exp = temp_storage.create_experiment(research_id)
    assert exp is not None
    assert exp.title == "Mini Croissant Trial"
    assert exp.status == "active"

    # Add outcomes
    out1 = temp_storage.add_outcome(
        exp.id,
        OutcomeInput(date="2026-11-21", orders=12, revenue=1200.0, variable_cost=400.0, notes="Day 1")
    )
    assert out1 is not None
    assert out1.contribution == 800.0  # 1200 - 400

    out2 = temp_storage.add_outcome(
        exp.id,
        OutcomeInput(date="2026-11-22", orders=15, revenue=1500.0, variable_cost=500.0, notes="Day 2")
    )
    assert out2 is not None
    assert out2.contribution == 1000.0

    updated_exp = temp_storage.get_experiment(exp.id)
    assert updated_exp.total_orders == 27
    assert updated_exp.total_revenue == 2700.0
    assert updated_exp.total_variable_cost == 900.0
    assert updated_exp.total_contribution == 1800.0
    assert updated_exp.gross_margin_pct == pytest.approx(66.67, 0.01)
