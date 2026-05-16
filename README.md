# IResume

AI Agent 驱动的智能简历生成系统。输入目标岗位描述 (JD)，自动分析匹配度并生成针对性简历。

## 功能概览

- **个人档案管理** — 维护教育背景、工作经历、技能等基础信息，作为简历生成的素材库
- **JD 解析** — 自动提取岗位描述中的关键要求、技术栈和软技能
- **技能匹配** — 将个人档案与 JD 要求进行对比，识别匹配点和缺口
- **差距分析** — 生成匹配度评分（viability score）和投递建议（推荐/可尝试/不建议）
- **简历生成** — 基于匹配结果，生成针对该岗位优化的 Markdown 简历

## 技术栈

| 层 | 技术 |
|---|------|
| 后端框架 | FastAPI (Python 3.11+) |
| AI Agent | LangGraph + LangChain |
| LLM | DeepSeek / OpenAI 兼容接口 |
| 前端 | Vue 3 + TypeScript + TailwindCSS |
| 构建工具 | Vite + Hatchling |

## 快速开始

### 环境要求

- Python >= 3.11
- Node.js >= 18
- LLM API Key（DeepSeek 或 OpenAI 兼容接口）

### 1. 克隆项目

```bash
git clone git@github.com:Wendymayu/IResume.git
cd IResume
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，填入 LLM 配置：

```env
IRESUME_LLM_PROVIDER=openai
IRESUME_LLM_MODEL=deepseek-chat
IRESUME_LLM_API_KEY=sk-your-api-key-here
IRESUME_LLM_BASE_URL=https://api.deepseek.com
```

### 3. 启动后端

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .

# 启动 API 服务（默认 http://localhost:8000）
iresume
```

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 `http://localhost:5173`。

### 5. 使用流程

1. 在「个人档案」页面填写教育背景、工作经历和技能
2. 进入「生成简历」页面，粘贴目标岗位的 JD
3. 点击「生成简历」，观察进度条实时反馈
4. 完成后自动展示简历预览和匹配分析，可下载 Markdown 文件

## 项目结构

```
IResume/
├── src/iresume/
│   ├── agent/          # LangGraph 节点和状态图
│   │   ├── nodes/      # jd_parser, skill_matcher, gap_analyzer 等
│   │   ├── prompts/    # 各节点的 LLM prompt 模板
│   │   ├── graph.py    # StateGraph 定义
│   │   └── state.py    # Agent 状态模型
│   ├── api/            # FastAPI 路由和中间件
│   ├── models/         # Pydantic 数据模型
│   ├── services/       # 任务管理和后台执行
│   ├── storage/        # 档案持久化
│   ├── exporter/       # Markdown 导出
│   ├── config.py       # 配置（环境变量）
│   └── main.py         # 应用入口
├── frontend/
│   └── src/
│       ├── views/      # ProfileView, ResumeView
│       └── api/        # Axios API 封装
├── docs/               # 文档
└── data/               # 运行时数据（profile、resumes）
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/profile` | 获取个人档案 |
| PUT | `/api/profile/education` | 更新教育背景 |
| PUT | `/api/profile/experience` | 更新工作经历 |
| PUT | `/api/profile/skills` | 更新技能 |
| POST | `/api/resume/generate` | 创建生成任务（返回 task_id） |
| GET | `/api/resume/tasks/{task_id}` | 查询任务状态和结果 |
| GET | `/api/resume/{resume_id}` | 获取已生成的简历 |
| GET | `/api/resume/{resume_id}/download` | 下载简历 Markdown |

## 架构说明

简历生成包含 4 次 LLM 调用，总耗时 60-120s。后端采用异步任务模式：POST 立即返回 `task_id`，后台执行各节点并通过内存任务管理器更新进度，前端每 2s 轮询进度。详见 [docs/optimilization/resume-generation-timeout.md](docs/optimilization/resume-generation-timeout.md)。
