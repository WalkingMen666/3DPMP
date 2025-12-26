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

export const useCartStore = defineStore('cart', {
  state: () => ({
    items: [],
    loading: false,
    error: null
  }),
  
  getters: {
    itemCount: (state) => state.items.reduce((sum, item) => sum + item.quantity, 0),
    subtotal: (state) => state.items.reduce((sum, item) => {
      const price = parseFloat(item.unit_price) || parseFloat(item.price) || 0
      return sum + (price * item.quantity)
    }, 0),
    total: (state) => {
      const subtotal = state.items.reduce((sum, item) => {
        const price = parseFloat(item.unit_price) || parseFloat(item.price) || 0
        return sum + (price * item.quantity)
      }, 0)
      return subtotal > 0 ? subtotal + 10 : 0 // $10 shipping if cart has items
    }
  },
  
  actions: {
    async fetchCart() {
      const authStore = useAuthStore()
      if (!authStore.isAuthenticated) {
        this.items = []
        return
      }

      this.loading = true
      this.error = null
      try {
        const response = await apiClient.get('/cart/')
        this.items = response.data.map(item => ({
          id: item.id,
          modelId: item.model,
          name: item.model_name,
          materialId: item.material,
          material: item.material_name,
          quantity: item.quantity,
          // Use estimated_price which is calculated from weight_g * price_per_g * quantity
          // Don't fall back to material_price as that's price per gram, not unit price
          price: item.estimated_price ? parseFloat(item.estimated_price) / item.quantity : 0,
          unit_price: item.estimated_price ? parseFloat(item.estimated_price) / item.quantity : 0,
          subtotal: parseFloat(item.estimated_price) || 0,
          image: item.model_thumbnail || '/placeholder-model.png',
          notes: item.notes,
          // Flag to show if price is unavailable (no slicing info)
          priceUnavailable: !item.estimated_price
        }))
      } catch (error) {
        if (error.response?.status !== 401) {
          this.error = 'Failed to load cart'
        }
        // If not authenticated, use local fallback
        this.items = []
      } finally {
        this.loading = false
      }
    },
    
    async addItem(model, quantity = 1, materialId = null) {
      const authStore = useAuthStore()
      if (!authStore.isAuthenticated) {
        // For unauthenticated users, use local storage fallback
        this.addItemLocal(model, quantity, materialId)
        return
      }

      this.loading = true
      this.error = null
      try {
        // Use standard REST endpoint to create cart item
        await apiClient.post('/cart/', {
          model: model.id,
          material: materialId,
          quantity: quantity
        })
        // Refresh cart after adding
        await this.fetchCart()
      } catch (error) {
        this.error = error.response?.data?.error || error.response?.data?.detail || 'Failed to add item to cart'
        throw new Error(this.error)
      } finally {
        this.loading = false
      }
    },
    
    addItemLocal(model, quantity = 1, material = 'PLA') {
      // Fallback for unauthenticated users - local storage
      const existingItem = this.items.find(item => item.modelId === model.id && item.material === material)
      
      if (existingItem) {
        existingItem.quantity += quantity
      } else {
        this.items.push({
          id: `local-${Date.now()}`,
          modelId: model.id,
          name: model.name || model.model_name,
          price: parseFloat(model.price) || 0,
          quantity,
          material,
          image: model.image || model.thumbnail
        })
      }
      this.saveToLocalStorage()
    },
    
    async removeItem(id) {
      const authStore = useAuthStore()
      if (!authStore.isAuthenticated || String(id).startsWith('local-')) {
        // Local storage removal
        this.items = this.items.filter(item => item.id !== id)
        this.saveToLocalStorage()
        return
      }

      this.loading = true
      this.error = null
      try {
        await apiClient.delete(`/cart/${id}/`)
        await this.fetchCart()
      } catch (error) {
        this.error = 'Failed to remove item'
      } finally {
        this.loading = false
      }
    },
    
    async updateQuantity(id, quantity) {
      const authStore = useAuthStore()
      if (!authStore.isAuthenticated || String(id).startsWith('local-')) {
        // Local storage update
        const item = this.items.find(item => item.id === id)
        if (item) {
          if (quantity <= 0) {
            this.items = this.items.filter(i => i.id !== id)
          } else {
            item.quantity = quantity
          }
          this.saveToLocalStorage()
        }
        return
      }

      this.loading = true
      this.error = null
      try {
        if (quantity <= 0) {
          // Remove item if quantity is 0 or less
          await apiClient.delete(`/cart/${id}/`)
        } else {
          // Use PATCH to update quantity
          await apiClient.patch(`/cart/${id}/`, { quantity })
        }
        await this.fetchCart()
      } catch (error) {
        this.error = 'Failed to update quantity'
      } finally {
        this.loading = false
      }
    },
    
    async clearCart() {
      const authStore = useAuthStore()
      if (!authStore.isAuthenticated) {
        this.items = []
        this.saveToLocalStorage()
        return
      }

      this.loading = true
      this.error = null
      try {
        // Delete all items one by one (or implement a clear endpoint)
        for (const item of this.items) {
          if (!String(item.id).startsWith('local-')) {
            await apiClient.delete(`/cart/${item.id}/`)
          }
        }
        this.items = []
      } catch (error) {
        this.error = 'Failed to clear cart'
      } finally {
        this.loading = false
      }
    },
    
    saveToLocalStorage() {
      localStorage.setItem('cart', JSON.stringify(this.items))
    },
    
    loadFromLocalStorage() {
      const savedCart = localStorage.getItem('cart')
      if (savedCart) {
        this.items = JSON.parse(savedCart)
      }
    },
    
    // Merge local cart to server cart after login
    async mergeLocalCartToServer() {
      const localCart = JSON.parse(localStorage.getItem('cart') || '[]')
      if (localCart.length > 0) {
        for (const item of localCart) {
          try {
            await apiClient.post('/cart/add_to_cart/', {
              model_id: item.modelId || item.id,
              material_id: item.materialId,
              quantity: item.quantity
            })
          } catch (error) {
            // Skip items that fail to add
          }
        }
        // Clear local storage after merge
        localStorage.removeItem('cart')
        // Refresh cart from server
        await this.fetchCart()
      }
    }
  }
})
