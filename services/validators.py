"""
DukaanPulse Grounding & Citation Validation Engine
Enforces exact quote-in-excerpt matching, evidence ID existence,
budget ceiling conformity, and structural validity.
"""
import re
from typing import List, Dict, Optional, Set
from services.models import ResearchReport, EvidenceItem


class GroundedValidationError(Exception):
    """Raised when AI synthesis fails grounding, schema, or citation rules."""
    def __init__(self, message: str, error_details: Optional[List[str]] = None):
        super().__init__(message)
        self.message = message
        self.error_details = error_details or [message]

    def __str__(self) -> str:
        if self.error_details:
            return f"{self.message}: " + "; ".join(self.error_details)
        return self.message


def normalize_whitespace(text: str) -> str:
    """Collapses whitespace and strips leading/trailing spaces."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def validate_report(
    report_dict: dict,
    evidence_items: List[EvidenceItem],
    max_budget: float
) -> ResearchReport:
    """
    Strictly validates raw report dict against grounding contracts:
    1. Schema conforms to ResearchReport
    2. Evidence IDs actually exist in this run
    3. Quotes exist verbatim (with whitespace normalization) in cited snippets
    4. Budget ceiling does not exceed input budget
    5. Required fields and notes are present
    """
    errors: List[str] = []

    # 1. Pydantic schema validation
    try:
        report = ResearchReport.model_validate(report_dict)
    except Exception as e:
        raise GroundedValidationError(f"Schema validation error: {str(e)}", [str(e)])

    evidence_map: Dict[str, EvidenceItem] = {e.evidence_id: e for e in evidence_items}
    valid_eids: Set[str] = set(evidence_map.keys())

    # 2. Check for insufficient evidence status
    if report.status == "insufficient_evidence":
        if report.experiment is not None:
            errors.append("When status is 'insufficient_evidence', experiment must be null.")
        if errors:
            raise GroundedValidationError("Report validation failed", errors)
        return report

    # 3. Check for needs_owner_input status
    if report.status == "needs_owner_input":
        # Observations may be present and must be validated if present
        for i, obs in enumerate(report.observations):
            for eid in obs.evidence_ids:
                if eid not in valid_eids:
                    errors.append(f"Observation {i+1} references invalid evidence ID '{eid}'.")
            for sq in obs.supporting_quotes:
                if sq.evidence_id in valid_eids:
                    norm_snippet = normalize_whitespace(evidence_map[sq.evidence_id].snippet).lower()
                    norm_quote = normalize_whitespace(sq.quote).lower()
                    if norm_quote not in norm_snippet:
                        errors.append(f"Quote '{sq.quote}' not found in evidence '{sq.evidence_id}'.")
        if errors:
            raise GroundedValidationError("Validation failed for needs_owner_input report", errors)
        return report

    # 4. For 'ready' status, validate observations and citations
    if not report.observations:
        errors.append("Report status is 'ready' but no observations were provided.")

    for i, obs in enumerate(report.observations):
        for eid in obs.evidence_ids:
            if eid not in valid_eids:
                errors.append(f"Observation {i+1} references invented or unknown evidence ID '{eid}'.")

        if not obs.supporting_quotes:
            errors.append(f"Observation {i+1} has no supporting quotes.")

        for sq in obs.supporting_quotes:
            if sq.evidence_id not in valid_eids:
                errors.append(f"Supporting quote references invalid evidence ID '{sq.evidence_id}'.")
                continue

            target_evidence = evidence_map[sq.evidence_id]
            norm_snippet = normalize_whitespace(target_evidence.snippet).lower()
            norm_quote = normalize_whitespace(sq.quote).lower()

            if not norm_quote:
                errors.append(f"Empty quote supplied for evidence ID '{sq.evidence_id}'.")
            elif norm_quote not in norm_snippet:
                errors.append(
                    f"Quote '{sq.quote}' not found in returned excerpt for evidence ID '{sq.evidence_id}'."
                )

    # 5. Validate experiment
    if not report.experiment:
        errors.append("Report status is 'ready' but no experiment was proposed.")
    else:
        exp = report.experiment
        if exp.budget_ceiling > max_budget:
            errors.append(
                f"Experiment budget ceiling (₹{exp.budget_ceiling}) exceeds input budget limit (₹{max_budget})."
            )
        if not exp.steps:
            errors.append("Experiment must contain at least one actionable step.")
        if not exp.cost_note or not exp.cost_note.strip():
            errors.append("Experiment must contain a cost note confirming owner costs.")
        if not exp.success_criterion or not exp.success_criterion.strip():
            errors.append("Experiment must contain an owner-approved measurable success criterion.")
        if not exp.validation_step or not exp.validation_step.strip():
            errors.append("Experiment must contain a pre-spending validation step.")

    if errors:
        raise GroundedValidationError("Grounding and citation verification failed", errors)

    return report
