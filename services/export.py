"""
DukaanPulse CSV Export Generator
Formats research runs, evidence ledgers, and experiment trackers into
clean, injection-safe CSV spreadsheets.
"""
from typing import List, Any
from services.models import ResearchResponse, ExperimentRecord, ExperimentTask


def escape_csv_cell(val: Any) -> str:
    """
    Escapes a single CSV cell:
    - Escapes double quotes with double quotes
    - Wraps in double quotes if commas or newlines present
    - Prepend single quote (') if starts with formula trigger (=, +, -, @, \\t, \\r)
      to protect against spreadsheet formula execution.
    """
    if val is None:
        return ""
    s = str(val)
    # Formula injection defense
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        s = "'" + s
    if any(c in s for c in (",", '"', "\n", "\r")):
        s = '"' + s.replace('"', '""') + '"'
    return s


def generate_research_csv(research: ResearchResponse) -> str:
    """Generates a multi-section, injection-safe CSV for a research run."""
    lines: List[str] = []

    def add_row(*cells):
        lines.append(",".join(escape_csv_cell(c) for c in cells))

    # 1. Header & Summary
    add_row("SECTION", "RESEARCH SUMMARY")
    add_row("Research ID", research.research_id)
    add_row("Category", research.category)
    add_row("Locality", research.locality)
    add_row("Business Question", research.question)
    add_row("Budget Ceiling (INR)", research.budget)
    add_row("Constraints", research.constraints or "None specified")
    add_row("Created At (UTC)", research.created_at)
    add_row("Report Status", research.report.status)
    add_row("Hypothesis", research.report.hypothesis)
    add_row("")

    # 2. Managerial Economics
    add_row("SECTION", "OWNER-ENTERED UNIT ECONOMICS")
    econ = research.report.economics
    if econ:
        add_row("Variable Cost Per Order (INR)", econ.variable_cost_per_order)
        add_row("Contribution Per Order (INR)", econ.contribution_per_order)
        add_row("Gross Margin (%)", f"{econ.gross_margin_pct or 0}%")
        add_row("Orders to Cover Setup", econ.orders_to_cover_setup_cost if econ.orders_to_cover_setup_cost is not None else "N/A (Non-positive contribution)")
        add_row("Estimated Pilot Cost (INR)", econ.estimated_total_pilot_cost or "N/A")
        add_row("Budget Compliant", "Yes" if econ.is_budget_compliant else "No")
        add_row("Recommendation", econ.recommendation)
        add_row("Guidance", econ.guidance)
    else:
        add_row("Status", "No owner cost assumptions provided for this run")
    add_row("")

    # 3. Factual Observations
    add_row("SECTION", "FACTUAL MARKET OBSERVATIONS")
    add_row("Observation #", "Claim", "Referenced Evidence IDs", "Supporting Verbatim Quotes")
    for idx, obs in enumerate(research.report.observations, 1):
        quotes_str = " | ".join(f'"{sq.quote}" ({sq.evidence_id})' for sq in obs.supporting_quotes)
        add_row(idx, obs.claim, " ".join(obs.evidence_ids), quotes_str)
    add_row("")

    # 4. Evidence Ledger
    add_row("SECTION", "VERIFIED EVIDENCE LEDGER")
    add_row("Evidence ID", "Source Title", "Domain", "Source URL", "Retrieved Timestamp", "Publication Date", "Locality Match", "Returned Excerpt")
    for item in research.evidence:
        add_row(
            item.evidence_id,
            item.title,
            item.domain or "",
            item.url,
            item.retrieved_at,
            item.source_date or "Not reported",
            item.locality_match or "",
            item.snippet
        )

    return "\n".join(lines)


def generate_experiment_csv(experiment: ExperimentRecord, tasks: List[ExperimentTask]) -> str:
    """Generates an injection-safe CSV for an active experiment, outcome ledger, and task checklist."""
    lines: List[str] = []

    def add_row(*cells):
        lines.append(",".join(escape_csv_cell(c) for c in cells))

    # 1. Summary
    add_row("SECTION", "EXPERIMENT SPECIFICATION")
    add_row("Experiment ID", experiment.id)
    add_row("Research ID", experiment.research_id)
    add_row("Category", experiment.category)
    add_row("Locality", experiment.locality)
    add_row("Title", experiment.title)
    add_row("Hypothesis", experiment.hypothesis or "")
    add_row("Validation Step", experiment.validation_step)
    add_row("Success Criterion", experiment.success_criterion)
    add_row("Budget Ceiling (INR)", experiment.budget_ceiling)
    add_row("Status", experiment.status)
    add_row("Created At (UTC)", experiment.created_at)
    add_row("")

    # 2. Cumulative Financial Performance
    add_row("SECTION", "CUMULATIVE PERFORMANCE KPIS")
    add_row("Total Test Orders", experiment.total_orders)
    add_row("Total Recorded Revenue (INR)", experiment.total_revenue)
    add_row("Total Variable Costs (INR)", experiment.total_variable_cost)
    add_row("Total Contribution (Gross Margin INR)", experiment.total_contribution)
    add_row("Gross Margin (%)", f"{experiment.gross_margin_pct or 0}%")
    add_row("")

    # 3. Actionable Task Checklist
    add_row("SECTION", "ACTIONABLE TASK CHECKLIST")
    add_row("Task ID", "Type", "Status", "Task Description", "Created At")
    for t in tasks:
        add_row(
            t.id,
            "Owner Added" if t.is_owner_added else "AI Proposed",
            "Completed" if t.is_completed else "Pending",
            t.text,
            t.created_at
        )
    add_row("")

    # 4. Daily Measurement Ledger
    add_row("SECTION", "DAILY MEASUREMENT LEDGER")
    add_row("Date", "Orders Sold", "Revenue (INR)", "Variable Cost (INR)", "Contribution (INR)", "Operational Notes")
    for m in experiment.measurements:
        add_row(
            m.date,
            m.orders,
            m.revenue,
            m.variable_cost,
            m.contribution,
            m.notes or ""
        )

    return "\n".join(lines)
