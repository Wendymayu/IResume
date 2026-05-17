<template>
  <div>
    <h2 class="text-2xl font-bold mb-6">生成简历</h2>

    <!-- JD Input -->
    <div class="mb-6">
      <label class="block text-sm font-medium text-gray-700 mb-2">粘贴岗位描述 (JD)</label>
      <textarea
        v-model="jdText"
        class="w-full h-48 p-3 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
        placeholder="请粘贴目标岗位的职位描述..."
      />
    </div>

    <!-- Generate button -->
    <div class="mb-6">
      <button
        @click="generate"
        :disabled="generating || !jdText.trim()"
        class="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
      >
        {{ generating ? '生成中...' : '生成简历' }}
      </button>
    </div>

    <!-- Progress bar -->
    <div v-if="generating" class="mb-6 p-4 bg-white border rounded-lg">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm text-gray-600">{{ progress }}</span>
        <span class="text-sm font-medium text-indigo-600">{{ progressPct }}%</span>
      </div>
      <div class="w-full bg-gray-200 rounded-full h-2">
        <div
          class="bg-indigo-600 h-2 rounded-full transition-all duration-500"
          :style="{ width: progressPct + '%' }"
        />
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
      {{ error }}
    </div>

    <!-- Gap Report -->
    <div v-if="gapReport" class="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
      <h3 class="font-medium text-blue-800 mb-2">匹配分析</h3>
      <p class="text-sm text-blue-700">
        匹配度: {{ (gapReport.viability_score * 100).toFixed(0) }}%
        <span v-if="gapReport.recommendation === 'proceed'" class="text-green-600">- 推荐投递</span>
        <span v-else-if="gapReport.recommendation === 'proceed_with_caveats'" class="text-yellow-600">- 可以尝试</span>
        <span v-else-if="gapReport.recommendation === 'not_viable'" class="text-red-600">- 不建议投递</span>
      </p>
      <div v-if="gapReport.missing_skills?.length" class="mt-2">
        <span class="text-sm text-red-600">缺失技能: {{ gapReport.missing_skills.join('、') }}</span>
      </div>
      <div v-if="gapReport.weak_skills?.length" class="mt-1">
        <span class="text-sm text-yellow-600">薄弱技能: {{ gapReport.weak_skills.join('、') }}</span>
      </div>
    </div>

    <!-- Resume Preview -->
    <div v-if="resumeMarkdown" class="mb-6">
      <div class="flex items-center justify-between mb-2">
        <h3 class="font-medium text-gray-800">简历预览</h3>
        <a
          v-if="resumeId"
          :href="downloadUrl"
          class="text-sm text-indigo-600 hover:underline"
          download
        >
          下载 Markdown
        </a>
      </div>
      <div
        class="p-6 bg-white border rounded-lg prose prose-sm max-w-none"
        v-html="renderedResume"
      />
    </div>

    <!-- History -->
    <div class="mt-10">
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-bold text-gray-800">历史记录</h3>
        <button
          @click="loadHistory"
          class="text-sm text-indigo-600 hover:underline"
        >
          刷新
        </button>
      </div>

      <div v-if="historyLoading" class="text-sm text-gray-500 py-4">加载中...</div>

      <div v-else-if="historyRecords.length === 0" class="text-sm text-gray-500 py-4 bg-gray-50 border rounded-lg p-6 text-center">
        暂无生成记录
      </div>

      <div v-else class="space-y-3">
        <div
          v-for="record in historyRecords"
          :key="record.task_id"
          class="p-4 bg-white border rounded-lg hover:shadow-sm transition-shadow"
        >
          <div class="flex items-start justify-between mb-2">
            <div class="flex-1 min-w-0 mr-4">
              <p class="text-sm text-gray-800 font-medium truncate" :title="record.jd_text">
                {{ record.jd_text.slice(0, 120) }}{{ record.jd_text.length > 120 ? '...' : '' }}
              </p>
            </div>
            <span
              class="shrink-0 px-2 py-0.5 text-xs rounded-full font-medium"
              :class="statusClass(record.status)"
            >
              {{ statusLabel(record.status) }}
            </span>
          </div>

          <div class="flex items-center gap-4 text-xs text-gray-500 mb-2">
            <span>{{ formatDate(record.created_at) }}</span>
            <span v-if="record.elapsed_ms != null">耗时 {{ formatElapsed(record.elapsed_ms) }}</span>
          </div>

          <div class="flex items-center gap-3">
            <a
              v-if="record.resume_id && record.file_exists"
              :href="`/api/resume/${record.resume_id}/download`"
              class="text-xs text-indigo-600 hover:underline"
              download
            >
              下载简历
            </a>
            <span v-else-if="record.status === 'not_viable'" class="text-xs text-gray-400">
              未生成简历
            </span>
            <span v-else-if="record.status === 'failed'" class="text-xs text-gray-400">
              {{ record.error || '生成失败' }}
            </span>
            <button
              @click="deleteRecord(record.task_id)"
              class="text-xs text-red-400 hover:text-red-600 ml-auto"
            >
              删除
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { marked } from 'marked'
import {
  generateResumeTask,
  getTaskStatus,
  downloadResume,
  getHistoryList,
  deleteHistoryRecord,
} from '../api'

const jdText = ref('')
const generating = ref(false)
const error = ref('')
const gapReport = ref<any>(null)
const resumeMarkdown = ref('')
const resumeId = ref('')

// Polling state
const taskId = ref('')
const progress = ref('')
const progressPct = ref(0)
let pollTimer: ReturnType<typeof setTimeout> | null = null

// History state
const historyRecords = ref<any[]>([])
const historyLoading = ref(false)

const renderedResume = computed(() => marked(resumeMarkdown.value))
const downloadUrl = computed(() => resumeId.value ? downloadResume(resumeId.value) : '')

function stopPolling() {
  if (pollTimer !== null) {
    clearTimeout(pollTimer)
    pollTimer = null
  }
}

async function pollTask() {
  if (!taskId.value) return
  try {
    const { data } = await getTaskStatus(taskId.value)
    progress.value = data.progress
    progressPct.value = data.progress_pct

    if (data.status === 'completed') {
      stopPolling()
      generating.value = false
      const result = data.result || {}
      gapReport.value = result.gap_report || null
      resumeMarkdown.value = result.resume_markdown || ''
      resumeId.value = result.resume_id || ''
      console.log('[ResumeView] 任务完成，简历ID:', resumeId.value)
      await loadHistory()
    } else if (data.status === 'failed') {
      stopPolling()
      generating.value = false
      error.value = data.error || '生成失败，请稍后重试'
      console.error('[ResumeView] 任务失败:', data.error)
      await loadHistory()
    } else {
      // Still running — poll again after 2s
      pollTimer = setTimeout(pollTask, 2000)
    }
  } catch (e: any) {
    stopPolling()
    generating.value = false
    if (e.response?.status === 404) {
      error.value = '服务已重启，请重新生成'
    } else if (e.message) {
      error.value = `查询任务状态失败: ${e.message}`
    } else {
      error.value = '查询任务状态失败'
    }
    console.error('[ResumeView] 轮询异常:', e)
  }
}

async function generate() {
  generating.value = true
  error.value = ''
  gapReport.value = null
  resumeMarkdown.value = ''
  resumeId.value = ''
  progress.value = '正在创建任务...'
  progressPct.value = 0

  try {
    console.log('[ResumeView] 开始生成简历，JD长度:', jdText.value.length)
    const { data } = await generateResumeTask(jdText.value)
    taskId.value = data.task_id
    console.log('[ResumeView] 任务已创建，taskId:', taskId.value)
    await pollTask()
  } catch (e: any) {
    generating.value = false
    console.error('[ResumeView] 创建任务失败:', e)
    if (e.response?.data?.detail) {
      error.value = String(e.response.data.detail)
    } else if (e.message) {
      error.value = `请求失败: ${e.message}`
    } else {
      error.value = '创建任务失败，请稍后重试'
    }
  }
}

async function loadHistory() {
  historyLoading.value = true
  try {
    const { data } = await getHistoryList()
    historyRecords.value = data.records
  } catch (e: any) {
    console.error('[ResumeView] 加载历史记录失败:', e)
  } finally {
    historyLoading.value = false
  }
}

async function deleteRecord(taskId: string) {
  try {
    await deleteHistoryRecord(taskId)
    historyRecords.value = historyRecords.value.filter((r: any) => r.task_id !== taskId)
  } catch (e: any) {
    console.error('[ResumeView] 删除记录失败:', e)
  }
}

function statusClass(status: string): string {
  switch (status) {
    case 'completed': return 'bg-green-100 text-green-700'
    case 'not_viable': return 'bg-yellow-100 text-yellow-700'
    case 'failed': return 'bg-red-100 text-red-700'
    default: return 'bg-gray-100 text-gray-700'
  }
}

function statusLabel(status: string): string {
  switch (status) {
    case 'completed': return '已完成'
    case 'not_viable': return '匹配度低'
    case 'failed': return '失败'
    default: return status
  }
}

function formatDate(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

function formatElapsed(ms: number): string {
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  const m = Math.floor(ms / 60000)
  const s = Math.round((ms % 60000) / 1000)
  return `${m}m${s}s`
}

onMounted(() => {
  loadHistory()
})

onUnmounted(() => {
  stopPolling()
})
</script>
