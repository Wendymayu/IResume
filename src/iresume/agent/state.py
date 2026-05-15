from operator import add
from typing import Annotated, Optional, TypedDict

from iresume.models.resume import GapReport, SkillMatch


class ResumeState(TypedDict):
    # Input
    jd_raw: str
    profile_path: str

    # Parsed JD (from jd_parser)
    jd_parsed: Optional[dict]

    # User profile (from profile_loader)
    profile: Optional[dict]

    # Skill matching (from skill_matcher)
    skill_matches: Annotated[list[dict], add]

    # Gap analysis (from gap_analyzer)
    gap_report: Optional[dict]

    # Generated resume content (from resume_generator)
    resume_content: Optional[dict]

    # Output
    resume_markdown: Optional[str]
    resume_path: Optional[str]

    # Metadata
    template_name: str
    errors: Annotated[list[str], add]
