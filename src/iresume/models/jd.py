from pydantic import BaseModel


class SkillRequirement(BaseModel):
    skill: str
    level: str  # "required" | "preferred" | "nice-to-have"
    importance: str  # "critical" | "important" | "minor"


class JobDescription(BaseModel):
    title: str
    company: str | None = None
    location: str | None = None
    salary_range: str | None = None
    required_skills: list[SkillRequirement] = []
    preferred_skills: list[SkillRequirement] = []
    responsibilities: list[str] = []
    education_requirements: str | None = None
    experience_requirements: str | None = None
    industry: str | None = None
    keywords: list[str] = []
