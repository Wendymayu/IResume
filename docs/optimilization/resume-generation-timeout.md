# 简历生成超时问题及优化方案

## 问题描述

简历生成流程串行调用 4 次 LLM（DeepSeek），每次响应耗时 10-20s，总耗时 60-120s。前端通过 `POST /api/resume/generate` **同步等待**完整流程结束后才拿到响应，导致：

- 浏览器连接长时间挂起，可能触发网关/浏览器超时
- 用户看不到任何进度反馈，以为页面卡死
- 无法区分"正在生成"和"服务异常"两种状态

### 优化前架构

```
用户点击 → POST /generate → graph.invoke() → jd_parser
                                               → profile_loader
                                               → skill_matcher
                                               → gap_analyzer
                                               → resume_generator
                                               → markdown_exporter
                                               → 返回结果给前端
                           (全程阻塞，60-120s 无响应)
```

### 根因

1. **同步阻塞**：`graph.invoke()` 是同步调用，在 FastAPI 异步 handler 中执行时会阻塞事件循环
2. **无进度反馈**：LangGraph 的 `invoke()` 只返回最终结果，不提供中间状态
3. **超时窗口长**：前端 axios 虽然设置了 120s 超时，但长时间无响应的体验极差

---

## 优化方案：Task + Polling

### 设计思路

将同步调用改为异步任务模式：

1. `POST /api/resume/generate` 立即返回 `{ task_id: "xxx" }`，不阻塞
2. 后端 `asyncio.create_task` 在后台依次执行各节点
3. 每执行完一个节点，更新任务状态（进度百分比 + 中文描述）
4. 前端每 2s 轮询 `GET /api/resume/tasks/{task_id}` 获取最新状态
5. 任务完成后，前端自动展示结果或错误信息

### 架构图

```
前端                           FastAPI                         节点函数
  |                              |                               |
  |-- POST /generate ----------->|                               |
  |                              |-- create_task()               |
  |<-- { task_id: "abc" } -------|                               |
  |                              |                               |
  |                              |-- asyncio.create_task(        |
  |                              |     run_resume_generation)    |
  |                              |                               |
  |                              |  update_task(10%, "解析JD")   |
  |                              |  → to_thread(jd_parser.run)  |
  |                              |                               |
  |-- GET /tasks/abc ----------->|                               |
  |<-- { status: "running",      |                               |
  |       progress_pct: 10 } ----|                               |
  |                              |                               |
  |   (每 2s 轮询...)            |  update_task(40%, "技能匹配")   |
  |                              |  → to_thread(skill_matcher)  |
  |                              |                               |
  |                              |  update_task(75%, "生成简历")  |
  |                              |  → to_thread(resume_generator)|
  |                              |                               |
  |-- GET /tasks/abc ----------->|                               |
  |<-- { status: "completed",    |                               |
  |       result: { ... } } -----|                               |
  |                              |                               |
  |   (停止轮询，展示结果)        |                               |
```

### 进度映射

| 步骤 | progress_pct | 页面显示 |
|------|-------------|---------|
| 初始化 | 0% | 正在初始化... |
| jd_parser | 10% | 正在解析职位描述... |
| profile_loader | 25% | 正在加载个人档案... |
| skill_matcher | 40% | 正在匹配技能... |
| gap_analyzer | 55% | 正在进行差距分析... |
| resume_generator | 75% | 正在生成简历内容... |
| markdown_exporter | 90% | 正在导出 Markdown... |
| 完成 | 100% | 简历生成完成 |

### 关键代码结构

**任务模型** - `src/iresume/models/task.py`
- `TaskStatus` 枚举：pending / running / completed / failed
- `GenerationTask`：id、状态、进度文本、百分比、结果、错误信息

**任务管理器** - `src/iresume/services/task_manager.py`
- 基于 `asyncio.Lock` 的线程安全内存存储
- 支持并发创建/读取/更新任务

**后台执行器** - `src/iresume/services/resume_runner.py`
- 按序调用 6 个节点函数（绕过 LangGraph `graph.invoke()` 以获取中间进度）
- 每个节点通过 `asyncio.to_thread()` 异步执行，不阻塞事件循环
- 异常捕获后标记任务为 failed

**API 路由** - `src/iresume/api/routes/resume.py`
- `POST /generate` → 创建任务 + 启动后台执行 + 返回 task_id
- `GET /tasks/{task_id}` → 返回当前任务状态

**前端** - `frontend/src/views/ResumeView.vue`
- 创建任务后每 2s 轮询一次（使用 `setTimeout` 而非 `setInterval`，避免请求堆积）
- 进度条显示当前进度百分比 + 中文描述
- 完成后自动展示简历和匹配分析
- 失败时显示错误信息
- `onUnmounted` 生命周期钩子清理定时器

### 边界情况处理

| 场景 | 处理方式 |
|------|---------|
| 服务重启 | 内存任务丢失，GET 返回 404，前端提示"服务已重启，请重新生成" |
| LLM 调用失败 | 异常捕获，任务标记为 failed，携带错误信息 |
| not_viable | 正常完成，result 包含 gap_report，前端展示匹配度过低提示 |
| 快速连点两次 | 只追踪最新 taskId，旧轮询通过 clearTimeout 停止 |
| 中途离开页面 | onUnmounted 清理定时器，后台任务继续执行（允许重复提交） |

---

## 优化效果对比

| 指标 | 优化前 | 优化后 |
|------|--------|--------|
| 首次响应时间 | 60-120s | < 500ms（立即返回 task_id） |
| 用户反馈 | 无，页面看起来卡死 | 实时进度条 + 文字描述 |
| 错误恢复 | 超时后全量重试 | 看到错误后重新提交 |
| 连接可靠性 | 依赖长连接稳定性 | 短连接轮询，连接失败可重建 |
| 并发请求 | 阻塞 worker 线程 | `asyncio.to_thread` + 事件循环不受影响 |

---

## 后续可能的优化

1. **合并分析节点**：将 skill_matcher + gap_analyzer 合并为一次 LLM 调用，减少串行节点数
2. **分模型策略**：分析节点使用 `deepseek-chat`（更快），生成节点使用 `deepseek-v4-pro`（质量更高）
3. **持久化任务**：改用 SQLite/Redis 存储任务状态，支持服务重启后恢复进度
4. **WebSocket 推送**：替代轮询，服务端主动推送进度变化（更低延迟，更少请求）
