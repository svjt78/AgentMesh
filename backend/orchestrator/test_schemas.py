#!/usr/bin/env python3
"""
Test script for Phase 5: Agent Output Schema Validation

Tests all agent output schemas with sample data to verify:
- Schema validation works correctly
- Required fields are enforced
- Type constraints are validated
- Error messages are clear and actionable
"""

import sys
from datetime import datetime
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.schemas import (
    validate_agent_output,
    get_schema_for_agent,
    list_available_schemas,
    SchemaValidationError,
    IntakeAgentOutput,
    CoverageAgentOutput,
    FraudAgentOutput,
    SeverityAgentOutput,
    RecommendationAgentOutput,
    ExplainabilityAgentOutput
)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)


def test_intake_agent():
    """Test IntakeAgentOutput schema."""
    print_section("Testing Intake Agent Schema")

    # Valid output
    valid_data = {
        "agent_id": "intake_agent",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "normalized_claim": {
            "claim_id": "CLM-001",
            "policy_id": "POL-001",
            "claim_amount": 15000.0
        },
        "data_quality_score": 0.95,
        "validation_passed": True,
        "data_quality_issues": [
            {
                "field": "incident_date",
                "issue_type": "inconsistent",
                "severity": "low",
                "message": "Date format standardized"
            }
        ],
        "normalization_changes": ["standardized_date_format", "uppercase_policy_id"]
    }

    try:
        validated = validate_agent_output("intake_agent", valid_data)
        print(f"✓ Valid intake output validated successfully")
        print(f"  - Agent ID: {validated.agent_id}")
        print(f"  - Quality Score: {validated.data_quality_score}")
        print(f"  - Validation Passed: {validated.validation_passed}")
        print(f"  - Issues: {len(validated.data_quality_issues)}")
    except SchemaValidationError as e:
        print(f"✗ FAILED: {e}")
        return False

    # Invalid output - score out of range
    invalid_data = valid_data.copy()
    invalid_data["data_quality_score"] = 1.5  # Invalid: > 1.0

    try:
        validated = validate_agent_output("intake_agent", invalid_data)
        print(f"✗ FAILED: Should have rejected score > 1.0")
        return False
    except SchemaValidationError as e:
        print(f"✓ Correctly rejected invalid score: {e}")

    return True


def test_coverage_agent():
    """Test CoverageAgentOutput schema."""
    print_section("Testing Coverage Agent Schema")

    valid_data = {
        "agent_id": "coverage_agent",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "coverage_determination": "approved",
        "coverage_amount": 14500.0,
        "deductible_amount": 500.0,
        "coverage_percentage": 95.0,
        "exclusions_triggered": [],
        "coverage_limits_applied": {
            "bodily_injury": 50000.0,
            "property_damage": 25000.0
        },
        "reasoning": "Full coverage approved. Claim amount within policy limits."
    }

    try:
        validated = validate_agent_output("coverage_agent", valid_data)
        print(f"✓ Valid coverage output validated successfully")
        print(f"  - Determination: {validated.coverage_determination}")
        print(f"  - Coverage Amount: ${validated.coverage_amount:,.2f}")
        print(f"  - Coverage %: {validated.coverage_percentage}%")
    except SchemaValidationError as e:
        print(f"✗ FAILED: {e}")
        return False

    return True


def test_fraud_agent():
    """Test FraudAgentOutput schema."""
    print_section("Testing Fraud Agent Schema")

    valid_data = {
        "agent_id": "fraud_agent",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "fraud_score": 0.15,
        "risk_band": "low",
        "triggered_indicators": [
            {
                "indicator_id": "FRD-001",
                "indicator_name": "Recent Policy Purchase",
                "severity": "low",
                "confidence": 0.6,
                "description": "Policy purchased within 30 days of incident"
            }
        ],
        "siu_referral_required": False,
        "similar_claims_analysis": {
            "similar_claims_found": 0,
            "similarity_threshold": 0.8
        },
        "rationale": "Low fraud risk. Single low-severity indicator detected."
    }

    try:
        validated = validate_agent_output("fraud_agent", valid_data)
        print(f"✓ Valid fraud output validated successfully")
        print(f"  - Fraud Score: {validated.fraud_score}")
        print(f"  - Risk Band: {validated.risk_band}")
        print(f"  - SIU Referral: {validated.siu_referral_required}")
        print(f"  - Indicators: {len(validated.triggered_indicators)}")
    except SchemaValidationError as e:
        print(f"✗ FAILED: {e}")
        return False

    return True


def test_severity_agent():
    """Test SeverityAgentOutput schema."""
    print_section("Testing Severity Agent Schema")

    valid_data = {
        "agent_id": "severity_agent",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "complexity_level": "medium",
        "complexity_score": 0.5,
        "complexity_factors": [
            "Multiple parties involved",
            "Property damage assessment needed"
        ],
        "estimated_processing_days": 7,
        "required_expertise_level": "senior_adjuster",
        "special_handling_required": False,
        "assessment_rationale": "Standard collision claim with moderate complexity."
    }

    try:
        validated = validate_agent_output("severity_agent", valid_data)
        print(f"✓ Valid severity output validated successfully")
        print(f"  - Complexity Level: {validated.complexity_level}")
        print(f"  - Score: {validated.complexity_score}")
        print(f"  - Est. Days: {validated.estimated_processing_days}")
    except SchemaValidationError as e:
        print(f"✗ FAILED: {e}")
        return False

    return True


def test_recommendation_agent():
    """Test RecommendationAgentOutput schema."""
    print_section("Testing Recommendation Agent Schema")

    valid_data = {
        "agent_id": "recommendation_agent",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "recommended_action": "approve_and_process",
        "action_priority": "medium",
        "processing_track": "standard",
        "required_approvals": ["senior_adjuster"],
        "next_steps": [
            "Schedule vehicle inspection",
            "Contact claimant for additional documentation",
            "Process payment"
        ],
        "estimated_timeline_days": 10,
        "confidence": 0.85,
        "rationale": "Standard claim with no fraud indicators. Recommend approval with inspection."
    }

    try:
        validated = validate_agent_output("recommendation_agent", valid_data)
        print(f"✓ Valid recommendation output validated successfully")
        print(f"  - Action: {validated.recommended_action}")
        print(f"  - Priority: {validated.action_priority}")
        print(f"  - Track: {validated.processing_track}")
        print(f"  - Confidence: {validated.confidence}")
    except SchemaValidationError as e:
        print(f"✗ FAILED: {e}")
        return False

    return True


def test_explainability_agent():
    """Test ExplainabilityAgentOutput schema."""
    print_section("Testing Explainability Agent Schema")

    valid_data = {
        "agent_id": "explainability_agent",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "decision": {
            "outcome": "Approve claim with standard processing",
            "confidence": 0.85,
            "basis": "Comprehensive analysis shows valid claim with no fraud indicators"
        },
        "supporting_evidence": [
            {
                "source": "intake_agent",
                "evidence_type": "data_quality",
                "summary": "High quality data (95% score), all required fields present",
                "weight": 0.8
            },
            {
                "source": "fraud_agent",
                "evidence_type": "risk_assessment",
                "summary": "Low fraud risk (15% score), minimal indicators",
                "weight": 0.9
            }
        ],
        "assumptions": [
            "Claimant information is accurate",
            "Policy was active at time of incident"
        ],
        "limitations": [
            "Vehicle inspection not yet completed",
            "Third-party verification pending"
        ],
        "agent_chain": [
            "intake_agent",
            "coverage_agent",
            "fraud_agent",
            "severity_agent",
            "recommendation_agent"
        ],
        "explanation": "Complete triage analysis recommends approval. Claim shows high data quality, valid coverage, low fraud risk, and medium complexity."
    }

    try:
        validated = validate_agent_output("explainability_agent", valid_data)
        print(f"✓ Valid explainability output validated successfully")
        print(f"  - Decision: {validated.decision.outcome}")
        print(f"  - Confidence: {validated.decision.confidence}")
        print(f"  - Evidence Pieces: {len(validated.supporting_evidence)}")
        print(f"  - Agents in Chain: {len(validated.agent_chain)}")
    except SchemaValidationError as e:
        print(f"✗ FAILED: {e}")
        return False

    return True


def test_missing_required_fields():
    """Test that missing required fields are caught."""
    print_section("Testing Missing Required Fields")

    incomplete_data = {
        "agent_id": "fraud_agent",
        "fraud_score": 0.5
        # Missing: risk_band, siu_referral_required, rationale
    }

    try:
        validated = validate_agent_output("fraud_agent", incomplete_data)
        print(f"✗ FAILED: Should have rejected incomplete data")
        return False
    except SchemaValidationError as e:
        print(f"✓ Correctly rejected incomplete data")
        print(f"  Error details: {e}")
        return True


def test_list_schemas():
    """Test schema listing utility."""
    print_section("Testing Schema Discovery")

    schemas = list_available_schemas()
    print(f"Available schemas: {len(schemas)}")
    for agent_id, schema_name in schemas.items():
        print(f"  - {agent_id}: {schema_name}")

        # Get schema class
        schema_class = get_schema_for_agent(agent_id)
        if schema_class:
            print(f"    ✓ Schema class retrieved: {schema_class.__name__}")
        else:
            print(f"    ✗ Failed to retrieve schema class")

    return len(schemas) == 7  # Should have 7 agent schemas


def main():
    """Run all schema validation tests."""
    print_section("Phase 5: Agent Output Schema Validation Tests")
    print("Testing all agent output schemas with sample data...\n")

    tests = [
        ("Intake Agent", test_intake_agent),
        ("Coverage Agent", test_coverage_agent),
        ("Fraud Agent", test_fraud_agent),
        ("Severity Agent", test_severity_agent),
        ("Recommendation Agent", test_recommendation_agent),
        ("Explainability Agent", test_explainability_agent),
        ("Missing Fields", test_missing_required_fields),
        ("Schema Discovery", test_list_schemas)
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print_section("Test Summary")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All schema validation tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
