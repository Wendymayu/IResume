from pydantic import BaseModel

from iresume.models.profile import Education


class ResumeHeader(BaseModel):
    name: str = ""
    phone: str | None = None
    email: str | None = None
    github: str | None = None
    location: str | None = None


class ResumeExperience(BaseModel):
    company: str
    role: str
    period: str
    highlights: list[str]


class ResumeSkillCategory(BaseModel):
    category: str
    items: list[str]


class ResumeContent(BaseModel):
    header: ResumeHeader
    summary: str
    experience: list[ResumeExperience]
    education: list[Education]
    skills_highlight: list[ResumeSkillCategory]


class SkillMatch(BaseModel):
    skill: str
    profile_level: str
    jd_requirement_level: str
    match_score: float  # 0.0 - 1.0


class GapReport(BaseModel):
    missing_skills: list[str]
    weak_skills: list[str]
    viability_score: float  # 0.0 - 1.0
    recommendation: str  # "proceed" | "proceed_with_caveats" | "not_viable"
