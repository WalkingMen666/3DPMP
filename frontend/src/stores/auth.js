import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE_URL = '/api/auth'

// Default blank avatar (simple gray silhouette)
const DEFAULT_AVATAR = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%239CA3AF"%3E%3Cpath d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/%3E%3C/svg%3E'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user')) || null,
    token: localStorage.getItem('token') || null,
    isAuthenticated: !!localStorage.getItem('token'),
    avatarChoices: [],
  }),
  
  getters: {
    // Get user avatar, defaulting to blank avatar
    userAvatar: (state) => {
      if (!state.user) return DEFAULT_AVATAR
      if (state.user.avatar_url) return state.user.avatar_url
      if (state.user.avatar_type && state.user.avatar_type !== 'default') {
        // Custom preset avatars would go here
        return DEFAULT_AVATAR
      }
      return DEFAULT_AVATAR
    }
  },
  
  actions: {
    async login(email, password) {
      try {
        const response = await axios.post(`${API_BASE_URL}/login/`, {
          email,
          password
        })
        
        const { key, user } = response.data
        
        this.token = key
        this.user = {
          id: user?.pk || user?.id || '1',
          email: user?.email || email,
          name: user?.first_name || user?.username || email.split('@')[0],
          role: 'customer',
          avatar_type: user?.avatar_type || 'default',
          avatar_url: user?.avatar_url || null,
          avatar: user?.avatar_url || DEFAULT_AVATAR
        }
        this.isAuthenticated = true
        
        localStorage.setItem('token', key)
        localStorage.setItem('user', JSON.stringify(this.user))
        
        // Fetch full user details including avatar and role
        await this.fetchCurrentUser()
        
        // Merge and fetch cart after login
        const { useCartStore } = await import('./cart')
        const cartStore = useCartStore()
        await cartStore.mergeLocalCartToServer()
        await cartStore.fetchCart()
        
        return true
      } catch (error) {
        throw new Error(error.response?.data?.non_field_errors?.[0] || 'Unable to log in with provided credentials.')
      }
    },
    
    async googleLogin(idToken) {
      try {
        const response = await axios.post(`${API_BASE_URL}/google/`, {
          id_token: idToken
        })
        
        const { key, user } = response.data
        
        this.token = key
        this.user = {
          id: user.id,
          email: user.email,
          name: user.email.split('@')[0],
          role: user.role || 'customer',
          is_employee: user.is_employee || false,
          is_admin: user.is_admin || false,
          auth_provider: user.auth_provider || 'google',
          avatar_type: user.avatar_type || 'default',
          avatar_url: user.avatar_url || null,
          avatar: user.avatar_url || DEFAULT_AVATAR
        }
        this.isAuthenticated = true
        
        localStorage.setItem('token', key)
        localStorage.setItem('user', JSON.stringify(this.user))
        
        // Merge and fetch cart after login
        const { useCartStore } = await import('./cart')
        const cartStore = useCartStore()
        await cartStore.mergeLocalCartToServer()
        await cartStore.fetchCart()
        
        return true
      } catch (error) {
        throw new Error(error.response?.data?.error || 'Google sign-in failed')
      }
    },
    
    async register(email, password1, password2) {
      try {
        const response = await axios.post(`${API_BASE_URL}/registration/`, {
          email,
          password1,
          password2
        })
        
        // After successful registration, login automatically
        await this.login(email, password1)
        return true
      } catch (error) {
        const errorData = error.response?.data
        let errorMessage = 'Registration failed'
        
        if (errorData) {
          if (errorData.email) {
            errorMessage = errorData.email[0]
          } else if (errorData.password1) {
            errorMessage = errorData.password1[0]
          } else if (errorData.password2) {
            errorMessage = errorData.password2[0]
          } else if (errorData.non_field_errors) {
            errorMessage = errorData.non_field_errors[0]
          }
        }
        
        throw new Error(errorMessage)
      }
    },
    
    async fetchCurrentUser() {
      if (!this.token) return null
      
      try {
        const response = await axios.get(`${API_BASE_URL}/me/`, {
          headers: { Authorization: `Token ${this.token}` }
        })
        
        const userData = response.data
        // Ensure avatar_url is a full URL (prepend backend URL if relative)
        let avatarUrl = userData.avatar_url
        if (avatarUrl && !avatarUrl.startsWith('http') && !avatarUrl.startsWith('data:')) {
          // In development, prepend the backend URL
          avatarUrl = `http://localhost:8000${avatarUrl.startsWith('/') ? '' : '/'}${avatarUrl}`
        }
        
        this.user = {
          ...this.user,
          id: userData.id,
          email: userData.email,
          name: userData.display_name || userData.email?.split('@')[0] || 'User',
          display_name: userData.display_name || '',
          avatar_type: userData.avatar_type,
          avatar_url: avatarUrl,
          avatar: avatarUrl || DEFAULT_AVATAR,
          role: userData.role || 'customer',
          is_employee: userData.is_employee || false,
          is_admin: userData.is_admin || false
        }
        
        localStorage.setItem('user', JSON.stringify(this.user))
        return this.user
      } catch (error) {
        console.error('Failed to fetch current user:', error)
        return null
      }
    },
    
    async fetchAvatarChoices() {
      if (!this.token) return []
      
      try {
        const response = await axios.get(`${API_BASE_URL}/avatar/choices/`, {
          headers: { Authorization: `Token ${this.token}` }
        })
        this.avatarChoices = response.data
        return this.avatarChoices
      } catch (error) {
        console.error('Failed to fetch avatar choices:', error)
        return []
      }
    },
    
    async updateAvatar(avatarType, avatarImage = null) {
      if (!this.token) return false
      
      try {
        const formData = new FormData()
        formData.append('avatar_type', avatarType)
        
        if (avatarImage) {
          formData.append('avatar_image', avatarImage)
        }
        
        const response = await axios.patch(`${API_BASE_URL}/avatar/`, formData, {
          headers: { 
            Authorization: `Token ${this.token}`,
            'Content-Type': 'multipart/form-data'
          }
        })
        
        const userData = response.data
        this.user = {
          ...this.user,
          avatar_type: userData.avatar_type,
          avatar_url: userData.avatar_url,
          avatar: userData.avatar_url || DEFAULT_AVATAR
        }
        
        localStorage.setItem('user', JSON.stringify(this.user))
        return true
      } catch (error) {
        console.error('Failed to update avatar:', error)
        throw new Error(error.response?.data?.detail || 'Failed to update avatar')
      }
    },
    
    async updateProfile(displayName) {
      if (!this.token) return false
      
      try {
        const response = await axios.patch(`${API_BASE_URL}/profile/`, {
          display_name: displayName
        }, {
          headers: { 
            Authorization: `Token ${this.token}`,
            'Content-Type': 'application/json'
          }
        })
        
        const userData = response.data
        this.user = {
          ...this.user,
          name: userData.display_name || this.user.email?.split('@')[0],
          display_name: userData.display_name
        }
        
        localStorage.setItem('user', JSON.stringify(this.user))
        return true
      } catch (error) {
        console.error('Failed to update profile:', error)
        throw new Error(error.response?.data?.detail || 'Failed to update profile')
      }
    },
    
    async logout() {
      this.token = null
      this.user = null
      this.isAuthenticated = false
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      
      // Clear cart on logout
      const { useCartStore } = await import('./cart')
      const cartStore = useCartStore()
      cartStore.items = []
    }
  }
})
