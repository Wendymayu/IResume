import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

// Profile
export const getProfile = () => api.get('/profile')
export const updateEducation = (content: string) => api.put('/profile/education', { content })
export const updateExperience = (content: string) => api.put('/profile/experience', { content })
export const updateSkills = (content: string) => api.put('/profile/skills', { content })

// Resume
export const generateResume = (jdText: string) => api.post('/resume/generate', { jd_text: jdText })
export const getResume = (resumeId: string) => api.get(`/resume/${resumeId}`)
export const downloadResume = (resumeId: string) => `/api/resume/${resumeId}/download`

export default api
