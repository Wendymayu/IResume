# IResume - AI Agent 简历生成与自动投递系统 实现方案

## Context

用户需要一个基于 AI Agent 的简历生成系统：输入个人经历，根据 JD 生成针对性简历，后续扩展自动搜索和投递功能。项目为全新空白项目，采用 LangGraph + Python + Vue 技术栈。

**Phase 1 MVP 目标**：先实现 Markdown 格式简历输出，PDF 导出后续迭代。

---

## 技术选型

| 层面 | 选择 | 理由 |
|------|------|------|
| Agent 框架 | LangGraph | 有状态图、支持并行/条件边、可视化、社区成熟 |
| LLM | OpenAI API (兼容 DeepSeek 等) | 通过 `llm_base_url` 配置，灵活切换 |
| 简历输出 | **先 Markdown，后 PDF** | MVP 先打通核心链路，Markdown 即可预览和下载 |
| PDF 生成 (后续) | WeasyPrint (HTML→PDF) | 纯 Python、CSS3 完整支持、中文字体处理简单 |
| 后端 | FastAPI + Uvicorn | 异步、自动文档、SSE 流式支持 |
| 前端 | Vue 3 + Vite + TailwindCSS | 轻量 MVP |
| 存储 | Markdown 文件 | 用户可直接编辑、版本控制友好 |
| 爬虫 (P2) | Playwright | 反检测能力强、API 友好 |

---

## 项目结构

```
IResume/
├── pyproject.toml
├── .env.example
├── .gitignore
├── src/iresume/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 入口
│   ├── config.py                  # Pydantic Settings
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── state.py               # ResumeState TypedDict
│   │   ├── graph.py               # LangGraph StateGraph 构建
│   │   ├── nodes/
│   │   │   ├── __init__.py
│   │   │   ├── jd_parser.py       # JD 解析节点
│   │   │   ├── profile_loader.py  # 用户档案加载节点
│   │   │   ├── skill_matcher.py   # 技能匹配节点
│   │   │   ├── gap_analyzer.py    # 缺口分析节点
│   │   │   ├── resume_generator.py # 简历生成节点(核心)
│   │   │   └── markdown_exporter.py # Markdown 导出节点
│   │   └── prompts/
│   │       ├── jd_parser_prompt.py
│   │       ├── skill_matcher_prompt.py
│   │       ├── gap_analyzer_prompt.py
│   │       └── resume_generator_prompt.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── jd.py
│   │   ├── profile.py
│   │   └── resume.py
│   ├── storage/
│   │   ├── __init__.py
│   │   └── profile_repository.py  # Markdown 读写
│   ├── exporter/
│   │   ├── __init__.py
│   │   └── markdown_renderer.py   # Markdown 简历渲染
│   │   # 后续迭代:
│   │   # ├── pdf_renderer.py     # WeasyPrint PDF 封装
│   │   # └── templates/          # Jinja2 HTML 模板
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   ├── middleware.py
│   │   └── routes/
│   │       ├── profile.py
│   │       └── resume.py
│   ├── scraper/                   # Phase 2
│   │   ├── base.py
│   │   ├── boss_zhipin.py
│   │   ├── maimai.py
│   │   └── qiancheng.py
│   ├── applier/                   # Phase 3
│   │   ├── form_filler.py
│   │   ├── captcha_handler.py
│   │   └── application_tracker.py
│   └── utils/
│       ├── __init__.py
│       ├── llm.py
│       └── logger.py
├── data/
│   ├── profile/
│   │   ├── education.md
│   │   ├── experience.md
│   │   └── skills.md
│   └── resumes/                   # 生成的简历存放处
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── App.vue
│       ├── main.ts
│       ├── api/index.ts
│       ├── views/
│       │   ├── ProfileView.vue
│       │   └── ResumeView.vue
│       └── components/
│           ├── ProfileEditor.vue
│           ├── JdInput.vue
│           └── ResumePreview.vue
└── tests/
    ├── test_agent/
    ├── test_api/
    └── test_exporter/
```

---

## LangGraph Agent 设计

### 状态定义 (state.py)

```python
class ResumeState(TypedDict):
    # 输入
    jd_raw: str
    profile_path: str
    # 中间状态
    jd_parsed: Optional[dict]
    profile: Optional[dict]
    skill_matches: Annotated[list[SkillMatch], add]
    gap_report: Optional[GapReport]
    resume_content: Optional[dict]    # 结构化简历内容
    # 输出
    resume_markdown: Optional[str]    # 生成的 Markdown 简历
    resume_path: Optional[str]        # 保存的文件路径
    # 后续迭代
    # pdf_bytes: Optional[bytes]
    # 元数据
    template_name: str                # "professional" | "concise"
    errors: Annotated[list[str], add]
```

### Agent 流程图

```
[START]
   │
   ├──→ [jd_parser] ──────────────┐
   │    (LLM: 解析JD为结构化数据)    │
   │                               ├──→ [skill_matcher] ──→ [gap_analyzer]
   ├──→ [profile_loader] ─────────┘    (LLM: 技能匹配)      (LLM: 缺口分析)
   │    (纯IO: 加载Markdown)                                  │
   │                                                ┌────────┼──────────┐
   │                                           not_viable    proceed   with_caveats
   │                                                │          │          │
   │                                             [END]  [resume_generator]
   │                                                    (LLM: 生成简历)
   │                                                         │
   │                                                [markdown_exporter]
   │                                                 (渲染Markdown)
   │                                                         │
   │                                                       [END]
```

关键设计：
- `start` 节点扇出 → `jd_parser` 和 `profile_loader` 并行执行
- `skill_matcher` 等待两者都完成（LangGraph fan-in）
- `gap_analyzer` 条件边：viability_score >= 0.5 → proceed, >= 0.3 → with_caveats, < 0.3 → END
- `markdown_exporter` 将 `resume_content` 渲染为格式化的 Markdown 文本并保存文件

### 各节点职责

| 节点 | 输入 | 输出 | LLM? |
|------|------|------|------|
| jd_parser | jd_raw | jd_parsed (title, required_skills, etc.) | Yes |
| profile_loader | profile_path | profile (education, experience, skills) | No |
| skill_matcher | jd_parsed + profile | skill_matches (scored list) | Yes |
| gap_analyzer | skill_matches + jd_parsed + profile | gap_report (viability_score, recommendation) | Yes |
| resume_generator | profile + jd_parsed + skill_matches + gap_report | resume_content (structured resume sections) | Yes |
| markdown_exporter | resume_content | resume_markdown + resume_path | No |

---

## Markdown 数据格式

### 用户档案 (`data/profile/`)

`education.md`:
```markdown
# 教育经历

## 清华大学
- **学位**: 计算机科学与技术 硕士
- **时间**: 2018.09 - 2021.06
- **核心课程**: 机器学习、深度学习、自然语言处理
- **荣誉**: 国家奖学金
```

`experience.md`:
```markdown
# 工作经历

## 字节跳动 | 高级后端工程师
- **时间**: 2021.07 - 至今
- **部门**: 抖音电商技术部

### 核心业绩
- 主导推荐系统重构，QPS提升300%
- 设计实时特征计算平台，日处理50TB+
```

`skills.md`:
```markdown
# 技能与优势

## 编程语言
- Python: 专家 (8年)
- Go: 熟练 (3年)

## 个人优势
- 强烈的业务导向思维
- 优秀的跨团队沟通能力
```

### 生成的简历 Markdown 格式

```markdown
# 张三 | 高级后端工程师

📞 138xxxx1234 | ✉️ zhangsan@email.com | 📍 北京

---

## 个人简介

8年后端开发经验，专注高并发系统设计与推荐系统架构...

## 工作经历

### 字节跳动 | 高级后端工程师
*2021.07 - 至今 | 抖音电商技术部*

- 主导电商推荐系统重构，QPS提升300%，转化率提升15%（与JD要求的推荐系统经验高度匹配）
- 设计实时特征计算平台，日处理50TB+数据
- ...

## 教育经历

### 清华大学 | 计算机科学与技术 硕士
*2018.09 - 2021.06*

## 专业技能

- **编程语言**: Python(专家)、Go(熟练)
- **推荐系统**: PyTorch、TensorFlow、XGBoost
- **后端开发**: FastAPI、gRPC、Kafka、Redis
```

---

## API 设计

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/profile` | 获取用户档案 |
| PUT | `/api/profile/education` | 更新教育经历 (Markdown body) |
| PUT | `/api/profile/experience` | 更新工作经历 |
| PUT | `/api/profile/skills` | 更新技能 |
| POST | `/api/resume/generate` | 输入JD生成简历 (返回 Markdown) |
| POST | `/api/resume/generate/stream` | SSE 流式生成 |
| GET | `/api/resume/{id}` | 获取生成的简历 Markdown |
| GET | `/api/resume/{id}/download` | 下载 .md 文件 |

---

## 实现顺序 (Phase 1 MVP)

1. **项目脚手架**：pyproject.toml、目录结构、.gitignore、config.py
2. **数据模型**：所有 Pydantic models (jd.py, profile.py, resume.py)
3. **Markdown 存储**：ProfileRepository 读写
4. **LLM 客户端工厂**：可配置 provider（支持 OpenAI/DeepSeek）
5. **Prompt 模板**：4个节点的提示词
6. **Agent 节点**：逐个实现
   - jd_parser (LLM)
   - profile_loader (纯 IO)
   - skill_matcher (LLM)
   - gap_analyzer (LLM)
   - resume_generator (LLM, 核心)
   - markdown_exporter (纯渲染)
7. **LangGraph 图**：graph.py 串联所有节点
8. **Markdown 渲染器**：将结构化简历内容渲染为格式化 Markdown
9. **API 端点**：FastAPI 路由
10. **前端**：Vue 最小 MVP（档案编辑 + JD输入 + Markdown 预览/下载）
11. **端到端测试**

### 后续迭代：PDF 导出

- 新增 `pdf_renderer.py`，使用 WeasyPrint 将 Markdown→HTML→PDF
- 新增 Jinja2 HTML 模板（professional / concise）
- 内置 Noto Sans SC 字体
- API 增加 `/api/resume/{id}/download/pdf` 端点

---

## Phase 2 概要：岗位搜索

- Playwright BaseScraper (反检测：UA伪装、webdriver隐藏、随机延迟)
- Boss直聘 → 脉脉 → 前程无忧 依次实现
- `/api/jobs/search` 聚合去重后返回岗位列表
- `/api/jobs/{id}/match` 计算岗位匹配度
- `/api/jobs/{id}/resume` 为特定岗位生成简历
- 前端增加岗位搜索和匹配度展示

## Phase 3 概要：自动投递

- 滑块验证码：OpenCV 模板匹配 + 人类鼠标轨迹模拟
- SMS 验证码：人工介入通知
- ApplicationTracker：SQLite 记录投递状态，防重复
- 安全护栏：每日上限20、最小间隔60s、dry-run 模式

---

## 验证方式

1. 启动后端 `uvicorn iresume.main:app --reload`
2. 启动前端 `cd frontend && npm run dev`
3. 在 ProfileView 填写教育/工作/技能信息
4. 在 ResumeView 粘贴一段 JD，点击生成
5. 查看技能匹配结果和缺口分析
6. 预览生成的 Markdown 简历，下载 .md 文件
