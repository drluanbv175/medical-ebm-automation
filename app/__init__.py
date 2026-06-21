"""Medical EBM Automation – package gốc của ứng dụng.

Sub-packages:
  app.research_os  — ResearchOS: G0–G9 state machine, SAP engine, design router,
                      reporting guideline mapper, traceability matrix, causal
                      inference guards, data lock, methods review workflow.
                      100% in-memory; no SQLAlchemy dependency.
"""

__version__ = "0.1.0"


def get_research_os():
    """Return the app.research_os package (lazy import, no ORM dependency)."""
    import app.research_os as _ros  # noqa: PLC0415
    return _ros
