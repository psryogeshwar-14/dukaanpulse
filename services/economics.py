"""
DukaanPulse Deterministic Merchant Economics Engine
Computes variable costs, contribution per order, break-even orders,
budget compliance, and detects stale recommendation assumptions.
"""
import math
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from services.models import (
    MerchantEconomicsInput, EconomicsResult,
    OfferProfile, OfferComparisonRequest, OfferComparisonItemResult, OfferComparisonResponse
)


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


def evaluate_offer_item(offer: OfferProfile, max_budget: float) -> OfferComparisonItemResult:
    """Calculates deterministic economics for an individual offer profile."""
    if offer.selling_price <= 0:
        raise EconomicsValidationError(f"Offer '{offer.name}': selling price must be greater than zero.")
    if offer.ingredient_cost < 0 or offer.packaging_cost < 0 or offer.other_variable_cost < 0:
        raise EconomicsValidationError(f"Offer '{offer.name}': variable costs cannot be negative.")
    if offer.one_time_pilot_cost < 0:
        raise EconomicsValidationError(f"Offer '{offer.name}': one-time pilot cost cannot be negative.")
    if offer.planned_quantity < 1:
        raise EconomicsValidationError(f"Offer '{offer.name}': planned quantity must be at least 1.")

    var_cost = round(offer.ingredient_cost + offer.packaging_cost + offer.other_variable_cost, 2)
    contrib = round(offer.selling_price - var_cost, 2)
    margin = round((contrib / offer.selling_price) * 100, 2) if offer.selling_price > 0 else 0.0
    est_spend = round(offer.one_time_pilot_cost + (offer.planned_quantity * var_cost), 2)
    is_compliant = est_spend <= max_budget
    budget_variance = round(max_budget - est_spend, 2)

    orders_to_cover: Optional[int] = None
    if contrib > 0:
        orders_to_cover = math.ceil(offer.one_time_pilot_cost / contrib) if offer.one_time_pilot_cost > 0 else 0

    return OfferComparisonItemResult(
        name=offer.name,
        selling_price=round(offer.selling_price, 2),
        variable_cost_per_order=var_cost,
        contribution_per_order=contrib,
        gross_margin_pct=margin,
        estimated_pilot_cost=est_spend,
        orders_to_cover_setup=orders_to_cover,
        is_budget_compliant=is_compliant,
        budget_variance=budget_variance,
        operational_notes=offer.operational_notes.strip() if offer.operational_notes else "None entered"
    )


def compare_offers(req: OfferComparisonRequest) -> OfferComparisonResponse:
    """
    Compares two owner-defined offers under entered cost assumptions.
    Strictly avoids calling an offer 'best' solely due to contribution.
    """
    if req.max_budget <= 0:
        raise EconomicsValidationError("Maximum pilot budget must be greater than zero.")

    res_a = evaluate_offer_item(req.offer_a, req.max_budget)
    res_b = evaluate_offer_item(req.offer_b, req.max_budget)

    higher = None
    if res_a.contribution_per_order > res_b.contribution_per_order:
        higher = req.offer_a.name
        summary = (
            f"'{req.offer_a.name}' yields a higher contribution per order (₹{res_a.contribution_per_order:.2f} vs ₹{res_b.contribution_per_order:.2f}) "
            f"under entered unit cost assumptions."
        )
    elif res_b.contribution_per_order > res_a.contribution_per_order:
        higher = req.offer_b.name
        summary = (
            f"'{req.offer_b.name}' yields a higher contribution per order (₹{res_b.contribution_per_order:.2f} vs ₹{res_a.contribution_per_order:.2f}) "
            f"under entered unit cost assumptions."
        )
    else:
        summary = (
            f"Both offers generate identical unit contribution of ₹{res_a.contribution_per_order:.2f} per order under entered assumptions."
        )

    return OfferComparisonResponse(
        id=f"cmp_{uuid.uuid4().hex[:12]}",
        max_budget=req.max_budget,
        offer_a=res_a,
        offer_b=res_b,
        higher_contribution_offer=higher,
        comparison_summary=summary,
        disclaimer=(
            "Calculated strictly under owner-entered managerial cost assumptions. "
            "Customer demand, operational capacity, and market feasibility are not established by this comparative model."
        ),
        created_at=datetime.utcnow().isoformat() + "Z"
    )
