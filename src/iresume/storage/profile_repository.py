import json
from pathlib import Path

from iresume.models.profile import (
    Education,
    ExperienceHighlight,
    PersonalInfo,
    SkillCategory,
    SkillItem,
    UserProfile,
)


class ProfileRepository:
    def __init__(self, profile_dir: Path | str):
        self.profile_dir = Path(profile_dir)

    def load_raw(self) -> str:
        """Load all profile markdown as a single raw text block."""
        parts = []
        # Personal info first
        info = self.read_personal_info()
        if any([info.name, info.email, info.phone, info.desired_position]):
            lines = ["## 个人信息\n"]
            if info.name:
                lines.append(f"- 姓名: {info.name}")
            if info.age is not None:
                lines.append(f"- 年龄: {info.age}")
            if info.email:
                lines.append(f"- 邮箱: {info.email}")
            if info.phone:
                lines.append(f"- 电话: {info.phone}")
            if info.desired_position:
                lines.append(f"- 期望职位: {info.desired_position}")
            parts.append("\n".join(lines))

        for filename in ["education.md", "experience.md", "skills.md"]:
            path = self.profile_dir / filename
            if path.exists():
                content = path.read_text(encoding="utf-8").strip()
                if content:
                    parts.append(f"## {filename.replace('.md', '')}\n\n{content}")
        return "\n\n".join(parts)

    def read_raw(self, filename: str) -> str:
        path = self.profile_dir / filename
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def write_raw(self, filename: str, content: str) -> None:
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        (self.profile_dir / filename).write_text(content, encoding="utf-8")

    # ── Personal info ──

    def read_personal_info(self) -> PersonalInfo:
        path = self.profile_dir / "personal_info.json"
        if not path.exists():
            return PersonalInfo()
        data = json.loads(path.read_text(encoding="utf-8"))
        return PersonalInfo(**data)

    def write_personal_info(self, info: PersonalInfo) -> None:
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        data = info.model_dump(exclude_none=True)
        (self.profile_dir / "personal_info.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ── Education ──
    # Format: Free-form text blocks separated by blank lines.
    # First line: "学校 学位 时间"
    # Rest: 毕设/论文, 描述, 在校经历 etc.
    def _parse_education(self, path: Path) -> list[Education]:
        if not path.exists():
            return []
        text = path.read_text(encoding="utf-8")
        blocks = self._split_blank_line_blocks(text)
        result = []
        for block in blocks:
            lines = [l.strip() for l in block.strip().split("\n") if l.strip()]
            if not lines:
                continue
            header = lines[0]
            school, degree, period = self._parse_edu_header(header)
            body = "\n".join(lines[1:])

            thesis = self._extract_label(body, "毕设/论文")
            description = self._extract_label(body, "描述")
            # Combine thesis and description into courses/honors equivalent
            courses = []
            honors = []
            if thesis:
                courses.append(thesis)
            if description:
                courses.append(description)

            # Extract any honor-like lines (奖学金, etc.)
            for line in lines[1:]:
                if "奖学金" in line or "荣誉" in line or "优秀" in line:
                    clean = line.strip().lstrip("- ").strip()
                    if clean:
                        honors.append(clean)

            result.append(Education(
                school=school,
                degree=degree,
                period=period,
                gpa=None,
                courses=courses,
                honors=honors,
            ))
        return result

    @staticmethod
    def _parse_edu_header(line: str) -> tuple[str, str, str]:
        """Parse '天津大学 硕士 2018.09-2021.03' → (school, degree, period)."""
        parts = line.split()
        school = ""
        degree = ""
        period = ""
        for p in parts:
            if any(c.isdigit() for c in p) and ("." in p or "-" in p):
                period = p
            elif p in ("硕士", "博士", "学士", "本科", "专科", "研究生"):
                degree = p
            elif not school:
                school = p
            else:
                school += " " + p
        return school, degree, period

    # ── Experience ──
    # Format: H1 = company, H2 = "项目名 职位", body has 内容/技术/业绩 sections
    def _parse_experience(self, path: Path) -> list[ExperienceHighlight]:
        if not path.exists():
            return []
        text = path.read_text(encoding="utf-8")
        result = []

        # Split by H1 headings (company)
        company_blocks = self._split_h1_sections(text)
        for company, company_body in company_blocks:
            # Split each company by H2 headings (projects)
            project_blocks = self._split_h2_sections(company_body)
            for project_title, project_body in project_blocks:
                title_parts = project_title.rsplit("  ", 1)
                project_name = title_parts[0].strip() if title_parts else project_title
                role = title_parts[1].strip() if len(title_parts) > 1 else ""

                # Extract 业绩 section
                highlights = self._extract_highlights_from_body(project_body)
                result.append(ExperienceHighlight(
                    company=company,
                    role=role or project_name,
                    period="",
                    department=None,
                    highlights=highlights,
                ))
        return result

    # ── Skills ──
    def _parse_skills(self, path: Path) -> list[SkillCategory]:
        if not path.exists():
            return []
        text = path.read_text(encoding="utf-8")
        sections = self._split_h2_sections(text)
        result = []
        for title, body in sections:
            if title == "个人优势":
                continue
            items = []
            for line in body.strip().split("\n"):
                line = line.strip()
                if not line.startswith("-"):
                    continue
                line = line.lstrip("- ")
                if not line:
                    continue
                parts = line.split(":", 1)
                name = parts[0].strip()
                rest = parts[1].strip() if len(parts) > 1 else ""
                level = ""
                years = None
                if "(" in rest or "（" in rest:
                    level_part = rest.split("(")[0].split("（")[0].strip()
                    years_part = (
                        rest.split("(")[-1]
                        .split("（")[-1]
                        .replace(")", "")
                        .replace("）", "")
                        .replace("年", "")
                        .strip()
                    )
                    level = level_part
                    years = int(years_part) if years_part.isdigit() else None
                elif rest:
                    level = rest
                items.append(SkillItem(name=name, level=level, years=years))
            if items:
                result.append(SkillCategory(category=title, items=items))
        return result

    # ── Strengths ──
    # Format: "标题：内容" lines (no bullet prefix)
    def _parse_strengths(self, path: Path) -> list[str]:
        if not path.exists():
            return []
        text = path.read_text(encoding="utf-8")
        for section_title, body in self._split_h2_sections(text):
            if section_title == "个人优势":
                strengths = []
                for line in body.strip().split("\n"):
                    line = line.strip().lstrip("- ")
                    if not line:
                        continue
                    strengths.append(line)
                return strengths
        return []

    # ── Helpers ──

    @staticmethod
    def _split_h1_sections(text: str) -> list[tuple[str, str]]:
        """Split by '# ' headings, skip the first empty block."""
        sections = []
        current_title = ""
        current_body: list[str] = []
        found_first = False
        for line in text.split("\n"):
            if line.startswith("# ") and not line.startswith("## "):
                if found_first and (current_title or current_body):
                    sections.append((current_title, "\n".join(current_body)))
                found_first = True
                current_title = line[2:].strip()
                current_body = []
            elif found_first:
                current_body.append(line)
        if found_first and (current_title or current_body):
            sections.append((current_title, "\n".join(current_body)))
        return sections

    @staticmethod
    def _split_h2_sections(text: str) -> list[tuple[str, str]]:
        """Split by '## ' headings, skip content before first H2."""
        sections = []
        current_title = ""
        current_body: list[str] = []
        found_first = False
        for line in text.split("\n"):
            if line.startswith("## ") and not line.startswith("### "):
                if found_first and (current_title or current_body):
                    sections.append((current_title, "\n".join(current_body)))
                found_first = True
                current_title = line[3:].strip()
                current_body = []
            elif found_first:
                current_body.append(line)
        if found_first and (current_title or current_body):
            sections.append((current_title, "\n".join(current_body)))
        return sections

    @staticmethod
    def _split_blank_line_blocks(text: str) -> list[str]:
        """Split text into blocks separated by blank lines."""
        blocks = []
        current: list[str] = []
        for line in text.split("\n"):
            if not line.strip():
                if current:
                    blocks.append("\n".join(current))
                    current = []
            else:
                current.append(line)
        if current:
            blocks.append("\n".join(current))
        return blocks

    @staticmethod
    def _extract_label(body: str, label: str) -> str:
        """Extract value after 'label：' or 'label:' in body text."""
        for line in body.split("\n"):
            stripped = line.strip()
            for sep in ["：", ":"]:
                if stripped.startswith(label + sep):
                    return stripped[len(label) + len(sep):].strip()
        return ""

    @staticmethod
    def _extract_highlights_from_body(body: str) -> list[str]:
        """Extract bullet-style highlights from 业绩/内容 sections."""
        highlights = []
        in_highlights = False
        for line in body.split("\n"):
            stripped = line.strip()
            # Detect 业绩/内容 section headers
            if stripped.startswith("业绩") or stripped.startswith("内容"):
                in_highlights = True
                # If there's text after the colon on the same line, capture it
                for sep in ["：", ":"]:
                    if sep in stripped:
                        after = stripped.split(sep, 1)[1].strip()
                        if after:
                            highlights.append(after)
                        break
                continue
            if in_highlights:
                # Numbered items: "1.xxx" or "1. xxx"
                if stripped and (stripped[0].isdigit() or stripped.startswith("-") or stripped.startswith("●")):
                    # Remove leading number/bullet
                    clean = stripped.lstrip("0123456789.-) ●").strip()
                    if clean:
                        highlights.append(clean)
                elif stripped.startswith("技术"):
                    in_highlights = False
                elif not stripped:
                    continue
                elif not stripped[0].isdigit() and not stripped.startswith("-") and not stripped.startswith("●"):
                    # Might be a regular text line in the highlights section
                    # Keep it if it looks like a statement
                    if len(stripped) > 10:
                        highlights.append(stripped)
        return highlights
