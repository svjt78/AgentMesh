"""
Fraud Rules Tool - Detect fraud indicators using rule-based logic.

Demonstrates: Rule engine pattern with configurable thresholds.
"""

from typing import Dict, Any, List


def execute_fraud_rules(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze claim for fraud indicators using rule-based detection.

    Args:
        parameters: Dict with claim data

    Returns:
        Fraud analysis with detected indicators and risk score
    """
    # Extract claim data
    claim_amount = parameters.get("claim_amount", 0)
    claim_date = parameters.get("claim_date", "")
    policy_effective_date = parameters.get("policy_effective_date", "")
    claimant_history = parameters.get("claimant_history", {})
    incident_description = parameters.get("incident_description", "").lower()
    injury_severity = parameters.get("injury_severity", "").lower()

    fraud_indicators = []
    risk_score = 0

    # Rule 1: High claim amount (>$50,000)
    if claim_amount > 50000:
        fraud_indicators.append({
            "rule_id": "FR-001",
            "rule_name": "High Claim Amount",
            "description": f"Claim amount ${claim_amount:,.2f} exceeds threshold of $50,000",
            "severity": "medium",
            "risk_points": 15
        })
        risk_score += 15

    # Rule 2: Very high claim amount (>$100,000)
    if claim_amount > 100000:
        fraud_indicators.append({
            "rule_id": "FR-002",
            "rule_name": "Very High Claim Amount",
            "description": f"Claim amount ${claim_amount:,.2f} exceeds threshold of $100,000",
            "severity": "high",
            "risk_points": 25
        })
        risk_score += 25

    # Rule 3: New policy claim (claim within 30 days of policy effective date)
    if claim_date and policy_effective_date:
        from datetime import datetime
        try:
            claim_dt = datetime.fromisoformat(claim_date.replace('Z', '+00:00'))
            policy_dt = datetime.fromisoformat(policy_effective_date.replace('Z', '+00:00'))
            days_diff = (claim_dt - policy_dt).days

            if days_diff <= 30:
                fraud_indicators.append({
                    "rule_id": "FR-003",
                    "rule_name": "New Policy Claim",
                    "description": f"Claim filed {days_diff} days after policy effective date",
                    "severity": "high",
                    "risk_points": 30
                })
                risk_score += 30
        except:
            pass

    # Rule 4: Multiple claims history
    prior_claims_count = claimant_history.get("prior_claims_count", 0)
    if prior_claims_count >= 3:
        fraud_indicators.append({
            "rule_id": "FR-004",
            "rule_name": "Multiple Claims History",
            "description": f"Claimant has {prior_claims_count} prior claims",
            "severity": "medium",
            "risk_points": 20
        })
        risk_score += 20

    # Rule 5: Suspicious keywords in description
    suspicious_keywords = ["total loss", "totaled", "stolen", "fire", "theft", "vandalism"]
    detected_keywords = [kw for kw in suspicious_keywords if kw in incident_description]

    if len(detected_keywords) >= 2:
        fraud_indicators.append({
            "rule_id": "FR-005",
            "rule_name": "Suspicious Description Keywords",
            "description": f"Description contains multiple high-risk keywords: {', '.join(detected_keywords)}",
            "severity": "medium",
            "risk_points": 15
        })
        risk_score += 15

    # Rule 6: Inconsistent injury severity and claim amount
    if injury_severity == "minor" and claim_amount > 25000:
        fraud_indicators.append({
            "rule_id": "FR-006",
            "rule_name": "Inconsistent Injury Severity",
            "description": f"Minor injury with high claim amount ${claim_amount:,.2f}",
            "severity": "medium",
            "risk_points": 20
        })
        risk_score += 20

    # Rule 7: Weekend or holiday incident (higher fraud correlation)
    if parameters.get("incident_day_of_week") in ["Saturday", "Sunday"]:
        fraud_indicators.append({
            "rule_id": "FR-007",
            "rule_name": "Weekend Incident",
            "description": "Incident occurred on weekend (statistically higher fraud rate)",
            "severity": "low",
            "risk_points": 5
        })
        risk_score += 5

    # Determine overall risk level
    if risk_score >= 50:
        risk_level = "high"
    elif risk_score >= 25:
        risk_level = "medium"
    elif risk_score > 0:
        risk_level = "low"
    else:
        risk_level = "none"

    # Build recommendations
    recommendations = []
    if risk_level == "high":
        recommendations.extend([
            "Initiate special investigation unit (SIU) review",
            "Request additional documentation and evidence",
            "Conduct claimant interview",
            "Verify incident with independent sources"
        ])
    elif risk_level == "medium":
        recommendations.extend([
            "Enhanced claims adjuster review required",
            "Request supporting documentation",
            "Verify claimant history"
        ])
    elif risk_level == "low":
        recommendations.append("Standard processing with routine verification")
    else:
        recommendations.append("No fraud indicators detected - proceed with standard processing")

    return {
        "fraud_indicators_detected": fraud_indicators,
        "fraud_indicators_count": len(fraud_indicators),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "recommendations": recommendations,
        "requires_siu_review": risk_level == "high",
        "analysis_metadata": {
            "rules_evaluated": 7,
            "rules_triggered": len(fraud_indicators),
            "max_possible_score": 135
        }
    }
