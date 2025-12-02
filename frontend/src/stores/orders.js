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

export const useOrdersStore = defineStore('orders', {
  state: () => ({
    orders: [],
    currentOrder: null,
    loading: false,
    error: null
  }),
  
  getters: {
    pendingOrders: (state) => state.orders.filter(o => o.status === 'PENDING'),
    completedOrders: (state) => state.orders.filter(o => o.status === 'DELIVERED'),
    orderCount: (state) => state.orders.length
  },
  
  actions: {
    async fetchOrders() {
      const authStore = useAuthStore()
      if (!authStore.isAuthenticated) {
        this.orders = []
        return
      }
      
      this.loading = true
      this.error = null
      try {
        const response = await apiClient.get('/orders/')
        
        if (Array.isArray(response.data)) {
          this.orders = response.data
        } else if (response.data.results) {
          this.orders = response.data.results
        }
      } catch (error) {
        this.error = 'Failed to load orders'
        this.orders = []
      } finally {
        this.loading = false
      }
    },
    
    async fetchOrderById(id) {
      this.loading = true
      this.error = null
      try {
        const response = await apiClient.get(`/orders/${id}/`)
        this.currentOrder = response.data
        return response.data
      } catch (error) {
        this.error = 'Failed to load order details'
        this.currentOrder = null
        return null
      } finally {
        this.loading = false
      }
    },
    
    async createOrder(orderData) {
      const authStore = useAuthStore()
      if (!authStore.isAuthenticated) {
        throw new Error('Please login to place an order')
      }
      
      this.loading = true
      this.error = null
      try {
        const response = await apiClient.post('/orders/', orderData)
        
        // Add new order to list
        this.orders.unshift(response.data)
        
        return response.data
      } catch (error) {
        this.error = error.response?.data?.detail || 
                     error.response?.data?.error ||
                     (typeof error.response?.data === 'string' ? error.response?.data : null) ||
                     'Failed to create order'
        throw new Error(this.error)
      } finally {
        this.loading = false
      }
    },
    
    async cancelOrder(id) {
      this.loading = true
      this.error = null
      try {
        const response = await apiClient.post(`/orders/${id}/cancel/`)
        
        // Update order in list
        const index = this.orders.findIndex(o => o.id === id)
        if (index !== -1) {
          this.orders[index] = response.data
        }
        
        // Update current order if viewing
        if (this.currentOrder?.id === id) {
          this.currentOrder = response.data
        }
        
        return response.data
      } catch (error) {
        this.error = error.response?.data?.error || 'Failed to cancel order'
        throw new Error(this.error)
      } finally {
        this.loading = false
      }
    }
  }
})
