from iresume.models.resume import ResumeContent


def render_markdown(content: dict) -> str:
    """Render structured resume content into formatted Markdown."""
    resume = ResumeContent.model_validate(content)
    lines: list[str] = []

    # Header
    header = resume.header
    name = header.name or "姓名"
    contact_parts = []
    if header.phone:
        contact_parts.append(f"📞 {header.phone}")
    if header.email:
        contact_parts.append(f"✉️ {header.email}")
    if header.location:
        contact_parts.append(f"📍 {header.location}")
    if header.github:
        contact_parts.append(f"🔗 {header.github}")

    lines.append(f"# {name}")
    if contact_parts:
        lines.append("")
        lines.append(" | ".join(contact_parts))
    lines.append("")
    lines.append("---")
    lines.append("")

    # Summary
    if resume.summary:
        lines.append("## 个人简介")
        lines.append("")
        lines.append(resume.summary)
        lines.append("")

    # Experience
    if resume.experience:
        lines.append("## 工作经历")
        lines.append("")
        for exp in resume.experience:
            lines.append(f"### {exp.company} | {exp.role}")
            lines.append(f"*{exp.period}*")
            lines.append("")
            for h in exp.highlights:
                lines.append(f"- {h}")
            lines.append("")

    # Skills
    if resume.skills_highlight:
        lines.append("## 专业技能")
        lines.append("")
        for cat in resume.skills_highlight:
            items_str = "、".join(cat.items)
            lines.append(f"- **{cat.category}**: {items_str}")
        lines.append("")

    # Education
    if resume.education:
        lines.append("## 教育经历")
        lines.append("")
        for edu in resume.education:
            lines.append(f"### {edu.school} | {edu.degree}")
            lines.append(f"*{edu.period}*")
            if edu.gpa:
                lines.append(f"GPA: {edu.gpa}")
            if edu.courses:
                lines.append(f"核心课程: {'、'.join(edu.courses)}")
            if edu.honors:
                lines.append(f"荣誉: {'、'.join(edu.honors)}")
            lines.append("")

    return "\n".join(lines)
