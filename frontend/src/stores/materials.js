import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE_URL = '/api'

export const useMaterialsStore = defineStore('materials', {
  state: () => ({
    materials: [],
    loading: false,
    error: null
  }),
  
  getters: {
    activeMaterials: (state) => state.materials.filter(m => m.is_active),
    getMaterialById: (state) => (id) => state.materials.find(m => m.id === id)
  },
  
  actions: {
    async fetchMaterials() {
      this.loading = true
      this.error = null
      try {
        const response = await axios.get(`${API_BASE_URL}/materials/`)
        
        if (Array.isArray(response.data)) {
          this.materials = response.data
        } else if (response.data.results) {
          this.materials = response.data.results
        }
      } catch (error) {
        this.error = 'Failed to load materials'
        // Fallback to default materials for demo
        this.materials = [
          { id: '1', name: 'PLA', description: 'Standard PLA', price_twd_g: 0.05, is_active: true },
          { id: '2', name: 'PETG', description: 'PETG', price_twd_g: 0.07, is_active: true },
          { id: '3', name: 'ABS', description: 'ABS', price_twd_g: 0.06, is_active: true },
          { id: '4', name: 'TPU', description: 'Flexible TPU', price_twd_g: 0.10, is_active: true }
        ]
      } finally {
        this.loading = false
      }
    }
  }
})
