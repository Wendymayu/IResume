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
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { marked } from 'marked'
import { generateResume, downloadResume } from '../api'

const jdText = ref('')
const generating = ref(false)
const error = ref('')
const gapReport = ref<any>(null)
const resumeMarkdown = ref('')
const resumeId = ref('')

const renderedResume = computed(() => marked(resumeMarkdown.value))
const downloadUrl = computed(() => resumeId.value ? downloadResume(resumeId.value) : '')

async function generate() {
  generating.value = true
  error.value = ''
  gapReport.value = null
  resumeMarkdown.value = ''
  resumeId.value = ''

  try {
    console.log('[ResumeView] 开始生成简历，JD长度:', jdText.value.length)
    const { data } = await generateResume(jdText.value)
    console.log('[ResumeView] 生成成功，响应数据:', data)
    gapReport.value = data.gap_report
    resumeMarkdown.value = data.resume_markdown || ''
    resumeId.value = data.resume_id || ''
    console.log('[ResumeView] 简历ID:', resumeId.value)
  } catch (e: any) {
    console.error('[ResumeView] 生成失败，错误:', e)
    if (e.response?.data?.detail) {
      const detail = e.response.data.detail
      if (typeof detail === 'object' && detail.message) {
        error.value = detail.message
        gapReport.value = detail.gap_report
      } else {
        error.value = String(detail)
      }
    } else if (e.message) {
      error.value = `请求失败: ${e.message}`
    } else {
      error.value = '生成失败，请稍后重试'
    }
    console.error('[ResumeView] 最终错误信息:', error.value)
  } finally {
    generating.value = false
  }
}
</script>
