from app.dashboard.v7_readonly import build_v7_readonly_snapshot


def test_v7_dashboard_snapshot_is_read_only_and_blocks_clinical_release():
    snapshot = build_v7_readonly_snapshot()

    assert snapshot.feature_flags["v7_read_only_dashboard"] is True
    assert snapshot.feature_flags["v7_clinical_release"] is False
    assert snapshot.feature_flags["v7_emr_write"] is False
    assert snapshot.feature_flags["v7_production_pathway"] is False
    assert snapshot.shadow_mode_status in {"ready_flag_off", "shadow_mode_enabled_read_only"}
    assert snapshot.last_updated
    assert snapshot.release_id == "not_available"
    assert "clinical_release_disabled" in snapshot.blocked_reasons
