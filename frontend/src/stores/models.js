import { defineStore } from 'pinia'
import axios from 'axios'
import { useAuthStore } from './auth'

const API_BASE_URL = '/api'

// Create axios instance with auth interceptor
const apiClient = axios.create({
  baseURL: API_BASE_URL
})

apiClient.interceptors.request.use(config => {
  const authStore = useAuthStore()
  if (authStore.token) {
    config.headers.Authorization = `Token ${authStore.token}`
  }
  return config
})

export const useModelsStore = defineStore('models', {
  state: () => ({
    publicModels: [],
    myModels: [],
    currentModel: null,
    loading: false,
    error: null,
    pagination: {
      count: 0,
      next: null,
      previous: null
    }
  }),
  
  getters: {
    featuredModels: (state) => state.publicModels.filter(m => m.is_featured).slice(0, 6),
    recentModels: (state) => [...state.publicModels].sort((a, b) => 
      new Date(b.created_at) - new Date(a.created_at)
    ).slice(0, 8)
  },
  
  actions: {
    async fetchPublicModels(params = {}) {
      this.loading = true
      this.error = null
      try {
        const response = await axios.get(`${API_BASE_URL}/public-models/`, { params })
        
        // Handle paginated response or array
        if (Array.isArray(response.data)) {
          this.publicModels = response.data
        } else if (response.data.results) {
          this.publicModels = response.data.results
          this.pagination = {
            count: response.data.count,
            next: response.data.next,
            previous: response.data.previous
          }
        }
      } catch (error) {
        this.error = 'Failed to load models'
        this.publicModels = []
      } finally {
        this.loading = false
      }
    },
    
    async fetchModelById(id) {
      this.loading = true
      this.error = null
      try {
        // Try public endpoint first
        const response = await axios.get(`${API_BASE_URL}/public-models/${id}/`)
        this.currentModel = response.data
        return response.data
      } catch (error) {
        // If not found in public, try authenticated endpoint for private models
        try {
          const response = await apiClient.get(`/models/${id}/`)
          this.currentModel = response.data
          return response.data
        } catch (err) {
          this.error = 'Failed to load model details'
          this.currentModel = null
          return null
        }
      } finally {
        this.loading = false
      }
    },
    
    async fetchMyModels() {
      const authStore = useAuthStore()
      if (!authStore.isAuthenticated) {
        this.myModels = []
        return
      }
      
      this.loading = true
      this.error = null
      try {
        const response = await apiClient.get('/models/my_models/')
        
        if (Array.isArray(response.data)) {
          this.myModels = response.data
        } else if (response.data.results) {
          this.myModels = response.data.results
        }
      } catch (error) {
        this.error = 'Failed to load your models'
        this.myModels = []
      } finally {
        this.loading = false
      }
    },
    
    async uploadModel(formData) {
      const authStore = useAuthStore()
      if (!authStore.isAuthenticated) {
        throw new Error('Please login to upload models')
      }
      
      this.loading = true
      this.error = null
      try {
        const response = await apiClient.post('/models/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        // Add to my models
        this.myModels.unshift(response.data)
        
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || 'Failed to upload model'
        throw new Error(this.error)
      } finally {
        this.loading = false
      }
    },
    
    async deleteModel(id) {
      this.loading = true
      this.error = null
      try {
        await apiClient.delete(`/models/${id}/`)
        this.myModels = this.myModels.filter(m => m.id !== id)
      } catch (error) {
        this.error = 'Failed to delete model'
        throw new Error(this.error)
      } finally {
        this.loading = false
      }
    },
    
    async updateModel(id, data) {
      this.loading = true
      this.error = null
      try {
        const response = await apiClient.patch(`/models/${id}/`, data)
        
        // Update in my models list
        const index = this.myModels.findIndex(m => m.id === id)
        if (index !== -1) {
          this.myModels[index] = response.data
        }
        
        // Update current model if viewing
        if (this.currentModel?.id === id) {
          this.currentModel = response.data
        }
        
        return response.data
      } catch (error) {
        this.error = 'Failed to update model'
        throw new Error(this.error)
      } finally {
        this.loading = false
      }
    },
    
    async uploadModelImages(modelId, formData) {
      try {
        const response = await apiClient.post(`/models/${modelId}/upload_images/`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        return response.data
      } catch (error) {
        console.error('Failed to upload images:', error)
        throw new Error('Failed to upload images')
      }
    },
    
    async submitForReview(modelId) {
      this.loading = true
      try {
        const response = await apiClient.post(`/models/${modelId}/submit_for_review/`)
        
        // Update in my models list
        const index = this.myModels.findIndex(m => m.id === modelId)
        if (index !== -1) {
          this.myModels[index] = response.data
        }
        
        return response.data
      } catch (error) {
        throw new Error(error.response?.data?.error || 'Failed to submit for review')
      } finally {
        this.loading = false
      }
    },
    
    async fetchReviewLogs(modelId) {
      try {
        const response = await apiClient.get(`/models/${modelId}/review_logs/`)
        return response.data
      } catch (error) {
        console.error('Failed to fetch review logs:', error)
        return []
      }
    }
  }
})
