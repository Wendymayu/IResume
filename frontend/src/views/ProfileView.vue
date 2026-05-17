<template>
  <div>
    <h2 class="text-2xl font-bold mb-6">个人档案</h2>

    <div class="space-y-6">
      <!-- Tabs -->
      <div class="flex gap-2 flex-wrap">
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

      <!-- Personal Info Form -->
      <div v-if="activeTab === 'personal'" class="max-w-2xl bg-white border rounded-lg p-6">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">姓名</label>
            <input
              v-model="personalInfo.name"
              class="w-full p-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="请输入姓名"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">年龄</label>
            <input
              v-model.number="personalInfo.age"
              type="number"
              class="w-full p-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="请输入年龄"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">邮箱</label>
            <input
              v-model="personalInfo.email"
              type="email"
              class="w-full p-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="请输入邮箱"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">电话</label>
            <input
              v-model="personalInfo.phone"
              class="w-full p-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="请输入电话"
            />
          </div>
          <div class="md:col-span-2">
            <label class="block text-sm font-medium text-gray-700 mb-1">期望职位</label>
            <input
              v-model="personalInfo.desired_position"
              class="w-full p-2 border rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              placeholder="请输入期望职位"
            />
          </div>
        </div>
      </div>

      <!-- Markdown Editor (non-personal tabs) -->
      <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-4">
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
import { ref, reactive, computed, onMounted } from 'vue'
import { marked } from 'marked'
import { getProfile, updatePersonalInfo, updateEducation, updateExperience, updateSkills } from '../api'

const tabs = [
  { key: 'personal', label: '个人信息' },
  { key: 'education', label: '教育经历' },
  { key: 'experience', label: '工作经历' },
  { key: 'skills', label: '技能' },
]

const activeTab = ref('personal')
const education = ref('')
const experience = ref('')
const skills = ref('')
const saving = ref(false)
const personalInfo = reactive({
  name: '',
  age: null as number | null,
  email: '',
  phone: '',
  desired_position: '',
})

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
    if (data.personal_info) {
      personalInfo.name = data.personal_info.name || ''
      personalInfo.age = data.personal_info.age ?? null
      personalInfo.email = data.personal_info.email || ''
      personalInfo.phone = data.personal_info.phone || ''
      personalInfo.desired_position = data.personal_info.desired_position || ''
    }
  } catch (e) {
    console.error('Failed to load profile', e)
  }
}

async function save() {
  saving.value = true
  try {
    if (activeTab.value === 'personal') {
      await updatePersonalInfo({
        name: personalInfo.name,
        age: personalInfo.age,
        email: personalInfo.email,
        phone: personalInfo.phone,
        desired_position: personalInfo.desired_position,
      })
    } else {
      await updateEducation(education.value)
      await updateExperience(experience.value)
      await updateSkills(skills.value)
    }
  } catch (e) {
    console.error('Failed to save profile', e)
  } finally {
    saving.value = false
  }
}

onMounted(loadProfile)
</script>
