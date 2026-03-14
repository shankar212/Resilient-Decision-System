# Decision Explanation Examples

The system relies on an immutable `AuditLog` table to record decisions across stages. Below are examples showcasing traceability.

---

### Example 1: Happy Path Approval
**Input Payload**:
```json
{
  "applicant_name": "Alice Smith",
  "age": 25,
  "credit_score": 750
}
```

**Audit Trail Output (Summarized)**:
1. `WORKFLOW_STARTED`: Initialized "application_approval".
2. `STAGE_PASSED` (Stage: `stage_1_validation`): Both `applicant_name` and `age` were structurally present.
3. `STAGE_PASSED` (Stage: `stage_2_evaluation`): Evaluated rules successfully. 
   - `age >= 18` logic returned True.
   - `credit_score >= 650` logic returned True.
4. `DEPENDENCY_SUCCESS`: Mock "background_check_service" passed.
5. **Final Status**: `SUCCESS`

---

### Example 2: Rejected Due to Business Rule (Threshold)
**Input Payload**:
```json
{
  "applicant_name": "Bob Minor",
  "age": 16,
  "credit_score": 700
}
```

**Audit Trail Output (Summarized)**:
1. `WORKFLOW_STARTED`: Initialized
2. `STAGE_PASSED` (Stage: `stage_1_validation`)
3. `RULE_FAILED` (Stage: `stage_2_evaluation`, details: `{"failed_rule_id": "rule_min_age"}`)
   - System flagged that `age: 16` fails the `>= 18` constraint. 
   - Rule `on_fail` was marked `reject`.
4. **Final Status**: `REJECTED`

---

### Example 3: External Dependency Failure & Retry Resilience
**Input Payload**:
```json
{
  "applicant_name": "Charlie Flaky",
  "age": 30,
  "credit_score": 680,
  "force_dependency_failure": true
}
```

**Audit Trail Output (Summarized)**:
1. `WORKFLOW_STARTED`: Initialized
2. `STAGE_PASSED` (Stage: `stage_1_validation`)
3. `STAGE_PASSED` (Stage: `stage_2_evaluation`)
4. `DEPENDENCY_ERROR` (Stage: `stage_3_background_check`, details: `{"error": "Simulated connection timeout"}`)
5. **Final Status**: `RETRY` (Allows admin/system cron to manually intervene via `/requests/{id}/retry` and continue where it paused)
