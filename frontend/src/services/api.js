import axios from 'axios';

// In production, VITE_API_URL points to the deployed Render backend.
// Locally, it falls back to '/api' which Vite proxies to localhost:5000.
const BASE_URL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api';

const API = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const authAPI = {
  getProfile: async () => {
    const response = await API.get('/auth/profile');
    return response.data;
  },
  updateProfile: async (data) => {
    const response = await API.post('/auth/profile', data);
    return response.data;
  },
};

export const resumeAPI = {
  uploadResume: async (formData) => {
    const response = await API.post('/resume/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  getLatest: async () => {
    const response = await API.get('/resume/latest');
    return response.data;
  },
  seedDemo: async (profileType) => {
    const response = await API.post('/resume/demo-seed', { profile_type: profileType });
    return response.data;
  },
};

export const roadmapAPI = {
  getGoals: async () => {
    const response = await API.get('/roadmap/goals');
    return response.data;
  },
  generate: async (goalTitle) => {
    const response = await API.post('/roadmap/generate', { goal_title: goalTitle });
    return response.data;
  },
  getActive: async () => {
    const response = await API.get('/roadmap/active');
    return response.data;
  },
};

export const quizAPI = {
  generate: async (skillName) => {
    const response = await API.post('/quiz/generate', { skill_name: skillName });
    return response.data;
  },
  submit: async (quizId, answers) => {
    const response = await API.post('/quiz/submit', { quiz_id: quizId, answers });
    return response.data;
  },
  getHistory: async () => {
    const response = await API.get('/quiz/history');
    return response.data;
  },
};

export const progressAPI = {
  getLesson: async (roadmapId, stepKey, stepTitle, topics) => {
    const response = await API.post('/progress/lesson', {
      roadmap_id: roadmapId,
      step_key: stepKey,
      step_title: stepTitle,
      topics,
    });
    return response.data;
  },
  toggleStep: async (roadmapId, stepKey, completed) => {
    const response = await API.post('/progress/toggle', {
      roadmap_id: roadmapId,
      step_key: stepKey,
      completed,
    });
    return response.data;
  },
  getStats: async () => {
    const response = await API.get('/progress/stats');
    return response.data;
  },
};

export default API;
