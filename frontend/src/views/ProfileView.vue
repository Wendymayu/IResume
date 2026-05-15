<template>
  <div>
    <h2 class="text-2xl font-bold mb-6">个人档案</h2>

    <div class="space-y-6">
      <!-- Tabs -->
      <div class="flex gap-2">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          @click="activeTab = tab.key"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition',
            activeTab === tab.key
              ? 'bg-indigo-600 text-white'
              : 'bg-white text-gray-600 hover:bg-gray-100'
          ]"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Editor -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Markdown 编辑</label>
          <textarea
            v-model="editContent"
            class="w-full h-96 p-3 border rounded-lg font-mono text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="在此输入 Markdown 内容..."
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">预览</label>
          <div
            class="w-full h-96 p-3 border rounded-lg overflow-auto prose prose-sm"
            v-html="renderedHtml"
          />
        </div>
      </div>

      <!-- Save button -->
      <div class="flex justify-end">
        <button
          @click="save"
          :disabled="saving"
          class="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
        >
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { marked } from 'marked'
import { getProfile, updateEducation, updateExperience, updateSkills } from '../api'

const tabs = [
  { key: 'education', label: '教育经历' },
  { key: 'experience', label: '工作经历' },
  { key: 'skills', label: '技能' },
]

const activeTab = ref('education')
const education = ref('')
const experience = ref('')
const skills = ref('')
const saving = ref(false)

const editContent = computed({
  get() {
    if (activeTab.value === 'education') return education.value
    if (activeTab.value === 'experience') return experience.value
    return skills.value
  },
  set(val: string) {
    if (activeTab.value === 'education') education.value = val
    else if (activeTab.value === 'experience') experience.value = val
    else skills.value = val
  },
})

const renderedHtml = computed(() => {
  return marked(editContent.value)
})

async function loadProfile() {
  try {
    const { data } = await getProfile()
    education.value = data.education || ''
    experience.value = data.experience || ''
    skills.value = data.skills || ''
  } catch (e) {
    console.error('Failed to load profile', e)
  }
}

async function save() {
  saving.value = true
  try {
    await updateEducation(education.value)
    await updateExperience(experience.value)
    await updateSkills(skills.value)
  } catch (e) {
    console.error('Failed to save profile', e)
  } finally {
    saving.value = false
  }
}

onMounted(loadProfile)
</script>
