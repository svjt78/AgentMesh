"""
Similarity Tool - Find similar historical claims.

Demonstrates: Vector similarity search pattern (mocked with rule-based matching).
"""

from typing import Dict, Any, List
import hashlib


def execute_similarity(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Find similar historical claims based on claim characteristics.

    In production, this would use vector embeddings and semantic search.
    For this prototype, we use rule-based matching on key attributes.

    Args:
        parameters: Dict with claim attributes to match

    Returns:
        List of similar claims with similarity scores
    """
    # Extract search criteria
    loss_type = parameters.get("loss_type", "").lower()
    claim_amount = parameters.get("claim_amount", 0)
    policy_type = parameters.get("policy_type", "").lower()
    location = parameters.get("location", "").lower()

    # Mock historical claims database
    # In production, this would query vector database with embeddings
    MOCK_HISTORICAL_CLAIMS = [
        {
            "claim_id": "CLM-2023-0789",
            "loss_type": "collision",
            "claim_amount": 8500,
            "policy_type": "auto",
            "location": "california",
            "resolution": "approved",
            "payout_amount": 7800,
            "processing_days": 12,
            "fraud_detected": False,
            "settlement_notes": "Rear-end collision, clear liability, minor injuries"
        },
        {
            "claim_id": "CLM-2023-0654",
            "loss_type": "collision",
            "claim_amount": 12000,
            "policy_type": "auto",
            "location": "texas",
            "resolution": "approved",
            "payout_amount": 11200,
            "processing_days": 18,
            "fraud_detected": False,
            "settlement_notes": "Multi-vehicle accident, shared liability (80/20)"
        },
        {
            "claim_id": "CLM-2023-0521",
            "loss_type": "theft",
            "claim_amount": 25000,
            "policy_type": "auto",
            "location": "california",
            "resolution": "approved",
            "payout_amount": 22000,
            "processing_days": 45,
            "fraud_detected": False,
            "settlement_notes": "Vehicle stolen and recovered damaged, depreciation applied"
        },
        {
            "claim_id": "CLM-2023-0433",
            "loss_type": "collision",
            "claim_amount": 45000,
            "policy_type": "auto",
            "location": "new york",
            "resolution": "partial",
            "payout_amount": 28000,
            "processing_days": 67,
            "fraud_detected": True,
            "settlement_notes": "Fraud investigation revealed exaggerated damages, settled for actual repair costs"
        },
        {
            "claim_id": "CLM-2023-0312",
            "loss_type": "fire",
            "claim_amount": 180000,
            "policy_type": "homeowners",
            "location": "california",
            "resolution": "approved",
            "payout_amount": 175000,
            "processing_days": 90,
            "fraud_detected": False,
            "settlement_notes": "Kitchen fire, structure damage, smoke damage throughout home"
        },
        {
            "claim_id": "CLM-2023-0287",
            "loss_type": "water damage",
            "claim_amount": 35000,
            "policy_type": "homeowners",
            "location": "florida",
            "resolution": "approved",
            "payout_amount": 32000,
            "processing_days": 30,
            "fraud_detected": False,
            "settlement_notes": "Burst pipe, flooring and drywall replacement"
        },
        {
            "claim_id": "CLM-2023-0156",
            "loss_type": "collision",
            "claim_amount": 9200,
            "policy_type": "auto",
            "location": "california",
            "resolution": "approved",
            "payout_amount": 8700,
            "processing_days": 14,
            "fraud_detected": False,
            "settlement_notes": "Single-vehicle accident, hit median barrier, airbags deployed"
        },
        {
            "claim_id": "CLM-2023-0098",
            "loss_type": "hail damage",
            "claim_amount": 6500,
            "policy_type": "auto",
            "location": "texas",
            "resolution": "approved",
            "payout_amount": 6200,
            "processing_days": 10,
            "fraud_detected": False,
            "settlement_notes": "Hail storm damage, roof and hood dents, windshield replacement"
        }
    ]

    # Calculate similarity scores for each historical claim
    similar_claims = []

    for historical_claim in MOCK_HISTORICAL_CLAIMS:
        similarity_score = 0
        matching_factors = []

        # Factor 1: Loss type match (40 points)
        if historical_claim["loss_type"] == loss_type:
            similarity_score += 40
            matching_factors.append("loss_type")

        # Factor 2: Policy type match (20 points)
        if historical_claim["policy_type"] == policy_type:
            similarity_score += 20
            matching_factors.append("policy_type")

        # Factor 3: Location match (15 points)
        if historical_claim["location"] == location:
            similarity_score += 15
            matching_factors.append("location")

        # Factor 4: Claim amount similarity (25 points max)
        # Score based on how close amounts are
        if claim_amount > 0:
            amount_diff_pct = abs(historical_claim["claim_amount"] - claim_amount) / max(claim_amount, 1)
            if amount_diff_pct <= 0.2:  # Within 20%
                similarity_score += 25
                matching_factors.append("claim_amount_very_close")
            elif amount_diff_pct <= 0.5:  # Within 50%
                similarity_score += 15
                matching_factors.append("claim_amount_close")
            elif amount_diff_pct <= 1.0:  # Within 100%
                similarity_score += 5
                matching_factors.append("claim_amount_similar")

        # Only include claims with meaningful similarity (score > 20)
        if similarity_score >= 20:
            similar_claims.append({
                "claim_id": historical_claim["claim_id"],
                "similarity_score": similarity_score,
                "matching_factors": matching_factors,
                "claim_details": {
                    "loss_type": historical_claim["loss_type"],
                    "claim_amount": historical_claim["claim_amount"],
                    "policy_type": historical_claim["policy_type"],
                    "location": historical_claim["location"],
                    "resolution": historical_claim["resolution"],
                    "payout_amount": historical_claim["payout_amount"],
                    "processing_days": historical_claim["processing_days"],
                    "fraud_detected": historical_claim["fraud_detected"],
                    "settlement_notes": historical_claim["settlement_notes"]
                }
            })

    # Sort by similarity score (descending)
    similar_claims.sort(key=lambda x: x["similarity_score"], reverse=True)

    # Limit to top 5 most similar
    top_similar_claims = similar_claims[:5]

    # Calculate aggregate statistics
    if top_similar_claims:
        avg_processing_days = sum(c["claim_details"]["processing_days"] for c in top_similar_claims) / len(top_similar_claims)
        fraud_rate = sum(1 for c in top_similar_claims if c["claim_details"]["fraud_detected"]) / len(top_similar_claims)
        avg_payout_ratio = sum(
            c["claim_details"]["payout_amount"] / max(c["claim_details"]["claim_amount"], 1)
            for c in top_similar_claims
        ) / len(top_similar_claims)
    else:
        avg_processing_days = 0
        fraud_rate = 0
        avg_payout_ratio = 0

    return {
        "similar_claims": top_similar_claims,
        "total_matches": len(top_similar_claims),
        "aggregate_insights": {
            "average_processing_days": round(avg_processing_days, 1),
            "fraud_detection_rate": round(fraud_rate * 100, 1),
            "average_payout_ratio": round(avg_payout_ratio * 100, 1),
            "most_common_resolution": _get_most_common_resolution(top_similar_claims)
        },
        "search_criteria": {
            "loss_type": loss_type,
            "claim_amount": claim_amount,
            "policy_type": policy_type,
            "location": location
        }
    }


def _get_most_common_resolution(claims: List[Dict[str, Any]]) -> str:
    """Helper to find most common resolution in similar claims."""
    if not claims:
        return "unknown"

    resolutions = [c["claim_details"]["resolution"] for c in claims]
    return max(set(resolutions), key=resolutions.count)
