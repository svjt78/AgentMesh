# Sample Claim Data

This directory contains comprehensive sample claim data for testing and demonstrating the AgentMesh platform.

## Sample Files

### 1. sample_claim_clean.json
**Scenario**: Straightforward legitimate auto collision claim

**Characteristics**:
- Clear liability (other driver at fault)
- Complete documentation
- Police report filed
- Witnesses available
- No injuries
- Normal claim history
- No fraud indicators

**Expected Workflow Outcome**:
- Fast-track processing
- High approval confidence
- Low fraud risk
- Standard coverage determination

**Use Case**: Demonstrates normal workflow execution with all agents producing clean outputs.

---

### 2. sample_claim_fraud.json
**Scenario**: Auto theft claim with multiple fraud red flags

**Characteristics**:
- Recent policy with coverage increase
- Multiple similar prior claims (3 theft claims in 3 years)
- Vague incident details
- No documentation submitted
- Suspicious timing (claim filed hours after incident, late at night)
- High claim amount
- Missing evidence (no photos, no witnesses)
- Vehicle not recovered
- Temporary email address
- Financial stress indicators

**Expected Workflow Outcome**:
- SIU referral required
- Investigation processing track
- High fraud risk score
- Claim approval denied or held pending investigation

**Use Case**: Demonstrates fraud detection capabilities and governance enforcement.

---

### 3. sample_claim_edge_case.json
**Scenario**: Complex multi-vehicle accident with disputed liability and injuries

**Characteristics**:
- Three vehicles involved
- Disputed liability between parties
- Multiple injuries with ongoing treatment
- Adverse weather conditions
- Conflicting witness statements
- Structural damage (potential total loss)
- Multiple insurers involved
- Lost wages claim
- Subrogation likely
- Litigation risk

**Expected Workflow Outcome**:
- Complex processing track
- Extended investigation required
- Medium fraud risk
- Special handling needed
- Multiple specialist referrals

**Use Case**: Demonstrates complex decision-making, multi-tier reasoning, and comprehensive evidence map generation.

---

## Using Sample Data

### Via API (cURL)

```bash
# Clean claim
curl -X POST http://localhost:8016/runs \
  -H "Content-Type: application/json" \
  -d @sample_data/sample_claim_clean.json

# Fraud case
curl -X POST http://localhost:8016/runs \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "claims_triage",
    "input_data": '$(cat sample_data/sample_claim_fraud.json)'
  }'

# Edge case
curl -X POST http://localhost:8016/runs \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "claims_triage",
    "input_data": '$(cat sample_data/sample_claim_edge_case.json)'
  }'
```

### Via Frontend UI

1. Navigate to http://localhost:3016/run-claim
2. Click "Load Sample Data" (if implemented)
3. Or manually copy fields from sample JSON files
4. Submit and watch live progress

### Via Python

```python
import requests
import json

# Load sample claim
with open('sample_data/sample_claim_clean.json') as f:
    claim_data = json.load(f)

# Submit to API
response = requests.post(
    'http://localhost:8016/runs',
    json={
        'workflow_id': 'claims_triage',
        'input_data': claim_data
    }
)

session = response.json()
print(f"Session ID: {session['session_id']}")
print(f"Stream URL: {session['stream_url']}")
```

## Data Structure

All sample claims follow the same comprehensive structure:

- **Claim Identification**: claim_id, policy_id, dates
- **Claimant Information**: Personal details, contact info, license
- **Policy Details**: Coverage type, limits, deductibles, status
- **Incident Details**: Location, description, conditions, police report
- **Vehicle Details**: Make, model, VIN, value, damage
- **Damage Assessment**: Areas affected, severity, estimates
- **Injuries**: Claimant, passengers, other parties, medical treatment
- **Witnesses**: Contact info and statements
- **Other Parties**: Drivers, insurers, fault admission
- **Documentation**: Photos, reports, estimates submitted
- **Claim History**: Previous claims, patterns
- **Fraud Indicators**: Flags for suspicious activity
- **Metadata**: Filing method, preferences, urgency

## Customizing Sample Data

To create your own test scenarios:

1. Copy one of the existing sample files
2. Modify the fields to create your desired scenario
3. Adjust fraud_indicators and complexity_factors to influence agent decisions
4. Add or remove documentation to test different completeness levels
5. Change claim_amount and coverage_limit to test policy limits

## Expected Agent Behaviors

### Intake Agent
- Validates all required fields present
- Normalizes data format
- Flags missing documentation

### Coverage Agent
- Determines coverage eligibility
- Calculates deductibles
- Checks policy limits and exclusions

### Fraud Agent
- Scores fraud risk based on indicators
- Checks claim history patterns
- Flags SIU referral when needed

### Severity Agent
- Assesses complexity level
- Estimates processing time
- Determines required expertise

### Recommendation Agent
- Assigns processing track
- Lists next steps
- Determines approval requirements

### Explainability Agent
- Compiles evidence map
- Documents decision rationale
- Lists assumptions and limitations
