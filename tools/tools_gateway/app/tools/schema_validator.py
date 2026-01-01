"""
Schema Validator Tool - Validate claim data against schema.

Demonstrates: Data validation pattern with detailed error reporting.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


def execute_schema_validator(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate claim data against expected schema.

    Args:
        parameters: Dict with 'claim_data' to validate

    Returns:
        Validation result with errors and warnings
    """
    # Extract claim data
    claim_data = parameters.get("claim_data", {})

    if not claim_data:
        raise ValueError("Missing required parameter: claim_data")

    validation_errors = []
    validation_warnings = []

    # Required fields validation
    required_fields = [
        "claim_id",
        "policy_id",
        "claim_date",
        "loss_type",
        "claim_amount"
    ]

    for field in required_fields:
        if field not in claim_data or claim_data[field] is None:
            validation_errors.append({
                "field": field,
                "error_type": "required_field_missing",
                "message": f"Required field '{field}' is missing or null",
                "severity": "error"
            })
        elif isinstance(claim_data[field], str) and claim_data[field].strip() == "":
            validation_errors.append({
                "field": field,
                "error_type": "required_field_empty",
                "message": f"Required field '{field}' is empty",
                "severity": "error"
            })

    # Field type validation
    if "claim_amount" in claim_data:
        if not isinstance(claim_data["claim_amount"], (int, float)):
            validation_errors.append({
                "field": "claim_amount",
                "error_type": "invalid_type",
                "message": f"Field 'claim_amount' must be numeric, got {type(claim_data['claim_amount']).__name__}",
                "severity": "error"
            })
        elif claim_data["claim_amount"] <= 0:
            validation_errors.append({
                "field": "claim_amount",
                "error_type": "invalid_value",
                "message": "Field 'claim_amount' must be greater than 0",
                "severity": "error"
            })
        elif claim_data["claim_amount"] > 1000000:
            validation_warnings.append({
                "field": "claim_amount",
                "warning_type": "unusual_value",
                "message": f"Field 'claim_amount' is unusually high: ${claim_data['claim_amount']:,.2f}",
                "severity": "warning"
            })

    # Date format validation
    date_fields = ["claim_date", "incident_date", "policy_effective_date"]
    for field in date_fields:
        if field in claim_data and claim_data[field]:
            if not _is_valid_date(claim_data[field]):
                validation_errors.append({
                    "field": field,
                    "error_type": "invalid_format",
                    "message": f"Field '{field}' has invalid date format. Expected ISO 8601 format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)",
                    "severity": "error"
                })

    # Loss type validation
    valid_loss_types = [
        "collision", "comprehensive", "liability", "medical", "uninsured_motorist",
        "fire", "theft", "vandalism", "water_damage", "wind", "hail", "other"
    ]

    if "loss_type" in claim_data and claim_data["loss_type"]:
        if claim_data["loss_type"].lower() not in valid_loss_types:
            validation_warnings.append({
                "field": "loss_type",
                "warning_type": "unexpected_value",
                "message": f"Field 'loss_type' has unexpected value: '{claim_data['loss_type']}'. Valid values: {', '.join(valid_loss_types)}",
                "severity": "warning"
            })

    # Email validation (if provided)
    if "claimant_email" in claim_data and claim_data["claimant_email"]:
        if not _is_valid_email(claim_data["claimant_email"]):
            validation_errors.append({
                "field": "claimant_email",
                "error_type": "invalid_format",
                "message": f"Field 'claimant_email' has invalid email format: '{claim_data['claimant_email']}'",
                "severity": "error"
            })

    # Phone validation (if provided)
    if "claimant_phone" in claim_data and claim_data["claimant_phone"]:
        if not _is_valid_phone(claim_data["claimant_phone"]):
            validation_warnings.append({
                "field": "claimant_phone",
                "warning_type": "invalid_format",
                "message": f"Field 'claimant_phone' may have invalid format: '{claim_data['claimant_phone']}'",
                "severity": "warning"
            })

    # Policy ID format validation
    if "policy_id" in claim_data and claim_data["policy_id"]:
        if not isinstance(claim_data["policy_id"], str):
            validation_errors.append({
                "field": "policy_id",
                "error_type": "invalid_type",
                "message": f"Field 'policy_id' must be string, got {type(claim_data['policy_id']).__name__}",
                "severity": "error"
            })

    # Cross-field validation
    if "claim_date" in claim_data and "incident_date" in claim_data:
        if _is_valid_date(claim_data["claim_date"]) and _is_valid_date(claim_data["incident_date"]):
            claim_dt = _parse_date(claim_data["claim_date"])
            incident_dt = _parse_date(claim_data["incident_date"])

            if claim_dt and incident_dt:
                if claim_dt < incident_dt:
                    validation_errors.append({
                        "field": "claim_date",
                        "error_type": "logical_inconsistency",
                        "message": "Claim date cannot be before incident date",
                        "severity": "error"
                    })

                days_diff = (claim_dt - incident_dt).days
                if days_diff > 365:
                    validation_warnings.append({
                        "field": "claim_date",
                        "warning_type": "unusual_value",
                        "message": f"Claim filed {days_diff} days after incident (unusually long delay)",
                        "severity": "warning"
                    })

    # Determine overall validation status
    is_valid = len(validation_errors) == 0

    return {
        "is_valid": is_valid,
        "validation_errors": validation_errors,
        "validation_warnings": validation_warnings,
        "error_count": len(validation_errors),
        "warning_count": len(validation_warnings),
        "fields_validated": len(claim_data),
        "validation_summary": _build_validation_summary(is_valid, validation_errors, validation_warnings)
    }


def _is_valid_date(date_str: str) -> bool:
    """Check if string is a valid ISO 8601 date."""
    if not isinstance(date_str, str):
        return False

    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%fZ"
    ]

    for fmt in formats:
        try:
            datetime.strptime(date_str.replace('+00:00', 'Z').replace('Z', ''), fmt.replace('Z', ''))
            return True
        except ValueError:
            continue

    return False


def _parse_date(date_str: str) -> Optional[datetime]:
    """Parse ISO 8601 date string."""
    formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%fZ"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str.replace('+00:00', 'Z').replace('Z', ''), fmt.replace('Z', ''))
        except ValueError:
            continue

    return None


def _is_valid_email(email: str) -> bool:
    """Simple email validation."""
    if not isinstance(email, str):
        return False

    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def _is_valid_phone(phone: str) -> bool:
    """Simple phone validation (just check if it has digits)."""
    if not isinstance(phone, str):
        return False

    import re
    # Check if phone has at least 10 digits
    digits = re.sub(r'\D', '', phone)
    return len(digits) >= 10


def _build_validation_summary(is_valid: bool, errors: List[Dict], warnings: List[Dict]) -> str:
    """Build human-readable validation summary."""
    if is_valid and len(warnings) == 0:
        return "All validations passed successfully"
    elif is_valid and len(warnings) > 0:
        return f"Validation passed with {len(warnings)} warning(s)"
    else:
        return f"Validation failed with {len(errors)} error(s) and {len(warnings)} warning(s)"
