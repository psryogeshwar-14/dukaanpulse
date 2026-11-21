"""
DukaanPulse End-to-End System Smoke Test
Exercises all API routes, data flows, calculations, and safety boundaries.
"""
import sys
from fastapi.testclient import TestClient
from app import app, storage


def run_smoke_test():
    print("==================================================")
    print("   DUKAANPULSE COMPREHENSIVE END-TO-END SMOKE TEST")
    print("==================================================")
    client = TestClient(app)

    # 1. Health Check
    print("\n[Step 1] Verifying System Health...")
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    health = res.json()
    print(f"  -> Health: OK (Database OK: {health['database_ok']}, Provider: {health['llm_provider']})")

    # 2. Input Validation Checks
    print("\n[Step 2] Testing Defensive Validation & Guardrails...")
    bad_req = {
        "category": "",
        "locality": "HSR Layout",
        "question": "Valid question?",
        "budget": -100
    }
    bad_res = client.post("/api/research", json=bad_req)
    assert bad_res.status_code == 422, f"Expected 422 for invalid request, got {bad_res.status_code}"
    print("  -> Blank category & negative budget rejected with HTTP 422: OK")

    # 3. Deterministic Economics Calculation
    print("\n[Step 3] Testing Deterministic Unit Economics Engine...")
    econ_req = {
        "selling_price": 179.0,
        "ingredient_cost": 50.0,
        "packaging_cost": 10.0,
        "other_variable_cost": 5.0,
        "one_time_pilot_cost": 450.0,
        "max_pilot_budget": 2000.0,
        "planned_quantity": 20
    }
    econ_res = client.post("/api/economics/calculate", json=econ_req)
    assert econ_res.status_code == 200
    econ = econ_res.json()
    assert econ["variable_cost_per_order"] == 65.0
    assert econ["contribution_per_order"] == 114.0
    assert econ["orders_to_cover_setup_cost"] == 4
    assert econ["is_budget_compliant"] is True
    assert econ["is_viable"] is True
    print(f"  -> Viable unit economics: Contribution ₹{econ['contribution_per_order']}/order, 4 break-even orders: OK")

    # Test Negative Contribution Protection
    neg_econ_req = dict(econ_req, selling_price=50.0, ingredient_cost=70.0)
    neg_res = client.post("/api/economics/calculate", json=neg_econ_req)
    assert neg_res.status_code == 200
    neg_econ = neg_res.json()
    assert neg_econ["is_viable"] is False
    assert neg_econ["recommendation"] == "negative_contribution"
    assert neg_econ["orders_to_cover_setup_cost"] is None
    print("  -> Negative contribution detected & 'DO NOT LAUNCH' triggered: OK")

    # 4. End-to-End Research Run
    print("\n[Step 4] Executing Grounded Market Research Flow...")
    research_payload = {
        "category": "Cafe",
        "locality": "HSR Layout, Bengaluru",
        "question": "Should I test a weekday breakfast bundle within a budget of INR 2,000, using existing equipment?",
        "budget": 2000.0,
        "constraints": "Existing kitchen staff only, no new machinery",
        "economics": econ_req
    }
    res_run = client.post("/api/research", json=research_payload)
    assert res_run.status_code == 200, f"Research execution failed: {res_run.text}"
    research_data = res_run.json()
    research_id = research_data["research_id"]
    report = research_data["report"]
    evidence = research_data["evidence"]

    assert research_id.startswith("res_")
    assert report["status"] == "ready"
    assert len(evidence) >= 1
    assert len(report["observations"]) >= 1
    assert report["experiment"]["budget_ceiling"] <= 2000.0
    print(f"  -> Research ID: {research_id}")
    print(f"  -> Evidence items collected: {len(evidence)}")
    print(f"  -> Factual observations: {len(report['observations'])}")
    print(f"  -> Proposed Experiment: '{report['experiment']['title']}' (Ceiling: ₹{report['experiment']['budget_ceiling']})")

    # Check Quote Grounding Verification
    first_obs = report["observations"][0]
    quote_obj = first_obs["supporting_quotes"][0]
    matched_evi = next(e for e in evidence if e["evidence_id"] == quote_obj["evidence_id"])
    assert quote_obj["quote"].lower() in matched_evi["snippet"].lower()
    print(f"  -> Quote-in-excerpt verification: Citation [{quote_obj['evidence_id']}] verified against source snippet: OK")

    # 5. Stale Advice Check
    print("\n[Step 5] Testing Cost Assumption Invalidation (Stale Advice)...")
    exp_res = client.post("/api/experiments", json={"research_id": research_id})
    assert exp_res.status_code == 200
    exp_data = exp_res.json()
    exp_id = exp_data["id"]

    # When owner increases ingredient cost from 50 to 120:
    stale_payload = {
        "experiment_id": exp_id,
        "current_economics": dict(econ_req, ingredient_cost=120.0)
    }
    stale_res = client.post("/api/economics/check-stale", json=stale_payload)
    assert stale_res.status_code == 200
    stale_data = stale_res.json()
    assert stale_data["is_stale"] is True
    print(f"  -> Stale advice detected: '{stale_data['stale_reason']}': OK")

    # 6. Outcome Tracking & Managerial Economics
    print("\n[Step 6] Recording Daily Outcomes & Measuring Contribution...")
    day1_payload = {
        "date": "2026-11-21",
        "orders": 12,
        "revenue": 2148.0,
        "variable_cost": 780.0,
        "notes": "12 cold brew breakfast combos sold out by 9:45 AM"
    }
    out1_res = client.post(f"/api/experiments/{exp_id}/outcome", json=day1_payload)
    assert out1_res.status_code == 200
    exp_after_day1 = out1_res.json()
    assert exp_after_day1["total_orders"] == 12
    assert exp_after_day1["total_revenue"] == 2148.0
    assert exp_after_day1["total_variable_cost"] == 780.0
    assert exp_after_day1["total_contribution"] == 1368.0  # 2148 - 780
    assert exp_after_day1["gross_margin_pct"] == round((1368.0 / 2148.0) * 100, 2)
    print(f"  -> Day 1: Orders: 12, Revenue: ₹2,148.00, Contribution: ₹{exp_after_day1['total_contribution']} ({exp_after_day1['gross_margin_pct']}% Gross Margin): OK")

    day2_payload = {
        "date": "2026-11-22",
        "orders": 15,
        "revenue": 2685.0,
        "variable_cost": 975.0,
        "notes": "Higher morning commuter footfall"
    }
    out2_res = client.post(f"/api/experiments/{exp_id}/outcome", json=day2_payload)
    assert out2_res.status_code == 200
    exp_after_day2 = out2_res.json()
    assert exp_after_day2["total_orders"] == 27
    assert exp_after_day2["total_revenue"] == 4833.0
    assert exp_after_day2["total_variable_cost"] == 1755.0
    assert exp_after_day2["total_contribution"] == 3078.0  # 4833 - 1755
    print(f"  -> Day 2: Cumulative Orders: 27, Revenue: ₹4,833.00, Contribution: ₹{exp_after_day2['total_contribution']}: OK")

    # 7. Restart Persistence Verification
    print("\n[Step 7] Testing Database Restart Persistence...")
    from services.storage import Storage
    restarted_storage = Storage(db_path=storage.db_path)
    persisted_exp = restarted_storage.get_experiment(exp_id)
    assert persisted_exp is not None
    assert persisted_exp.total_orders == 27
    assert persisted_exp.total_contribution == 3078.0
    assert len(persisted_exp.measurements) == 2
    print("  -> Full ledger & outcome history preserved across simulated restart: OK")

    print("\n==================================================")
    print("   ALL SMOKE TEST STAGES COMPLETED SUCCESSFULLY!")
    print("==================================================")


if __name__ == "__main__":
    run_smoke_test()
