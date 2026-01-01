"""
Policy Snapshot Tool - Retrieve policy coverage information.

Demonstrates: External data retrieval pattern with mock data.
"""

from typing import Dict, Any


def execute_policy_snapshot(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve policy coverage information for a given policy ID.

    Args:
        parameters: Dict with 'policy_id' key

    Returns:
        Mock policy coverage data

    Raises:
        ValueError: If policy_id is missing
    """
    # Validate required parameters
    if "policy_id" not in parameters:
        raise ValueError("Missing required parameter: policy_id")

    policy_id = parameters["policy_id"]

    # Mock policy database
    # In production, this would query actual policy management system
    MOCK_POLICIES = {
        "POL-001": {
            "policy_id": "POL-001",
            "policyholder": "John Doe",
            "policy_type": "Auto Insurance",
            "coverage_limits": {
                "bodily_injury": 100000,
                "property_damage": 50000,
                "collision": 25000,
                "comprehensive": 25000
            },
            "deductibles": {
                "collision": 500,
                "comprehensive": 250
            },
            "status": "active",
            "effective_date": "2023-01-01",
            "expiration_date": "2024-01-01",
            "premium": 1200,
            "riders": ["rental_reimbursement", "roadside_assistance"],
            "excluded_perils": ["racing", "commercial_use"]
        },
        "POL-002": {
            "policy_id": "POL-002",
            "policyholder": "Jane Smith",
            "policy_type": "Homeowners Insurance",
            "coverage_limits": {
                "dwelling": 300000,
                "personal_property": 150000,
                "liability": 300000,
                "medical_payments": 5000
            },
            "deductibles": {
                "all_perils": 1000,
                "wind_hail": 2500
            },
            "status": "active",
            "effective_date": "2023-06-01",
            "expiration_date": "2024-06-01",
            "premium": 1800,
            "riders": ["scheduled_jewelry", "water_backup"],
            "excluded_perils": ["flood", "earthquake"]
        },
        "POL-003": {
            "policy_id": "POL-003",
            "policyholder": "Bob Johnson",
            "policy_type": "Auto Insurance",
            "coverage_limits": {
                "bodily_injury": 250000,
                "property_damage": 100000,
                "collision": 50000,
                "comprehensive": 50000,
                "uninsured_motorist": 250000
            },
            "deductibles": {
                "collision": 1000,
                "comprehensive": 500
            },
            "status": "active",
            "effective_date": "2022-09-01",
            "expiration_date": "2024-09-01",
            "premium": 2400,
            "riders": ["rental_reimbursement", "roadside_assistance", "gap_coverage"],
            "excluded_perils": ["racing", "commercial_use", "ride_sharing"]
        }
    }

    # Return mock policy data or default if not found
    if policy_id in MOCK_POLICIES:
        return MOCK_POLICIES[policy_id]
    else:
        # Return default policy with warning
        return {
            "policy_id": policy_id,
            "policyholder": "Unknown",
            "policy_type": "Auto Insurance",
            "coverage_limits": {
                "bodily_injury": 50000,
                "property_damage": 25000,
                "collision": 10000,
                "comprehensive": 10000
            },
            "deductibles": {
                "collision": 500,
                "comprehensive": 250
            },
            "status": "active",
            "effective_date": "2023-01-01",
            "expiration_date": "2024-01-01",
            "premium": 800,
            "riders": [],
            "excluded_perils": ["racing", "commercial_use"],
            "_warning": "Policy not found in database, returning default coverage"
        }
