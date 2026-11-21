"""
DukaanPulse Deterministic Merchant Economics Engine
Computes variable costs, contribution per order, break-even orders,
budget compliance, and detects stale recommendation assumptions.
"""
import math
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from services.models import MerchantEconomicsInput, EconomicsResult


class EconomicsValidationError(Exception):
    """Raised when economics inputs are invalid, non-finite, or negative."""
    pass


def calculate_economics(inputs: MerchantEconomicsInput) -> EconomicsResult:
    """
    Executes pure deterministic managerial economics in Python.
    Strictly protects against division by zero, non-finite values, and negative inputs.
    """
    if inputs.selling_price <= 0:
        raise EconomicsValidationError("Selling price must be greater than zero.")
    if inputs.ingredient_cost < 0 or inputs.packaging_cost < 0 or inputs.other_variable_cost < 0:
        raise EconomicsValidationError("Variable costs cannot be negative.")
    if inputs.one_time_pilot_cost < 0:
        raise EconomicsValidationError("One-time pilot cost cannot be negative.")
    if inputs.max_pilot_budget <= 0:
        raise EconomicsValidationError("Maximum pilot budget must be greater than zero.")

    # 1. Variable cost per order
    variable_cost_per_order = round(
        inputs.ingredient_cost + inputs.packaging_cost + inputs.other_variable_cost, 2
    )

    # 2. Contribution per order = selling price - variable cost
    contribution_per_order = round(inputs.selling_price - variable_cost_per_order, 2)

    # 3. Gross margin % on selling price
    gross_margin_pct = round((contribution_per_order / inputs.selling_price) * 100, 2)

    # 4. Break-even setup cost coverage
    orders_to_cover_setup_cost: Optional[int] = None
    if contribution_per_order > 0:
        if inputs.one_time_pilot_cost > 0:
            orders_to_cover_setup_cost = math.ceil(inputs.one_time_pilot_cost / contribution_per_order)
        else:
            orders_to_cover_setup_cost = 0
    else:
        # Never divide by zero or negative contribution!
        orders_to_cover_setup_cost = None

    # 5. Budget Check
    estimated_total_pilot_cost: Optional[float] = None
    is_budget_compliant: Optional[bool] = None
    if inputs.planned_quantity is not None:
        if inputs.planned_quantity < 1:
            raise EconomicsValidationError("Planned quantity must be at least 1.")
        estimated_total_pilot_cost = round(
            inputs.one_time_pilot_cost + (inputs.planned_quantity * variable_cost_per_order), 2
        )
        is_budget_compliant = estimated_total_pilot_cost <= inputs.max_pilot_budget

    # 6. Managerial Viability & Recommendation
    now_str = datetime.utcnow().isoformat() + "Z"

    if contribution_per_order < 0:
        return EconomicsResult(
            variable_cost_per_order=variable_cost_per_order,
            contribution_per_order=contribution_per_order,
            gross_margin_pct=gross_margin_pct,
            orders_to_cover_setup_cost=None,
            estimated_total_pilot_cost=estimated_total_pilot_cost,
            is_budget_compliant=is_budget_compliant,
            is_viable=False,
            recommendation="negative_contribution",
            guidance=(
                f"DO NOT LAUNCH. Each bundle sold loses ₹{abs(contribution_per_order):.2f}. "
                f"Variable costs (₹{variable_cost_per_order:.2f}) exceed selling price (₹{inputs.selling_price:.2f}). "
                "You must renegotiate ingredient supplier costs or raise the offer price before piloting."
            ),
            calculated_at=now_str
        )
    elif contribution_per_order == 0:
        return EconomicsResult(
            variable_cost_per_order=variable_cost_per_order,
            contribution_per_order=0.0,
            gross_margin_pct=0.0,
            orders_to_cover_setup_cost=None,
            estimated_total_pilot_cost=estimated_total_pilot_cost,
            is_budget_compliant=is_budget_compliant,
            is_viable=False,
            recommendation="revise_costs",
            guidance=(
                "DO NOT LAUNCH. Each bundle breaks exactly even on variable costs (₹0 contribution). "
                "Any one-time setup expenses will cause a guaranteed net loss."
            ),
            calculated_at=now_str
        )
    elif is_budget_compliant is False:
        return EconomicsResult(
            variable_cost_per_order=variable_cost_per_order,
            contribution_per_order=contribution_per_order,
            gross_margin_pct=gross_margin_pct,
            orders_to_cover_setup_cost=orders_to_cover_setup_cost,
            estimated_total_pilot_cost=estimated_total_pilot_cost,
            is_budget_compliant=False,
            is_viable=False,
            recommendation="over_budget",
            guidance=(
                f"OVER BUDGET. Estimated pilot cost (₹{estimated_total_pilot_cost:.2f}) exceeds "
                f"budget ceiling of ₹{inputs.max_pilot_budget:.2f}. Reduce test batch quantity or signage/setup cost."
            ),
            calculated_at=now_str
        )
    else:
        return EconomicsResult(
            variable_cost_per_order=variable_cost_per_order,
            contribution_per_order=contribution_per_order,
            gross_margin_pct=gross_margin_pct,
            orders_to_cover_setup_cost=orders_to_cover_setup_cost,
            estimated_total_pilot_cost=estimated_total_pilot_cost,
            is_budget_compliant=is_budget_compliant,
            is_viable=True,
            recommendation="viable",
            guidance=(
                f"FINANCIALLY VIABLE. Generates positive contribution of ₹{contribution_per_order:.2f} per bundle "
                f"({gross_margin_pct}% gross margin). {orders_to_cover_setup_cost or 0} orders required to recover "
                f"one-time setup cost of ₹{inputs.one_time_pilot_cost:.2f}."
            ),
            calculated_at=now_str
        )


def check_stale_advice(
    new_economics: MerchantEconomicsInput,
    approved_snapshot: Optional[Dict[str, Any]]
) -> Tuple[bool, Optional[str]]:
    """
    Checks if newly entered cost parameters deviate from the approved snapshot.
    Prevents old recommendations from remaining active when underlying unit economics changed.
    """
    if not approved_snapshot:
        return False, None

    old_price = approved_snapshot.get("selling_price")
    old_ing = approved_snapshot.get("ingredient_cost")
    old_pkg = approved_snapshot.get("packaging_cost", 0.0)
    old_other = approved_snapshot.get("other_variable_cost", 0.0)
    old_budget = approved_snapshot.get("max_pilot_budget")

    if old_price is None or old_ing is None:
        return False, None

    # Check for meaningful changes
    changes = []
    if abs(new_economics.selling_price - old_price) > 0.01:
        changes.append(f"selling price changed from ₹{old_price} to ₹{new_economics.selling_price}")
    if abs(new_economics.ingredient_cost - old_ing) > 0.01:
        changes.append(f"ingredient cost changed from ₹{old_ing} to ₹{new_economics.ingredient_cost}")
    if abs(new_economics.packaging_cost - old_pkg) > 0.01:
        changes.append(f"packaging cost changed from ₹{old_pkg} to ₹{new_economics.packaging_cost}")
    if abs(new_economics.other_variable_cost - old_other) > 0.01:
        changes.append(f"other variable cost changed from ₹{old_other} to ₹{new_economics.other_variable_cost}")
    if old_budget and abs(new_economics.max_pilot_budget - old_budget) > 0.01:
        changes.append(f"budget ceiling changed from ₹{old_budget} to ₹{new_economics.max_pilot_budget}")

    if changes:
        return True, "Cost assumptions altered (" + ", ".join(changes) + "). Previously approved advice is STALE."
    return False, None
