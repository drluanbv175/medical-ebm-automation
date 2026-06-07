"""Module quản lý nghiên cứu y khoa."""
from app.research.manager import (add_project, list_projects, update_project,
                                  link_evidence, suggest_background_literature)
from app.research.dossier import (build_dossier_markdown, export_research_dossier,
                                  find_background_literature)
from app.research.checklists import (ACCEPTANCE_CHECKLIST, ETHICS_SUBMISSION_CHECKLIST,
                                     stats_suggestions, variable_framework)

__all__ = ["add_project", "list_projects", "update_project", "link_evidence",
           "suggest_background_literature", "build_dossier_markdown",
           "export_research_dossier", "find_background_literature",
           "ACCEPTANCE_CHECKLIST", "ETHICS_SUBMISSION_CHECKLIST",
           "stats_suggestions", "variable_framework"]
