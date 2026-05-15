from pathlib import Path

from iresume.storage.profile_repository import ProfileRepository
from iresume.exporter.markdown_renderer import render_markdown


SAMPLE_EDUCATION = """天津大学 硕士 2018.09-2021.03
毕设/论文：液晶弹性体一致性板理论
描述：针对弹性体这种超材料，提出一种板壳近似理论。
在校经历：
2020获研究生国家奖学金

昆明理工大学 本科 2014.09-2018.06
"""

SAMPLE_EXPERIENCE = """# 字节跳动

## 抖音推荐系统 高级工程师
内容：
1.主导推荐系统重构，QPS提升300%
2.设计实时特征计算平台，日处理50TB+
业绩：
1.推荐系统上线后转化率提升15%
"""

SAMPLE_SKILLS = """# 技能与优势

## 编程语言
- Python: 专家 (8年)
- Go: 熟练 (3年)

## 个人优势
强业务导向：擅长将技术方案与业务目标对齐
快速学习：能在短时间内掌握新技术栈
"""


def test_parse_education(tmp_path: Path):
    (tmp_path / "education.md").write_text(SAMPLE_EDUCATION, encoding="utf-8")
    (tmp_path / "experience.md").write_text("", encoding="utf-8")
    (tmp_path / "skills.md").write_text("", encoding="utf-8")

    repo = ProfileRepository(tmp_path)
    profile = repo.load()

    assert len(profile.education) == 2
    assert profile.education[0].school == "天津大学"
    assert profile.education[0].degree == "硕士"
    assert profile.education[0].period == "2018.09-2021.03"
    assert any("液晶弹性体" in c for c in profile.education[0].courses)
    assert any("国家奖学金" in h for h in profile.education[0].honors)


def test_parse_experience(tmp_path: Path):
    (tmp_path / "education.md").write_text("", encoding="utf-8")
    (tmp_path / "experience.md").write_text(SAMPLE_EXPERIENCE, encoding="utf-8")
    (tmp_path / "skills.md").write_text("", encoding="utf-8")

    repo = ProfileRepository(tmp_path)
    profile = repo.load()

    assert len(profile.experience) == 1
    exp = profile.experience[0]
    assert exp.company == "字节跳动"
    assert "高级工程师" in exp.role
    assert len(exp.highlights) >= 2
    assert any("QPS" in h for h in exp.highlights)


def test_parse_skills(tmp_path: Path):
    (tmp_path / "education.md").write_text("", encoding="utf-8")
    (tmp_path / "experience.md").write_text("", encoding="utf-8")
    (tmp_path / "skills.md").write_text(SAMPLE_SKILLS, encoding="utf-8")

    repo = ProfileRepository(tmp_path)
    profile = repo.load()

    assert len(profile.skills) == 1  # "编程语言" category (个人优势 excluded)
    assert profile.skills[0].category == "编程语言"
    assert profile.skills[0].items[0].name == "Python"
    assert profile.skills[0].items[0].level == "专家"
    assert profile.skills[0].items[0].years == 8
    assert len(profile.strengths) == 2


def test_render_markdown():
    content = {
        "header": {
            "name": "张三",
            "phone": "138xxxx1234",
            "email": "zhangsan@email.com",
            "location": "北京",
        },
        "summary": "8年后端开发经验，专注高并发系统设计。",
        "experience": [
            {
                "company": "字节跳动",
                "role": "高级后端工程师",
                "period": "2021.07 - 至今",
                "highlights": ["主导推荐系统重构，QPS提升300%", "设计实时特征计算平台"],
            }
        ],
        "education": [
            {
                "school": "清华大学",
                "degree": "计算机科学与技术 硕士",
                "period": "2018.09 - 2021.06",
                "gpa": "3.8",
                "courses": ["机器学习"],
                "honors": ["国家奖学金"],
            }
        ],
        "skills_highlight": [
            {"category": "编程语言", "items": ["Python", "Go"]},
        ],
    }

    md = render_markdown(content)
    assert "# 张三" in md
    assert "138xxxx1234" in md
    assert "个人简介" in md
    assert "8年后端开发经验" in md
    assert "字节跳动" in md
    assert "QPS提升300%" in md
    assert "清华大学" in md
    assert "Python" in md


def test_read_write_raw(tmp_path: Path):
    repo = ProfileRepository(tmp_path)
    repo.write_raw("education.md", "# Test")
    assert repo.read_raw("education.md") == "# Test"
    assert repo.read_raw("nonexistent.md") == ""
