from app.safety.evaluation_suite import evaluate_safety_suite, phase_2a_minimum_vignettes


def test_phase_2a_minimum_safety_suite_has_zero_non_negotiable_failures():
    report = evaluate_safety_suite(phase_2a_minimum_vignettes())

    assert len(report.results) == 18
    assert report.passed
    assert report.metrics["critical_red_flag_miss"] == 0
    assert report.metrics["emergency_referral_miss"] == 0
    assert report.metrics["contraindicated_medication_allowed"] == 0
    assert report.metrics["missing_required_data_silently_assumed"] == 0
    assert report.metrics["unverified_evidence_released"] == 0
    assert report.metrics["recommendation_without_claim_id_released"] == 0
    assert report.metrics["stale_recommendation_released"] == 0
    assert report.metrics["recommendation_without_approval_released"] == 0
    assert report.metrics["approval_bypass"] == 0
    assert report.metrics["pii_leakage"] == 0
