"""
Unit tests for DukaanPulse Deterministic Economics Engine
"""
import pytest
from services.models import MerchantEconomicsInput
from services.economics import (
    calculate_economics, check_stale_advice, EconomicsValidationError
)


def test_positive_contribution():
    inp = MerchantEconomicsInput(
        selling_price=179.0,
        ingredient_cost=50.0,
        packaging_cost=10.0,
        other_variable_cost=5.0,
        one_time_pilot_cost=450.0,
        max_pilot_budget=2000.0,
        planned_quantity=20
    )
    res = calculate_economics(inp)
    assert res.variable_cost_per_order == 65.0
    assert res.contribution_per_order == 114.0
    assert res.gross_margin_pct == pytest.approx(63.69, 0.01)
    assert res.orders_to_cover_setup_cost == 4  # ceil(450 / 114) = 4
    assert res.estimated_total_pilot_cost == 450.0 + (20 * 65.0)  # 1750.0
    assert res.is_budget_compliant is True
    assert res.is_viable is True
    assert res.recommendation == "viable"


def test_zero_setup_cost():
    inp = MerchantEconomicsInput(
        selling_price=150.0,
        ingredient_cost=50.0,
        packaging_cost=10.0,
        other_variable_cost=0.0,
        one_time_pilot_cost=0.0,
        max_pilot_budget=1000.0
    )
    res = calculate_economics(inp)
    assert res.contribution_per_order == 90.0
    assert res.orders_to_cover_setup_cost == 0
    assert res.is_viable is True


def test_zero_contribution_no_division_by_zero():
    inp = MerchantEconomicsInput(
        selling_price=100.0,
        ingredient_cost=80.0,
        packaging_cost=20.0,
        other_variable_cost=0.0,
        one_time_pilot_cost=500.0,
        max_pilot_budget=2000.0
    )
    res = calculate_economics(inp)
    assert res.contribution_per_order == 0.0
    assert res.orders_to_cover_setup_cost is None
    assert res.is_viable is False
    assert res.recommendation == "revise_costs"
    assert "breaks exactly even" in res.guidance.lower()


def test_negative_contribution():
    inp = MerchantEconomicsInput(
        selling_price=80.0,
        ingredient_cost=85.0,
        packaging_cost=15.0,
        other_variable_cost=0.0,
        one_time_pilot_cost=500.0,
        max_pilot_budget=2000.0
    )
    res = calculate_economics(inp)
    assert res.contribution_per_order == -20.0
    assert res.orders_to_cover_setup_cost is None
    assert res.is_viable is False
    assert res.recommendation == "negative_contribution"
    assert "DO NOT LAUNCH" in res.guidance


def test_over_budget_pilot():
    inp = MerchantEconomicsInput(
        selling_price=179.0,
        ingredient_cost=50.0,
        packaging_cost=10.0,
        other_variable_cost=5.0,
        one_time_pilot_cost=600.0,
        max_pilot_budget=2000.0,
        planned_quantity=30  # 600 + (30 * 65) = 2550 > 2000
    )
    res = calculate_economics(inp)
    assert res.estimated_total_pilot_cost == 2550.0
    assert res.is_budget_compliant is False
    assert res.is_viable is False
    assert res.recommendation == "over_budget"


def test_invalid_negative_or_zero_price():
    with pytest.raises(Exception):
        MerchantEconomicsInput(
            selling_price=-10.0,
            ingredient_cost=20.0,
            max_pilot_budget=1000.0
        )

    with pytest.raises(Exception):
        MerchantEconomicsInput(
            selling_price=0.0,
            ingredient_cost=20.0,
            max_pilot_budget=1000.0
        )


def test_stale_advice_detection():
    approved = {
        "selling_price": 179.0,
        "ingredient_cost": 50.0,
        "packaging_cost": 10.0,
        "other_variable_cost": 5.0,
        "max_pilot_budget": 2000.0
    }

    # Case A: Same costs -> not stale
    same_inp = MerchantEconomicsInput(
        selling_price=179.0,
        ingredient_cost=50.0,
        packaging_cost=10.0,
        other_variable_cost=5.0,
        max_pilot_budget=2000.0
    )
    is_stale, reason = check_stale_advice(same_inp, approved)
    assert is_stale is False
    assert reason is None

    # Case B: Ingredient cost raised to 110 -> STALE
    changed_inp = MerchantEconomicsInput(
        selling_price=179.0,
        ingredient_cost=110.0,
        packaging_cost=10.0,
        other_variable_cost=5.0,
        max_pilot_budget=2000.0
    )
    is_stale, reason = check_stale_advice(changed_inp, approved)
    assert is_stale is True
    assert "ingredient cost changed" in reason.lower()
    assert "STALE" in reason
