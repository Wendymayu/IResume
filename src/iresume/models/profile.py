from pydantic import BaseModel


class PersonalInfo(BaseModel):
    name: str = ""
    age: int | None = None
    email: str = ""
    phone: str = ""
    desired_position: str = ""


class Education(BaseModel):
    school: str
    degree: str
    period: str
    gpa: str | None = None
    courses: list[str] = []
    honors: list[str] = []


class ExperienceHighlight(BaseModel):
    company: str
    role: str
    period: str
    department: str | None = None
    highlights: list[str] = []


class SkillItem(BaseModel):
    name: str
    level: str  # "专家" | "熟练" | "了解"
    years: int | None = None


class SkillCategory(BaseModel):
    category: str  # "编程语言", "技术栈", etc.
    items: list[SkillItem]


class UserProfile(BaseModel):
    education: list[Education]
    experience: list[ExperienceHighlight]
    skills: list[SkillCategory]
    strengths: list[str]
