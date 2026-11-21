"""
DukaanPulse Domain & API Models
"""
import math
from datetime import datetime
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, field_validator


class MerchantEconomicsInput(BaseModel):
    selling_price: float = Field(..., gt=0, description="Proposed selling price per bundle in INR")
    ingredient_cost: float = Field(..., ge=0, description="Ingredient cost per bundle in INR")
    packaging_cost: float = Field(0.0, ge=0, description="Packaging cost per bundle in INR")
    other_variable_cost: float = Field(0.0, ge=0, description="Other variable cost per bundle in INR")
    one_time_pilot_cost: float = Field(0.0, ge=0, description="One-time pilot cost (e.g. chalkboard, test batch) in INR")
    max_pilot_budget: float = Field(..., gt=0, le=1000000, description="Maximum pilot budget in INR")
    planned_quantity: Optional[int] = Field(None, ge=1, le=10000, description="Planned test bundle quantity")
    operational_constraints: Optional[str] = Field("", max_length=500, description="e.g. existing kitchen staff only")
    baseline_daily_orders: Optional[int] = Field(None, ge=0, description="Optional baseline daily orders")

    @field_validator("selling_price", "ingredient_cost", "packaging_cost", "other_variable_cost", "one_time_pilot_cost", "max_pilot_budget")
    @classmethod
    def validate_finite(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("Numeric values must be finite numbers")
        return v


class EconomicsResult(BaseModel):
    variable_cost_per_order: float = Field(..., description="ingredient + packaging + other variable costs")
    contribution_per_order: float = Field(..., description="selling_price - variable_cost_per_order")
    gross_margin_pct: Optional[float] = Field(None, description="(contribution / selling_price) * 100")
    orders_to_cover_setup_cost: Optional[int] = Field(
        None, description="ceil(one_time_pilot_cost / contribution_per_order) if contribution > 0 else null"
    )
    estimated_total_pilot_cost: Optional[float] = Field(
        None, description="one_time_pilot_cost + (planned_quantity * variable_cost_per_order) if quantity entered"
    )
    is_budget_compliant: Optional[bool] = Field(
        None, description="True if estimated_total_pilot_cost <= max_pilot_budget"
    )
    is_viable: bool = Field(..., description="True if contribution_per_order > 0 and within budget")
    recommendation: Literal["viable", "revise_costs", "negative_contribution", "over_budget", "unviable"]
    guidance: str = Field(..., description="Honest managerial advice for merchant")
    calculated_at: str


class ResearchRequest(BaseModel):
    category: str = Field(..., min_length=2, max_length=100, description="Business category, e.g. Cafe, Bakery")
    locality: str = Field(..., min_length=2, max_length=150, description="Locality, e.g. HSR Layout, Bengaluru")
    question: str = Field(..., min_length=5, max_length=300, description="Business question to research")
    budget: float = Field(..., gt=0, le=1000000, description="Experiment budget ceiling in INR")
    constraints: Optional[str] = Field("", max_length=500, description="Constraints, e.g. no new equipment")
    economics: Optional[MerchantEconomicsInput] = Field(None, description="Optional owner-entered unit economics")

    @field_validator("category", "locality", "question")
    @classmethod
    def clean_strings(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Field cannot be empty or blank")
        return s


class EvidenceItem(BaseModel):
    evidence_id: str = Field(..., description="Stable unique ID in this run, e.g. E1, E2")
    url: str = Field(..., description="Normalized source URL (HTTP/HTTPS only)")
    title: str = Field(..., description="Cleaned title of source page")
    snippet: str = Field(..., description="Exact returned excerpt/snippet text")
    query: str = Field(..., description="Original search query that fetched this item")
    retrieved_at: str = Field(..., description="ISO 8601 retrieval timestamp")
    domain: Optional[str] = Field(None, description="Extracted domain hostname")
    source_date: Optional[str] = Field(None, description="Reported publication/update date if available")
    locality_match: Optional[str] = Field(None, description="Locality relevance reason or heuristic")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("Only http:// and https:// URLs are allowed")
        return v


class SupportingQuote(BaseModel):
    evidence_id: str
    quote: str


class Observation(BaseModel):
    claim: str = Field(..., min_length=3, description="Narrow factual observation supported by evidence")
    evidence_ids: List[str] = Field(..., min_length=1, description="List of referenced evidence IDs")
    supporting_quotes: List[SupportingQuote] = Field(..., min_length=1, description="Exact quotes and source IDs")


class Experiment(BaseModel):
    title: str = Field(..., min_length=3, description="Practical title of the test")
    hypothesis: Optional[str] = Field(None, description="Specific hypothesis this experiment tests")
    steps: List[str] = Field(..., min_length=1, description="Concrete sequential actions")
    validation_step: str = Field("Verify customer interest before spending pilot funds", description="Validation step before spending any money")
    duration_days: int = Field(3, ge=1, le=30, description="Proposed experiment duration in days")
    budget_ceiling: float = Field(..., gt=0, description="Strict spending ceiling in INR")
    estimated_cost: Optional[float] = Field(None, description="Estimated cost if known; null requires owner confirmation")
    cost_note: str = Field(..., description="Explicit note on cost confirmation or uncertainty")
    success_criterion: str = Field(..., description="Owner-approved measurable target metric")
    stop_conditions: List[str] = Field(default_factory=list, description="Conditions under which to stop or revise")
    metrics: List[str] = Field(default_factory=lambda: ["orders", "revenue", "variable_cost"])
    assumptions_snapshot: Optional[Dict[str, Any]] = Field(None, description="Owner-entered economics at time of generation")


class ResearchReport(BaseModel):
    status: Literal["ready", "insufficient_evidence", "needs_owner_input"]
    observations: List[Observation] = Field(default_factory=list)
    unknowns: List[str] = Field(default_factory=list)
    hypothesis: str = Field(..., description="Tentative business opportunity, not proven demand")
    economics: Optional[EconomicsResult] = Field(None, description="Deterministic economics evaluation if owner supplied costs")
    experiment: Optional[Experiment] = None
    limitations: List[str] = Field(default_factory=list)
    is_stale: bool = Field(False, description="Flag indicating previously generated recommendation is stale due to cost changes")
    stale_reason: Optional[str] = Field(None, description="Explanation of why advice became stale")


class ResearchResponse(BaseModel):
    research_id: str
    category: str
    locality: str
    question: str
    budget: float
    constraints: Optional[str] = ""
    created_at: str
    report: ResearchReport
    evidence: List[EvidenceItem]


class ExperimentCreate(BaseModel):
    research_id: str


class OutcomeInput(BaseModel):
    date: str = Field(..., description="Date of measurement, YYYY-MM-DD")
    orders: int = Field(..., ge=0, description="Number of test orders")
    revenue: float = Field(..., ge=0, description="Gross test revenue in INR")
    variable_cost: float = Field(..., ge=0, description="Variable costs incurred in INR")
    notes: Optional[str] = Field("", max_length=500, description="Operational merchant notes")

    @field_validator("revenue", "variable_cost")
    @classmethod
    def validate_finite(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("Numeric values must be finite numbers")
        return v


class OutcomeRecord(OutcomeInput):
    id: str
    experiment_id: str
    contribution: float = Field(..., description="revenue - variable_cost")
    created_at: str


class ExperimentRecord(BaseModel):
    id: str
    research_id: str
    category: str
    locality: str
    title: str
    hypothesis: Optional[str] = None
    steps: List[str]
    validation_step: str = ""
    duration_days: int = 3
    budget_ceiling: float
    cost_note: str
    success_criterion: str
    stop_conditions: List[str] = Field(default_factory=list)
    assumptions_snapshot: Optional[Dict[str, Any]] = None
    created_at: str
    status: str = "active"
    measurements: List[OutcomeRecord] = Field(default_factory=list)
    total_orders: int = 0
    total_revenue: float = 0.0
    total_variable_cost: float = 0.0
    total_contribution: float = 0.0
    gross_margin_pct: Optional[float] = None


class HealthResponse(BaseModel):
    status: str
    you_search_configured: bool
    llm_configured: bool
    llm_provider: str
    database_ok: bool


class ResearchRunSummary(BaseModel):
    id: str
    category: str
    locality: str
    question: str
    budget: float
    created_at: str
    report_status: str
    has_accepted_experiment: bool
    experiment_id: Optional[str] = None


class ExperimentTask(BaseModel):
    id: str
    experiment_id: str
    text: str
    is_completed: bool = False
    is_owner_added: bool = False
    created_at: str


class ExperimentTaskCreate(BaseModel):
    text: str = Field(..., min_length=2, max_length=250)


class ExperimentTaskUpdate(BaseModel):
    is_completed: Optional[bool] = None
    text: Optional[str] = Field(None, min_length=2, max_length=250)


class OfferProfile(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    selling_price: float = Field(..., gt=0)
    ingredient_cost: float = Field(..., ge=0)
    packaging_cost: float = Field(0.0, ge=0)
    other_variable_cost: float = Field(0.0, ge=0)
    one_time_pilot_cost: float = Field(0.0, ge=0)
    planned_quantity: int = Field(..., ge=1, le=10000)
    operational_notes: Optional[str] = Field("", max_length=500)


class OfferComparisonRequest(BaseModel):
    offer_a: OfferProfile
    offer_b: OfferProfile
    max_budget: float = Field(..., gt=0, le=1000000)


class OfferComparisonItemResult(BaseModel):
    name: str
    selling_price: float
    variable_cost_per_order: float
    contribution_per_order: float
    gross_margin_pct: Optional[float]
    estimated_pilot_cost: float
    orders_to_cover_setup: Optional[int]
    is_budget_compliant: bool
    budget_variance: float
    operational_notes: str


class OfferComparisonResponse(BaseModel):
    id: str
    max_budget: float
    offer_a: OfferComparisonItemResult
    offer_b: OfferComparisonItemResult
    higher_contribution_offer: Optional[str]
    comparison_summary: str
    disclaimer: str
    created_at: str
