"""
Integration & API tests for DukaanPulse FastAPI application
"""
import pytest
from fastapi.testclient import TestClient
from app import app, storage


@pytest.fixture(autouse=True)
def clean_db(monkeypatch, tmp_path):
    from services.storage import Storage
    db_file = tmp_path / "test_api.db"
    new_storage = Storage(db_path=str(db_file))
    monkeypatch.setattr("app.storage", new_storage)


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "database_ok" in data
    assert data["database_ok"] is True


def test_research_flow_and_validation(client):
    # 1. Invalid input: negative budget
    bad_req = {
        "category": "Cafe",
        "locality": "HSR Layout, Bengaluru",
        "question": "Which breakfast combo to test?",
        "budget": -500.0,
        "constraints": "None"
    }
    res_bad = client.post("/api/research", json=bad_req)
    assert res_bad.status_code == 422

    # 2. Invalid input: blank category
    bad_cat = {
        "category": "   ",
        "locality": "HSR Layout, Bengaluru",
        "question": "Which breakfast combo to test?",
        "budget": 2000.0
    }
    res_bad_cat = client.post("/api/research", json=bad_cat)
    assert res_bad_cat.status_code == 422

    # 3. Valid input (HSR Cafe primary demo)
    valid_req = {
        "category": "Cafe",
        "locality": "HSR Layout, Bengaluru",
        "question": "Which weekday breakfast offer to test without new equipment?",
        "budget": 2000.0,
        "constraints": "No new equipment"
    }
    res = client.post("/api/research", json=valid_req)
    assert res.status_code == 200
    data = res.json()
    assert "research_id" in data
    research_id = data["research_id"]
    assert data["category"] == "Cafe"
    assert data["locality"] == "HSR Layout, Bengaluru"
    assert len(data["evidence"]) >= 1
    assert data["report"]["status"] == "ready"
    assert len(data["report"]["observations"]) >= 1
    assert data["report"]["experiment"]["budget_ceiling"] <= 2000.0

    # 4. Retrieve saved research
    get_res = client.get(f"/api/research/{research_id}")
    assert get_res.status_code == 200
    assert get_res.json()["research_id"] == research_id

    # 5. Retrieve unknown research ID -> 404
    get_unknown = client.get("/api/research/res_nonexistent")
    assert get_unknown.status_code == 404

    # 6. Accept experiment
    exp_res = client.post("/api/experiments", json={"research_id": research_id})
    assert exp_res.status_code == 200
    exp_data = exp_res.json()
    exp_id = exp_data["id"]
    assert exp_data["status"] == "active"
    assert exp_data["budget_ceiling"] <= 2000.0

    # 7. Add outcome measurement
    outcome_payload = {
        "date": "2026-11-21",
        "orders": 12,
        "revenue": 2148.0,
        "variable_cost": 720.0,
        "notes": "Fast grab-and-go chalkboard attracted morning office commuters"
    }
    out_res = client.post(f"/api/experiments/{exp_id}/outcome", json=outcome_payload)
    assert out_res.status_code == 200
    updated_exp = out_res.json()
    assert updated_exp["total_orders"] == 12
    assert updated_exp["total_revenue"] == 2148.0
    assert updated_exp["total_variable_cost"] == 720.0
    assert updated_exp["total_contribution"] == 1428.0
    assert updated_exp["gross_margin_pct"] == pytest.approx(66.48, 0.01)

    # 8. List experiments
    list_res = client.get("/api/experiments")
    assert list_res.status_code == 200
    exps = list_res.json()
    assert len(exps) == 1
    assert exps[0]["id"] == exp_id


def test_root_serves_index_html(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "DukaanPulse" in res.text
    assert "Café Profile & Research Goal" in res.text


def test_economics_calculation_endpoint(client):
    payload = {
        "selling_price": 179.0,
        "ingredient_cost": 50.0,
        "packaging_cost": 10.0,
        "other_variable_cost": 5.0,
        "one_time_pilot_cost": 450.0,
        "max_pilot_budget": 2000.0,
        "planned_quantity": 20
    }
    res = client.post("/api/economics/calculate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["variable_cost_per_order"] == 65.0
    assert data["contribution_per_order"] == 114.0
    assert data["orders_to_cover_setup_cost"] == 4
    assert data["is_budget_compliant"] is True
    assert data["is_viable"] is True
    assert data["recommendation"] == "viable"

    # Test invalid negative price
    bad_payload = {
        "selling_price": -50.0,
        "ingredient_cost": 20.0,
        "max_pilot_budget": 1000.0
    }
    bad_res = client.post("/api/economics/calculate", json=bad_payload)
    assert bad_res.status_code == 422 or bad_res.status_code == 400


def test_stale_economics_check_endpoint(client):
    # 1. Run research with initial economics
    res = client.post("/api/research", json={
        "category": "Cafe",
        "locality": "HSR Layout, Bengaluru",
        "question": "Which weekday breakfast offer to test?",
        "budget": 2000.0,
        "economics": {
            "selling_price": 179.0,
            "ingredient_cost": 50.0,
            "packaging_cost": 10.0,
            "other_variable_cost": 5.0,
            "one_time_pilot_cost": 450.0,
            "max_pilot_budget": 2000.0
        }
    })
    assert res.status_code == 200
    research_id = res.json()["research_id"]

    # 2. Accept experiment
    exp_res = client.post("/api/experiments", json={"research_id": research_id})
    assert exp_res.status_code == 200
    exp_id = exp_res.json()["id"]

    # 3. Check staleness with same economics -> not stale
    check1 = client.post("/api/economics/check-stale", json={
        "experiment_id": exp_id,
        "current_economics": {
            "selling_price": 179.0,
            "ingredient_cost": 50.0,
            "packaging_cost": 10.0,
            "other_variable_cost": 5.0,
            "one_time_pilot_cost": 450.0,
            "max_pilot_budget": 2000.0
        }
    })
    assert check1.status_code == 200
    assert check1.json()["is_stale"] is False

    # 4. Check staleness with altered ingredient cost -> STALE
    check2 = client.post("/api/economics/check-stale", json={
        "experiment_id": exp_id,
        "current_economics": {
            "selling_price": 179.0,
            "ingredient_cost": 120.0,  # Jump from 50 to 120
            "packaging_cost": 10.0,
            "other_variable_cost": 5.0,
            "one_time_pilot_cost": 450.0,
            "max_pilot_budget": 2000.0
        }
    })
    assert check2.status_code == 200
    assert check2.json()["is_stale"] is True
    assert "ingredient cost changed" in check2.json()["stale_reason"].lower()


def test_research_history_and_csv_export(client):
    # 1. Create a research run
    res = client.post("/api/research", json={
        "category": "Cafe",
        "locality": "HSR Layout, Bengaluru",
        "question": "Which weekday breakfast combo to test?",
        "budget": 2000.0,
        "economics": {
            "selling_price": 179.0,
            "ingredient_cost": 50.0,
            "packaging_cost": 10.0,
            "other_variable_cost": 5.0,
            "one_time_pilot_cost": 450.0,
            "max_pilot_budget": 2000.0
        }
    })
    assert res.status_code == 200
    research_id = res.json()["research_id"]

    # 2. List history
    hist_res = client.get("/api/research")
    assert hist_res.status_code == 200
    hist = hist_res.json()
    assert len(hist) >= 1
    run_entry = next((r for r in hist if r["id"] == research_id), None)
    assert run_entry is not None
    assert run_entry["category"] == "Cafe"
    assert run_entry["has_accepted_experiment"] is False

    # 3. Export research CSV
    csv_res = client.get(f"/api/research/{research_id}/export-csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    csv_text = csv_res.text
    assert "RESEARCH SUMMARY" in csv_text
    assert research_id in csv_text
    assert "VERIFIED EVIDENCE LEDGER" in csv_text
    assert "OWNER-ENTERED UNIT ECONOMICS" in csv_text


def test_experiment_tasks_lifecycle_and_csv_export(client):
    # 1. Create research and accept experiment
    res = client.post("/api/research", json={
        "category": "Cafe",
        "locality": "HSR Layout, Bengaluru",
        "question": "Which weekday breakfast combo to test?",
        "budget": 2000.0
    })
    research_id = res.json()["research_id"]
    exp_res = client.post("/api/experiments", json={"research_id": research_id})
    assert exp_res.status_code == 200
    exp_id = exp_res.json()["id"]

    # 2. Get initial tasks (seeded from experiment steps)
    tasks_res = client.get(f"/api/experiments/{exp_id}/tasks")
    assert tasks_res.status_code == 200
    initial_tasks = tasks_res.json()
    assert len(initial_tasks) >= 1
    assert all(t["is_owner_added"] is False for t in initial_tasks)
    first_task = initial_tasks[0]

    # 3. Add an owner task
    add_res = client.post(f"/api/experiments/{exp_id}/tasks", json={
        "text": "Taste test batch with barista team"
    })
    assert add_res.status_code == 200
    owner_task = add_res.json()
    assert owner_task["is_owner_added"] is True
    assert owner_task["is_completed"] is False
    assert owner_task["text"] == "Taste test batch with barista team"

    # 4. Toggle task completed
    patch_res = client.patch(
        f"/api/experiments/{exp_id}/tasks/{first_task['id']}",
        json={"is_completed": True}
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["is_completed"] is True

    # 5. Export experiment CSV
    csv_res = client.get(f"/api/experiments/{exp_id}/export-csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "ACTIONABLE TASK CHECKLIST" in csv_res.text
    assert "Taste test batch with barista team" in csv_res.text

    # 6. Delete owner task
    del_res = client.delete(f"/api/experiments/{exp_id}/tasks/{owner_task['id']}")
    assert del_res.status_code == 200

    tasks_after_del = client.get(f"/api/experiments/{exp_id}/tasks").json()
    assert not any(t["id"] == owner_task["id"] for t in tasks_after_del)


def test_offer_comparison_endpoint(client):
    payload = {
        "max_budget": 2500.0,
        "offer_a": {
            "name": "Standard Cold Brew Combo",
            "selling_price": 179.0,
            "ingredient_cost": 50.0,
            "packaging_cost": 10.0,
            "other_variable_cost": 5.0,
            "one_time_pilot_cost": 450.0,
            "planned_quantity": 20,
            "operational_notes": "Existing cold brew kegs"
        },
        "offer_b": {
            "name": "Premium Artisanal Croissant Box",
            "selling_price": 249.0,
            "ingredient_cost": 90.0,
            "packaging_cost": 15.0,
            "other_variable_cost": 5.0,
            "one_time_pilot_cost": 600.0,
            "planned_quantity": 15,
            "operational_notes": "Morning bakery delivery needed"
        }
    }
    res = client.post("/api/economics/compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["offer_a"]["contribution_per_order"] == 114.0
    assert data["offer_b"]["contribution_per_order"] == 139.0
    assert data["higher_contribution_offer"] == "Premium Artisanal Croissant Box"
    assert "under entered unit cost assumptions" in data["comparison_summary"]
    assert "Customer demand" in data["disclaimer"]

    # Check list comparisons
    list_res = client.get("/api/economics/comparisons")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


def test_csv_injection_formula_defense():
    from services.export import escape_csv_cell
    # Test formula triggers: =, +, -, @, tab, return
    assert escape_csv_cell("=cmd|' /C calc'!A0") == "'=cmd|' /C calc'!A0"
    assert escape_csv_cell("+12345") == "'+12345"
    assert escape_csv_cell("-12345") == "'-12345"
    assert escape_csv_cell("@SUM(A1:A10)") == "'@SUM(A1:A10)"
    assert escape_csv_cell("Normal Text") == "Normal Text"
    assert escape_csv_cell('Text with "quotes"') == '"Text with ""quotes"""'


def test_compare_offers_equal_contribution_and_budget_variance(client):
    payload = {
        "max_budget": 1000.0,
        "offer_a": {
            "name": "Combo A",
            "selling_price": 100.0,
            "ingredient_cost": 40.0,
            "packaging_cost": 10.0,
            "other_variable_cost": 0.0,
            "one_time_pilot_cost": 100.0,
            "planned_quantity": 10,
            "operational_notes": "None"
        },
        "offer_b": {
            "name": "Combo B",
            "selling_price": 120.0,
            "ingredient_cost": 60.0,
            "packaging_cost": 10.0,
            "other_variable_cost": 0.0,
            "one_time_pilot_cost": 200.0,
            "planned_quantity": 25,  # 200 + 25 * 70 = 1950 > 1000 (Over budget)
            "operational_notes": "None"
        }
    }
    res = client.post("/api/economics/compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["offer_a"]["contribution_per_order"] == 50.0
    assert data["offer_b"]["contribution_per_order"] == 50.0
    assert data["higher_contribution_offer"] is None
    assert "Both offers generate identical unit contribution" in data["comparison_summary"]
    assert data["offer_a"]["is_budget_compliant"] is True
    assert data["offer_b"]["is_budget_compliant"] is False


def test_experiment_task_not_found_handling(client):
    res = client.patch(
        "/api/experiments/exp_nonexistent/tasks/task_nonexistent",
        json={"is_completed": True}
    )
    assert res.status_code == 404

    del_res = client.delete("/api/experiments/exp_nonexistent/tasks/task_nonexistent")
    assert del_res.status_code == 404


def test_export_csv_missing_research(client):
    res = client.get("/api/research/res_nonexistent/export-csv")
    assert res.status_code == 404
