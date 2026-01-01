"""
Decision Rules Tool - Recommend action based on analysis results.

Demonstrates: Decision tree pattern for claims processing.
"""

from typing import Dict, Any, List


def execute_decision_rules(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recommend next action for claim based on analysis results.

    Combines inputs from coverage, fraud, severity assessments to determine
    the appropriate processing path.

    Args:
        parameters: Dict with coverage_result, fraud_result, severity_result

    Returns:
        Action recommendation with reasoning
    """
    # Extract analysis results
    coverage_result = parameters.get("coverage_result", {})
    fraud_result = parameters.get("fraud_result", {})
    severity_result = parameters.get("severity_result", {})

    # Extract key metrics
    coverage_determination = coverage_result.get("coverage_determination", "unknown")
    coverage_amount = coverage_result.get("coverage_amount", 0)

    fraud_risk_level = fraud_result.get("risk_level", "unknown")
    fraud_risk_score = fraud_result.get("risk_score", 0)
    requires_siu = fraud_result.get("requires_siu_review", False)

    severity_level = severity_result.get("complexity_level", "unknown")
    estimated_processing_days = severity_result.get("estimated_processing_days", 0)

    # Decision logic
    recommended_action = "unknown"
    action_priority = "medium"
    processing_track = "standard"
    required_approvals = []
    next_steps = []
    reasoning_chain = []

    # Decision Tree Logic

    # Branch 1: Coverage denied
    if coverage_determination == "denied":
        recommended_action = "deny_claim"
        action_priority = "high"
        processing_track = "expedited"
        next_steps = [
            "Send denial letter to claimant",
            "Provide detailed explanation of coverage exclusion",
            "Inform claimant of appeal rights",
            "Close claim file"
        ]
        reasoning_chain.append({
            "decision_point": "Coverage Determination",
            "outcome": "denied",
            "reasoning": "Claim does not meet policy coverage requirements"
        })

        return _build_response(
            recommended_action, action_priority, processing_track,
            required_approvals, next_steps, reasoning_chain,
            coverage_result, fraud_result, severity_result
        )

    # Branch 2: High fraud risk
    if fraud_risk_level == "high" or requires_siu:
        recommended_action = "escalate_to_siu"
        action_priority = "high"
        processing_track = "investigation"
        required_approvals = ["SIU Manager", "Claims Director"]
        next_steps = [
            "Assign to Special Investigation Unit (SIU)",
            "Conduct comprehensive fraud investigation",
            "Request additional documentation from claimant",
            "Verify incident with independent sources",
            "Interview claimant and witnesses",
            "Hold payment pending investigation completion"
        ]
        reasoning_chain.append({
            "decision_point": "Fraud Risk Assessment",
            "outcome": f"high_risk (score: {fraud_risk_score})",
            "reasoning": "Multiple fraud indicators detected, requires SIU review"
        })

        return _build_response(
            recommended_action, action_priority, processing_track,
            required_approvals, next_steps, reasoning_chain,
            coverage_result, fraud_result, severity_result
        )

    # Branch 3: High severity/complexity
    if severity_level in ["high", "critical"]:
        recommended_action = "assign_senior_adjuster"
        action_priority = "high"
        processing_track = "complex"
        required_approvals = ["Senior Claims Manager"]
        next_steps = [
            "Assign to senior claims adjuster",
            "Conduct detailed damage assessment",
            "Obtain independent appraisal",
            "Review policy terms in detail",
            "Coordinate with legal team if needed",
            f"Target resolution within {estimated_processing_days} days"
        ]
        reasoning_chain.append({
            "decision_point": "Severity Assessment",
            "outcome": f"{severity_level} complexity",
            "reasoning": "High complexity claim requires senior adjuster expertise"
        })

        # Medium fraud risk - add fraud monitoring
        if fraud_risk_level == "medium":
            next_steps.insert(2, "Monitor for additional fraud indicators during processing")
            reasoning_chain.append({
                "decision_point": "Fraud Risk Assessment",
                "outcome": f"medium_risk (score: {fraud_risk_score})",
                "reasoning": "Enhanced monitoring recommended during processing"
            })

    # Branch 4: High value claim (>$50,000)
    elif coverage_amount > 50000:
        recommended_action = "require_manager_approval"
        action_priority = "high"
        processing_track = "standard_with_approval"
        required_approvals = ["Claims Manager"]
        next_steps = [
            "Assign to experienced claims adjuster",
            "Verify coverage limits and policy terms",
            "Obtain independent damage assessment",
            "Prepare approval request for Claims Manager",
            "Process payment upon manager approval",
            f"Target resolution within {estimated_processing_days} days"
        ]
        reasoning_chain.append({
            "decision_point": "Coverage Amount",
            "outcome": f"high_value (${coverage_amount:,.2f})",
            "reasoning": "Claims over $50,000 require manager approval"
        })

        # Medium fraud risk - add verification
        if fraud_risk_level == "medium":
            next_steps.insert(3, "Conduct enhanced verification due to fraud indicators")
            reasoning_chain.append({
                "decision_point": "Fraud Risk Assessment",
                "outcome": f"medium_risk (score: {fraud_risk_score})",
                "reasoning": "Enhanced verification recommended"
            })

    # Branch 5: Medium complexity with medium fraud risk
    elif severity_level == "medium" and fraud_risk_level == "medium":
        recommended_action = "standard_processing_with_review"
        action_priority = "medium"
        processing_track = "standard_enhanced"
        required_approvals = []
        next_steps = [
            "Assign to standard claims adjuster",
            "Conduct standard damage assessment with extra diligence",
            "Verify documentation thoroughly",
            "Review for fraud indicators during processing",
            "Process payment if all verifications pass",
            f"Target resolution within {estimated_processing_days} days"
        ]
        reasoning_chain.append({
            "decision_point": "Combined Assessment",
            "outcome": "medium_complexity_medium_fraud",
            "reasoning": "Standard processing with enhanced review protocols"
        })

    # Branch 6: Partial coverage
    elif coverage_determination == "partial":
        recommended_action = "approve_with_explanation"
        action_priority = "medium"
        processing_track = "standard"
        required_approvals = []
        shortfall = parameters.get("coverage_result", {}).get("claim_amount", 0) - coverage_amount
        next_steps = [
            f"Approve payment of ${coverage_amount:,.2f}",
            f"Prepare explanation letter detailing ${shortfall:,.2f} shortfall",
            "Explain policy limits and deductible application",
            "Process approved payment",
            "Send settlement letter to claimant"
        ]
        reasoning_chain.append({
            "decision_point": "Coverage Determination",
            "outcome": "partial_coverage",
            "reasoning": f"Partial coverage due to policy limits or deductible"
        })

    # Branch 7: Standard approval (low risk, standard complexity, approved coverage)
    else:
        recommended_action = "approve_and_pay"
        action_priority = "medium"
        processing_track = "fast_track"
        required_approvals = []
        next_steps = [
            "Conduct standard verification",
            "Validate claim documentation",
            f"Approve payment of ${coverage_amount:,.2f}",
            "Process payment within 5 business days",
            "Send confirmation to claimant"
        ]
        reasoning_chain.append({
            "decision_point": "Combined Assessment",
            "outcome": "standard_approval",
            "reasoning": "Claim meets all standard approval criteria"
        })

    return _build_response(
        recommended_action, action_priority, processing_track,
        required_approvals, next_steps, reasoning_chain,
        coverage_result, fraud_result, severity_result
    )


def _build_response(
    action: str,
    priority: str,
    track: str,
    approvals: List[str],
    steps: List[str],
    reasoning: List[Dict],
    coverage_result: Dict,
    fraud_result: Dict,
    severity_result: Dict
) -> Dict[str, Any]:
    """Build standardized decision response."""
    return {
        "recommended_action": action,
        "action_priority": priority,
        "processing_track": track,
        "required_approvals": approvals,
        "next_steps": steps,
        "reasoning_chain": reasoning,
        "estimated_timeline": _estimate_timeline(track, severity_result.get("estimated_processing_days", 14)),
        "input_summary": {
            "coverage_determination": coverage_result.get("coverage_determination", "unknown"),
            "coverage_amount": coverage_result.get("coverage_amount", 0),
            "fraud_risk_level": fraud_result.get("risk_level", "unknown"),
            "fraud_risk_score": fraud_result.get("risk_score", 0),
            "severity_level": severity_result.get("complexity_level", "unknown")
        },
        "confidence_level": _calculate_confidence(coverage_result, fraud_result, severity_result)
    }


def _estimate_timeline(processing_track: str, base_days: int) -> Dict[str, Any]:
    """Estimate processing timeline based on track."""
    track_multipliers = {
        "fast_track": 0.5,
        "standard": 1.0,
        "standard_enhanced": 1.2,
        "standard_with_approval": 1.3,
        "complex": 1.5,
        "investigation": 2.0,
        "expedited": 0.3
    }

    multiplier = track_multipliers.get(processing_track, 1.0)
    estimated_days = int(base_days * multiplier)

    return {
        "processing_track": processing_track,
        "estimated_days": estimated_days,
        "estimated_business_days": estimated_days,
        "timeline_confidence": "high" if processing_track in ["fast_track", "standard", "expedited"] else "medium"
    }


def _calculate_confidence(coverage: Dict, fraud: Dict, severity: Dict) -> str:
    """Calculate confidence level in recommendation."""
    # High confidence if all inputs are definitive
    if (coverage.get("coverage_determination") in ["approved", "denied"] and
        fraud.get("risk_level") in ["none", "low", "high"] and
        severity.get("complexity_level") in ["low", "high"]):
        return "high"

    # Medium confidence if some ambiguity
    if (coverage.get("coverage_determination") == "partial" or
        fraud.get("risk_level") == "medium" or
        severity.get("complexity_level") == "medium"):
        return "medium"

    # Low confidence if missing data
    return "low"
