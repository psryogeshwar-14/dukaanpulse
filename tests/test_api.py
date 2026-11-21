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
