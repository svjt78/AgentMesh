"""
Coverage Rules Tool - Determine coverage eligibility based on policy and claim.

Demonstrates: Business rules engine pattern for coverage determination.
"""

from typing import Dict, Any, List


def execute_coverage_rules(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Determine coverage eligibility based on policy terms and claim details.

    Args:
        parameters: Dict with policy_data and claim_data

    Returns:
        Coverage determination with reasoning
    """
    # Extract parameters
    policy_data = parameters.get("policy_data", {})
    claim_data = parameters.get("claim_data", {})

    if not policy_data:
        raise ValueError("Missing required parameter: policy_data")

    if not claim_data:
        raise ValueError("Missing required parameter: claim_data")

    # Extract key fields
    loss_type = claim_data.get("loss_type", "").lower()
    claim_amount = claim_data.get("claim_amount", 0)
    policy_status = policy_data.get("status", "").lower()
    coverage_limits = policy_data.get("coverage_limits", {})
    deductibles = policy_data.get("deductibles", {})
    excluded_perils = policy_data.get("excluded_perils", [])

    coverage_determination = "unknown"
    coverage_amount = 0
    deductible_amount = 0
    reasons = []
    exclusions_triggered = []

    # Rule 1: Policy must be active
    if policy_status != "active":
        coverage_determination = "denied"
        reasons.append({
            "rule_id": "COV-001",
            "rule_name": "Policy Status Check",
            "result": "fail",
            "message": f"Policy status is '{policy_status}', must be 'active' for coverage"
        })
        return _build_response(
            coverage_determination, coverage_amount, deductible_amount,
            reasons, exclusions_triggered, policy_data, claim_data
        )

    reasons.append({
        "rule_id": "COV-001",
        "rule_name": "Policy Status Check",
        "result": "pass",
        "message": "Policy is active"
    })

    # Rule 2: Check for excluded perils
    for excluded_peril in excluded_perils:
        if excluded_peril.lower() in loss_type or loss_type in excluded_peril.lower():
            coverage_determination = "denied"
            exclusions_triggered.append({
                "exclusion": excluded_peril,
                "message": f"Loss type '{loss_type}' is excluded under policy terms"
            })
            reasons.append({
                "rule_id": "COV-002",
                "rule_name": "Peril Exclusion Check",
                "result": "fail",
                "message": f"Loss type '{loss_type}' matches excluded peril '{excluded_peril}'"
            })
            return _build_response(
                coverage_determination, coverage_amount, deductible_amount,
                reasons, exclusions_triggered, policy_data, claim_data
            )

    reasons.append({
        "rule_id": "COV-002",
        "rule_name": "Peril Exclusion Check",
        "result": "pass",
        "message": f"Loss type '{loss_type}' is not excluded"
    })

    # Rule 3: Map loss type to coverage limit
    coverage_limit = _get_coverage_limit_for_loss_type(loss_type, coverage_limits)

    if coverage_limit is None or coverage_limit == 0:
        coverage_determination = "denied"
        reasons.append({
            "rule_id": "COV-003",
            "rule_name": "Coverage Limit Check",
            "result": "fail",
            "message": f"No coverage limit found for loss type '{loss_type}'"
        })
        return _build_response(
            coverage_determination, coverage_amount, deductible_amount,
            reasons, exclusions_triggered, policy_data, claim_data
        )

    reasons.append({
        "rule_id": "COV-003",
        "rule_name": "Coverage Limit Check",
        "result": "pass",
        "message": f"Coverage limit for '{loss_type}' is ${coverage_limit:,.2f}"
    })

    # Rule 4: Get applicable deductible
    deductible_amount = _get_deductible_for_loss_type(loss_type, deductibles)

    reasons.append({
        "rule_id": "COV-004",
        "rule_name": "Deductible Determination",
        "result": "pass",
        "message": f"Applicable deductible is ${deductible_amount:,.2f}"
    })

    # Rule 5: Calculate covered amount
    # Covered amount = min(claim_amount, coverage_limit) - deductible
    gross_covered = min(claim_amount, coverage_limit)
    net_covered = max(0, gross_covered - deductible_amount)

    if net_covered <= 0:
        coverage_determination = "denied"
        reasons.append({
            "rule_id": "COV-005",
            "rule_name": "Coverage Amount Calculation",
            "result": "fail",
            "message": f"Claim amount ${claim_amount:,.2f} does not exceed deductible ${deductible_amount:,.2f}"
        })
    elif net_covered < claim_amount:
        coverage_determination = "partial"
        coverage_amount = net_covered
        reasons.append({
            "rule_id": "COV-005",
            "rule_name": "Coverage Amount Calculation",
            "result": "partial",
            "message": f"Partial coverage: ${net_covered:,.2f} (claim ${claim_amount:,.2f} exceeds limit or subject to deductible)"
        })
    else:
        coverage_determination = "approved"
        coverage_amount = net_covered
        reasons.append({
            "rule_id": "COV-005",
            "rule_name": "Coverage Amount Calculation",
            "result": "pass",
            "message": f"Full coverage approved: ${net_covered:,.2f}"
        })

    return _build_response(
        coverage_determination, coverage_amount, deductible_amount,
        reasons, exclusions_triggered, policy_data, claim_data
    )


def _get_coverage_limit_for_loss_type(loss_type: str, coverage_limits: Dict[str, Any]) -> float:
    """Map loss type to appropriate coverage limit."""
    # Direct mapping
    if loss_type in coverage_limits:
        return float(coverage_limits[loss_type])

    # Fuzzy mapping for common loss types
    loss_type_mapping = {
        "collision": "collision",
        "comprehensive": "comprehensive",
        "theft": "comprehensive",
        "vandalism": "comprehensive",
        "fire": "comprehensive",
        "hail": "comprehensive",
        "water_damage": "dwelling",
        "wind": "dwelling",
        "liability": "liability",
        "bodily_injury": "bodily_injury",
        "property_damage": "property_damage",
        "medical": "medical_payments"
    }

    mapped_type = loss_type_mapping.get(loss_type)
    if mapped_type and mapped_type in coverage_limits:
        return float(coverage_limits[mapped_type])

    return 0


def _get_deductible_for_loss_type(loss_type: str, deductibles: Dict[str, Any]) -> float:
    """Get applicable deductible for loss type."""
    # Direct mapping
    if loss_type in deductibles:
        return float(deductibles[loss_type])

    # Check for collision/comprehensive deductibles
    if loss_type in ["collision"]:
        return float(deductibles.get("collision", 0))

    if loss_type in ["comprehensive", "theft", "vandalism", "fire", "hail"]:
        return float(deductibles.get("comprehensive", 0))

    # Check for all_perils deductible (common in homeowners)
    if "all_perils" in deductibles:
        return float(deductibles["all_perils"])

    # Default to 0 if no deductible found
    return 0


def _build_response(
    determination: str,
    coverage_amount: float,
    deductible_amount: float,
    reasons: List[Dict],
    exclusions: List[Dict],
    policy_data: Dict,
    claim_data: Dict
) -> Dict[str, Any]:
    """Build standardized coverage determination response."""
    return {
        "coverage_determination": determination,
        "coverage_amount": coverage_amount,
        "deductible_amount": deductible_amount,
        "claim_amount": claim_data.get("claim_amount", 0),
        "coverage_percentage": round((coverage_amount / max(claim_data.get("claim_amount", 1), 1)) * 100, 1),
        "reasons": reasons,
        "exclusions_triggered": exclusions,
        "policy_limits_applied": {
            "coverage_limit": _get_coverage_limit_for_loss_type(
                claim_data.get("loss_type", ""),
                policy_data.get("coverage_limits", {})
            ),
            "deductible": deductible_amount
        },
        "recommendation": _get_recommendation(determination, coverage_amount, claim_data.get("claim_amount", 0))
    }


def _get_recommendation(determination: str, coverage_amount: float, claim_amount: float) -> str:
    """Generate recommendation based on coverage determination."""
    if determination == "approved":
        return f"Approve claim for ${coverage_amount:,.2f}"
    elif determination == "partial":
        shortfall = claim_amount - coverage_amount
        return f"Approve partial payment of ${coverage_amount:,.2f}. Claimant responsible for ${shortfall:,.2f} shortfall."
    elif determination == "denied":
        return "Deny claim - does not meet coverage criteria"
    else:
        return "Additional review required"
