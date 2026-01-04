# Explainability Tab Documentation

## Overview

The **Explainability** tab in the AgentMesh Observability interface provides transparent, comprehensive documentation of how the multi-agent system arrived at its claim decisions. This tab is designed to support regulatory compliance, audit requirements, customer communication, and internal quality assurance by making AI decision-making processes fully transparent and defensible.

## Purpose and Strategic Value

The Explainability tab addresses critical business needs:

- **Regulatory Compliance**: Provides complete audit trails required by insurance regulators
- **Decision Defense**: Enables claims adjusters to defend decisions to customers, lawyers, and auditors
- **Quality Assurance**: Supports systematic review and improvement of AI decision quality
- **Risk Management**: Explicitly documents assumptions and limitations to manage decision risk
- **Human-in-the-Loop Governance**: Tracks all human interventions for accountability
- **Stakeholder Communication**: Provides clear, understandable explanations for non-technical audiences

## Tab Structure

The Explainability tab consists of six primary sections, each providing different facets of decision transparency:

1. **Decision** - The final outcome and core decision metrics
2. **Supporting Evidence** - Detailed findings from each specialized agent
3. **Human Interventions** - Record of all human touchpoints
4. **Agent Execution Chain** - Sequence of agent invocations
5. **Assumptions** - Key assumptions underlying the decision
6. **Limitations** - Known constraints and data gaps

---

## Section 1: Decision

The Decision section presents the final claim outcome and core decision metrics at a glance.

### Fields

#### Final Decision Outcome
**Label**: Final Decision Outcome
**Description**: The definitive claim decision made by the system after analyzing all evidence. This represents the culmination of multi-agent analysis and determines the business action to be taken. Key outcomes include APPROVE (pay claim), DENY (reject claim), or REQUIRES_MANUAL_REVIEW (escalate to human).

**Typical Values**:
- `APPROVE_CLAIM` - Claim approved for payment
- `DENY_CLAIM` - Claim rejected/denied
- `REQUIRES_MANUAL_REVIEW` - Escalated to human review

#### Decision Confidence Score
**Label**: Decision Confidence Score
**Description**: Statistical confidence level (0-100%) indicating how certain the system is about its decision. Higher confidence scores (>85%) indicate strong convergent evidence across multiple analysis domains. This metric helps prioritize manual review resources and supports automated decision-making within risk tolerances.

**Interpretation**:
- **90-100%**: Very high confidence - strong convergent evidence
- **75-89%**: High confidence - solid evidence base
- **60-74%**: Medium confidence - may warrant review
- **<60%**: Low confidence - should escalate to manual review

**Displayed as**: Progress bar with percentage

#### Decision Rationale
**Label**: Decision Rationale
**Description**: Comprehensive explanation of WHY this decision was made, synthesizing evidence from all agents. This provides the narrative justification linking evidence to conclusion, ensuring decisions are explainable for regulatory compliance, audit trails, and customer communication. Critical for defending decisions and maintaining transparency.

**Use Cases**:
- Customer denial letters
- Legal defense documentation
- Regulatory audit responses
- Internal quality review

#### Financial Exposure
**Label**: Financial Exposure
**Description**: Total potential financial loss to the insurer if the claim is paid as submitted. This includes claimed damages, medical costs, legal reserves, and estimated claim handling expenses. Understanding exposure helps prioritize high-value claims for detailed investigation.

**Displayed as**: Dollar amount in red (risk indicator)

#### Potential Savings
**Label**: Potential Savings
**Description**: Estimated financial savings to the insurer from denying or reducing this claim. Calculated as the difference between claimed amount and actual assessed value.

**Displayed as**: Dollar amount in green (savings indicator)

---

## Section 2: Supporting Evidence

The Supporting Evidence section provides detailed findings from each specialized agent that contributed to the final decision.

### Section Overview
**Label**: Supporting Evidence from Agents
**Description**: Detailed findings from each specialized agent that contributed to the final decision. Each piece of evidence includes the source agent, analysis type, key findings, and relative weight in the decision. This granular view enables evidence tracing, quality assurance, and supports root cause analysis of decision outcomes.

### Per-Evidence Fields

#### Source Agent
**Description**: The specialized agent that produced this evidence
**Common Values**:
- `fraud_detection_agent`
- `policy_check_agent`
- `damage_assessment_agent`
- `injury_verification_agent`
- `document_validation_agent`
- `recommendation_agent`
- `explainability_agent`

#### Evidence Type
**Description**: The category of analysis performed
**Examples**:
- `fraud_analysis`
- `policy_verification`
- `damage_verification`
- `medical_verification`
- `documentation_analysis`
- `decision_synthesis`

#### Summary
**Description**: Detailed findings and key observations from the agent's analysis. This narrative explains what the agent discovered, why it matters, and how it contributes to the overall decision.

#### Evidence Weight
**Label**: Evidence Weight
**Description**: Relative importance (0-1.0) of this evidence in the final decision. Higher weights indicate evidence that had greater influence on the outcome. Weight allocation reflects domain expertise about which factors are most predictive and critical for accurate decision-making.

**Interpretation**:
- **0.25-0.30 (25-30%)**: Primary evidence - highest impact
- **0.15-0.24 (15-24%)**: Secondary evidence - significant impact
- **0.05-0.14 (5-14%)**: Supporting evidence - moderate impact
- **<0.05 (<5%)**: Contextual evidence - minor impact

**Note**: All evidence weights across all agents sum to exactly 100%

#### Fraud Risk Score
**Label**: Fraud Risk Score
**Description**: Quantitative assessment (0-100%) of fraud likelihood based on statistical models, pattern matching, and known fraud indicators. Scores above 70% typically trigger enhanced scrutiny or SIU investigation. This metric enables risk stratification and prioritization of investigative resources.

**Interpretation**:
- **>85%**: Very high fraud risk - SIU investigation recommended
- **70-85%**: High fraud risk - enhanced scrutiny required
- **50-69%**: Moderate fraud risk - additional verification
- **<50%**: Low fraud risk - standard processing

**Only displayed when**: Agent provides a risk score (typically fraud_detection_agent)

---

## Section 3: Human Interventions

The Human Interventions section records all human touchpoints in the decision process, creating a complete audit trail.

### Section Overview
**Label**: Human Review & Interventions
**Description**: Record of all human touchpoints in the decision process - including checkpoints, reviews, approvals, or overrides. This creates an audit trail showing when humans were involved, what they reviewed, and how they influenced the outcome. Essential for accountability, compliance, and human-in-the-loop governance.

### Per-Intervention Fields

#### Intervention Type
**Description**: Category of human intervention
**Common Values**:
- `checkpoint_review` - Scheduled review checkpoint
- `manual_override` - Human override of AI decision
- `siu_escalation` - Special Investigations Unit escalation
- `quality_assurance` - QA review
- `appeals_review` - Customer appeal review

#### Timestamp
**Description**: When the intervention occurred
**Format**: Human-readable date and time (e.g., "Mar 15, 2024, 2:23 PM")

#### Reviewer
**Description**: Name and role of the human reviewer
**Example**: "Senior Claims Examiner - Sarah Martinez"

#### Checkpoint
**Description**: The specific checkpoint in the workflow where intervention occurred
**Common Values**:
- `before_completion`
- `after_denial`
- `high_value_claim`
- `fraud_detected`

#### Action
**Description**: What action the reviewer took
**Common Values**:
- `approved` - Reviewer approved AI decision
- `rejected` - Reviewer rejected AI decision
- `modified` - Reviewer modified decision parameters
- `escalated` - Reviewer escalated for additional review
- `accepted_for_investigation` - SIU accepted case

**Displayed as**: Green badge for approved actions

#### Comments
**Description**: Reviewer's notes and observations about the decision. Provides qualitative human judgment and reasoning.

**Use Cases**:
- Audit trail documentation
- Handoff communication
- Quality improvement feedback
- Legal defense support

#### Decision Impact
**Description**: How the intervention affected the final decision
**Examples**:
- "Confirmed denial recommendation; added SIU escalation"
- "Modified claim amount from $45,000 to $18,000"
- "Overrode AI denial; approved claim with conditions"

---

## Section 4: Agent Execution Chain

The Agent Chain section visualizes the sequence of specialized agents that analyzed the claim.

### Section Overview
**Label**: Agent Execution Sequence
**Description**: The ordered sequence of specialized agents that analyzed this claim. This execution flow shows how information flowed through the system, which agents were invoked, and in what order. Understanding the agent chain helps diagnose system behavior, optimize workflows, and ensure comprehensive coverage of all risk domains.

### Interpretation

**Visual Display**: Agents displayed as badges with arrows (→) showing execution sequence

**Typical Execution Flow**:
1. `fraud_detection_agent` - Initial fraud screening
2. `policy_check_agent` - Policy validity verification
3. `damage_assessment_agent` - Physical damage evaluation
4. `injury_verification_agent` - Medical claims validation
5. `document_validation_agent` - Document authenticity check
6. `recommendation_agent` - Decision synthesis
7. `explainability_agent` - Decision explanation generation

**Use Cases**:
- Debugging workflow issues
- Optimizing agent invocation order
- Ensuring comprehensive risk domain coverage
- Performance analysis and optimization

---

## Section 5: Assumptions

The Assumptions section explicitly documents key assumptions underlying the decision.

### Section Overview
**Label**: Decision Assumptions
**Description**: Key assumptions underlying the decision that, if invalid, could affect the outcome. Explicitly documenting assumptions is critical for risk management - it identifies which factors, if changed or proven incorrect, might require decision revision. This supports scenario analysis and sensitivity testing of decisions.

### Format
Bullet list of assumptions

### Example Assumptions
- "Digital forensic analysis tools accurately detect metadata manipulation with 95%+ accuracy"
- "Cross-carrier fraud database is current and complete as of investigation date"
- "Vehicle valuation from KBB represents fair market value within +/- 10% margin"
- "Witness statement pattern matching algorithm has <2% false positive rate"
- "Social network analysis correctly identifies connections within 2 degrees of separation"

### Strategic Importance

**Risk Management**: Identifies decision dependencies
**Scenario Testing**: Enables "what-if" analysis of different assumptions
**Quality Assurance**: Highlights areas requiring validation
**Continuous Improvement**: Identifies assumptions to test and refine

---

## Section 6: Limitations

The Limitations section transparently communicates known constraints and data gaps.

### Section Overview
**Label**: Known Limitations
**Description**: Acknowledged constraints, data gaps, or uncertainties in the analysis. Transparently communicating what the system CANNOT determine is as important as what it can. This manages expectations, identifies areas requiring human judgment, and prevents overconfidence in automated decisions.

### Format
Bullet list of limitations

### Example Limitations
- "Cannot definitively prove intent - relies on pattern recognition and probability"
- "Social network analysis limited to publicly available information and insurer databases"
- "Vehicle damage assessment based on photos - in-person inspection would provide additional confidence"
- "Medical evaluation relies on records review - independent medical examination was declined"
- "Some fraud indicators (e.g., 'known fraud hotspot') based on geographic correlation, not causation"
- "Decision made without interviewing claimant under oath - SIU investigation may reveal additional factors"

### Strategic Importance

**Expectation Management**: Sets realistic boundaries on AI capabilities
**Human Judgment**: Identifies areas requiring human expertise
**Risk Awareness**: Highlights uncertainty in decision confidence
**Legal Defense**: Documents known constraints for defensibility
**Continuous Improvement**: Identifies gaps to address in future iterations

---

## Demo Data Fallback

When a session does not have complete evidence data (e.g., workflow failed or incomplete), the Explainability tab automatically displays a comprehensive **demo evidence map** showing a fraud detection scenario. This demo:

- Showcases all 7 specialized agents in action
- Demonstrates complete evidence structure
- Illustrates human interventions (checkpoint review and SIU escalation)
- Provides educational value for stakeholders
- Shows the strategic value of evidence-based decision making

**Note**: The demo data is clearly indicated to users (banner removed as of latest version) and serves demonstration purposes only.

---

## Interactive Features

### Information Tooltips (ℹ️ Icons)

Every major field includes an **information tooltip** (blue ℹ️ icon) that provides:
- **2-3 sentence explanations** of what the field means
- **Strategic context** on why it matters for business decisions
- **Usage guidance** on how to interpret values

**How to Use**: Hover over the ℹ️ icon next to any field label to see the detailed explanation

### Evidence Weight Visualization

Evidence weights are displayed both as:
- **Percentage values** (e.g., "27%")
- **Relative comparisons** across all agents (should sum to 100%)

This allows quick visual assessment of which evidence had the most influence on the decision.

### Financial Metrics Display

Financial exposure and potential savings are:
- **Color-coded**: Red for exposure (risk), Green for savings (benefit)
- **Formatted with thousands separators**: $45,000 (readable)
- **Side-by-side comparison**: Easy cost-benefit analysis

---

## Use Cases and Workflows

### 1. Regulatory Audit Response
**Scenario**: Regulator requests documentation of AI decision-making process

**Workflow**:
1. Navigate to Explainability tab for questioned claim
2. Export Decision Rationale for narrative explanation
3. Reference Supporting Evidence for agent-by-agent breakdown
4. Include Assumptions and Limitations for transparency
5. Attach Human Interventions log for accountability

**Key Sections**: All sections, particularly Decision Rationale and Human Interventions

### 2. Customer Denial Explanation
**Scenario**: Customer challenges claim denial and requests explanation

**Workflow**:
1. Review Decision Rationale for plain-language summary
2. Extract key findings from Supporting Evidence
3. Note Human Interventions showing senior examiner approval
4. Reference specific fraud indicators and policy violations
5. Draft denial letter incorporating decision basis

**Key Sections**: Decision, Supporting Evidence, Human Interventions

### 3. SIU Investigation Support
**Scenario**: Fraud indicators detected, need SIU escalation documentation

**Workflow**:
1. Check Fraud Risk Score from fraud_detection_agent
2. Review all Supporting Evidence for fraud indicators
3. Document Financial Exposure for case prioritization
4. Note existing Human Interventions (checkpoint reviews)
5. Compile comprehensive evidence package for SIU

**Key Sections**: Supporting Evidence (especially fraud_detection_agent), Financial Exposure

### 4. Quality Assurance Review
**Scenario**: Systematic review of AI decision quality

**Workflow**:
1. Sample claims across confidence score ranges
2. Review Decision Confidence vs actual outcomes
3. Analyze Evidence Weight distributions for bias
4. Validate Assumptions against ground truth
5. Identify Limitations requiring process improvements

**Key Sections**: Decision Confidence, Evidence Weight, Assumptions, Limitations

### 5. Workflow Optimization
**Scenario**: Improve agent orchestration efficiency

**Workflow**:
1. Examine Agent Execution Chain across multiple claims
2. Identify redundant or unnecessary agent invocations
3. Analyze execution order for logical dependencies
4. Measure evidence contribution vs computational cost
5. Optimize workflow configuration

**Key Sections**: Agent Chain, Evidence Weight

---

## Best Practices

### For Claims Adjusters
1. **Always review Decision Rationale first** - Get the high-level summary
2. **Check Confidence Score** - Low confidence (<75%) warrants additional scrutiny
3. **Examine top-weighted evidence** - Focus on agents with highest weights
4. **Review Human Interventions** - Understand what colleagues have already reviewed
5. **Note Limitations** - Identify areas where human judgment may be needed

### For Auditors
1. **Verify completeness of Agent Chain** - All required risk domains covered
2. **Validate Assumptions** - Check if assumptions are reasonable and documented
3. **Review Human Interventions audit trail** - Ensure proper governance
4. **Check evidence consistency** - Supporting Evidence aligns with Decision Rationale
5. **Assess transparency** - Limitations honestly documented

### For Technical Teams
1. **Monitor Evidence Weight distributions** - Detect bias or misconfiguration
2. **Track Confidence Score correlations** - Validate predictive accuracy
3. **Analyze Agent Chain patterns** - Optimize workflow efficiency
4. **Review Assumptions** - Identify opportunities for improved data sources
5. **Address Limitations** - Prioritize technical improvements

### For Executives
1. **Focus on Financial Metrics** - Exposure and Savings at a glance
2. **Review Fraud Risk Scores** - Portfolio-level risk assessment
3. **Monitor Human Intervention rates** - Gauge AI autonomy vs oversight
4. **Track Confidence Score trends** - System learning and improvement
5. **Assess strategic Limitations** - Investment priorities for AI enhancement

---

## Technical Implementation Notes

### Data Source
Evidence data is retrieved from the backend API endpoint:
```
GET /sessions/{session_id}/evidence
```

Returns an `EvidenceMap` object containing:
- `decision` - Decision outcome and metrics
- `supporting_evidence` - Array of agent findings
- `agent_chain` - Ordered agent execution sequence
- `assumptions` - Array of assumption strings
- `limitations` - Array of limitation strings
- `human_interventions` - Array of intervention records
- `metadata` - Session metadata (timestamp, version, etc.)

### Demo Data Fallback Logic
The tab automatically detects minimal/incomplete evidence using these criteria:
- `evidence_map.partial === true`
- `evidence_map.no_output === true`
- `decision.outcome` is missing or "N/A"
- `supporting_evidence` array is empty

When detected, the system displays `DEMO_EVIDENCE_MAP` from `/lib/demo-evidence.ts`

### Field Explanations
All tooltip content is defined in `FIELD_EXPLANATIONS` object in `/lib/demo-evidence.ts`, making it easy to update explanations without code changes.

---

## Frequently Asked Questions

### Q: Why are some fields showing demo data?
**A**: The session did not complete successfully or generate complete evidence. Demo data is displayed to show what a complete evidence map looks like for educational purposes.

### Q: What does a good Confidence Score look like?
**A**: Scores above 85% indicate very strong evidence. Scores between 70-85% are typical for solid decisions. Scores below 70% may warrant manual review depending on claim complexity and financial exposure.

### Q: Why don't all agents appear in every claim?
**A**: The orchestrator dynamically invokes agents based on claim characteristics and workflow state. Not all agents are needed for every claim type. The Agent Chain shows which agents were actually invoked.

### Q: Can I override an AI decision?
**A**: Yes. Human reviewers can override AI decisions at designated checkpoints. All overrides are recorded in the Human Interventions section with full audit trails.

### Q: What if evidence weights don't sum to 100%?
**A**: This indicates a data integrity issue. Evidence weights should always sum to exactly 1.0 (100%). Contact technical support if you observe discrepancies.

### Q: How are fraud scores calculated?
**A**: Fraud scores are calculated by the fraud_detection_agent using statistical models, pattern matching against known fraud schemes, and analysis of fraud indicators. The specific algorithm is proprietary but based on industry-standard fraud detection techniques.

### Q: What happens if assumptions are violated?
**A**: Documented assumptions help identify when decisions may need revision. If an assumption is proven incorrect (e.g., data source was outdated), the claim should be re-evaluated with updated information.

### Q: Why document limitations?
**A**: Transparency about what the AI cannot determine is critical for:
- Managing stakeholder expectations
- Identifying areas requiring human judgment
- Legal defensibility (we acknowledge constraints)
- Continuous improvement priorities

---

## Related Documentation

- **Observability Overview**: General guide to the Observability tab and its three sub-tabs
- **Token Analytics Tab**: Documentation of context compilation and token budget management
- **Event Timeline Tab**: Documentation of session event replay and debugging
- **Context Engineering System**: Technical documentation of the 4-tier context architecture
- **Agent Registry**: Reference guide to all specialized agents and their capabilities
- **Governance Policies**: Documentation of access control and execution constraints

---

## Version History

- **v1.0** (2024-03-15) - Initial release with 7 specialized agents
  - Added Decision, Supporting Evidence, Agent Chain, Assumptions, Limitations
  - Implemented demo data fallback mechanism
  - Added comprehensive field tooltips

- **v1.1** (2024-03-18) - Human Interventions enhancement
  - Added Human Interventions section
  - Expanded tooltip explanations for strategic context
  - Improved financial metrics visualization

- **v2.0** (2026-01-03) - Tab renaming and UI refinement
  - Renamed "Evidence" tab to "Explainability"
  - Removed demo data banner (demo still functions as fallback)
  - Corrected evidence weight calculations to sum to 100%
  - Enhanced tooltip accessibility

---

## Contact and Support

For questions, issues, or feedback regarding the Explainability tab:

- **Technical Support**: Contact your AgentMesh system administrator
- **Feature Requests**: Submit via GitHub issues at [AgentMesh Repository]
- **Documentation Updates**: Contribute via pull request to EXPLAINABILITY_TAB_DOCUMENTATION.md

---

**Last Updated**: January 3, 2026
**Document Version**: 2.0
**Maintained By**: AgentMesh Development Team
