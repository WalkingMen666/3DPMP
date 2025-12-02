<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()
const auth = useAuthStore()

// Check if user is employee/admin
onMounted(async () => {
  await auth.fetchCurrentUser()
  if (!auth.user?.is_employee) {
    router.push('/dashboard')
  }
})

const isAdmin = computed(() => auth.user?.is_admin)

// Tab state
const activeTab = ref('pending-models')

// Data states
const pendingModels = ref([])
const pendingOrders = ref([])
const materials = ref([])
const shippingOptions = ref([])
const employees = ref([])
const globalDiscounts = ref([])

const loading = ref(false)
const error = ref('')
const successMessage = ref('')

// API client with auth
const apiClient = axios.create({ baseURL: '/api' })
apiClient.interceptors.request.use(config => {
  if (auth.token) {
    config.headers.Authorization = `Token ${auth.token}`
  }
  return config
})

// Fetch data
const fetchPendingModels = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/models/pending_review/')
    pendingModels.value = response.data
  } catch (err) {
    error.value = 'Failed to load pending models'
  } finally {
    loading.value = false
  }
}

const fetchPendingOrders = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/orders/pending/')
    pendingOrders.value = response.data || []
  } catch (err) {
    // API might not exist yet
    pendingOrders.value = []
  } finally {
    loading.value = false
  }
}

const fetchMaterials = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/materials/')
    materials.value = response.data?.results || response.data || []
  } catch (err) {
    error.value = 'Failed to load materials'
  } finally {
    loading.value = false
  }
}

const fetchShippingOptions = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/shipping/options/')
    shippingOptions.value = response.data?.results || response.data || []
  } catch (err) {
    shippingOptions.value = []
  } finally {
    loading.value = false
  }
}

// Model review actions
const reviewingModel = ref(null)
const rejectReason = ref('')
const showRejectModal = ref(false)

const viewModelDetail = (modelId) => {
  router.push(`/models/${modelId}`)
}

const approveModel = async (modelId) => {
  try {
    await axios.post(`/api/models/${modelId}/approve/`, {}, {
      headers: { Authorization: `Token ${auth.token}` }
    })
    successMessage.value = 'Model approved successfully'
    pendingModels.value = pendingModels.value.filter(m => m.id !== modelId)
    setTimeout(() => successMessage.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to approve model'
  }
}

const openRejectModal = (model) => {
  reviewingModel.value = model
  rejectReason.value = ''
  showRejectModal.value = true
}

const rejectModel = async () => {
  if (!rejectReason.value.trim()) {
    error.value = 'Rejection reason is required'
    return
  }
  
  try {
    await axios.post(`/api/models/${reviewingModel.value.id}/reject/`, {
      reason: rejectReason.value
    }, {
      headers: { Authorization: `Token ${auth.token}` }
    })
    successMessage.value = 'Model rejected'
    pendingModels.value = pendingModels.value.filter(m => m.id !== reviewingModel.value.id)
    showRejectModal.value = false
    reviewingModel.value = null
    setTimeout(() => successMessage.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to reject model'
  }
}

// Order actions
const updateOrderStatus = async (orderId, newStatus) => {
  try {
    await apiClient.patch(`/orders/${orderId}/update_status/`, { status: newStatus })
    successMessage.value = `Order status updated to ${newStatus}`
    await fetchPendingOrders()
    setTimeout(() => successMessage.value = '', 3000)
  } catch (err) {
    error.value = 'Failed to update order status'
  }
}

// Tab change handler
const changeTab = (tab) => {
  activeTab.value = tab
  error.value = ''
  successMessage.value = ''
  
  if (tab === 'pending-models') fetchPendingModels()
  else if (tab === 'orders') fetchPendingOrders()
  else if (tab === 'materials' && isAdmin.value) fetchMaterials()
  else if (tab === 'shipping' && isAdmin.value) fetchShippingOptions()
}

// Initialize
onMounted(() => {
  fetchPendingModels()
})

// Employee tabs
const employeeTabs = [
  { id: 'pending-models', name: 'Pending Models', icon: 'M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z' },
  { id: 'orders', name: 'Orders', icon: 'M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z' },
]

// Admin-only tabs
const adminTabs = [
  { id: 'materials', name: 'Materials', icon: 'M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4' },
  { id: 'shipping', name: 'Shipping Options', icon: 'M8 17l4 4 4-4m-4-5v9M5 8l4-4 4 4M9 3v9' },
  { id: 'discounts', name: 'Discounts', icon: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z' },
  { id: 'employees', name: 'Employees', icon: 'M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' },
]

const allTabs = computed(() => {
  if (isAdmin.value) {
    return [...employeeTabs, ...adminTabs]
  }
  return employeeTabs
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <div class="flex flex-col md:flex-row gap-8">
      <!-- Sidebar -->
      <div class="w-full md:w-64 flex-shrink-0">
        <div class="bg-white dark:bg-dark-surface rounded-xl shadow-sm border border-gray-100 dark:border-gray-700/50 overflow-hidden">
          <div class="p-6 border-b border-gray-100 dark:border-gray-700">
            <div class="flex items-center space-x-3">
              <div class="w-12 h-12 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                <svg class="w-6 h-6 text-primary-600 dark:text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <div>
                <div class="font-bold text-gray-900 dark:text-white">
                  {{ auth.user?.employee_name || 'Admin' }}
                </div>
                <div class="text-sm text-gray-500 dark:text-gray-400 capitalize">
                  {{ isAdmin ? 'Administrator' : 'Employee' }}
                </div>
              </div>
            </div>
          </div>
          
          <nav class="p-2">
            <button
              v-for="tab in allTabs"
              :key="tab.id"
              @click="changeTab(tab.id)"
              :class="[
                'w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors text-sm font-medium',
                activeTab === tab.id
                  ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800',
              ]"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="tab.icon" />
              </svg>
              <span>{{ tab.name }}</span>
            </button>
          </nav>
        </div>
      </div>

      <!-- Content -->
      <div class="flex-1">
        <!-- Success/Error Messages -->
        <div v-if="successMessage" class="mb-4 p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400 rounded-lg">
          {{ successMessage }}
        </div>
        <div v-if="error" class="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 rounded-lg">
          {{ error }}
        </div>

        <!-- Pending Models Tab -->
        <div v-if="activeTab === 'pending-models'" class="space-y-6 animate-fade-in">
          <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Pending Model Reviews</h2>
          
          <div v-if="loading" class="text-center py-12">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          </div>
          
          <div v-else-if="pendingModels.length === 0" class="text-center py-12 bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50">
            <svg class="mx-auto h-16 w-16 text-gray-300 dark:text-gray-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p class="text-gray-500 dark:text-gray-400">No models pending review</p>
          </div>
          
          <div v-else class="grid gap-4">
            <div v-for="model in pendingModels" :key="model.id" class="bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50 p-6">
              <div class="flex items-start justify-between">
                <div class="flex items-start space-x-4 cursor-pointer hover:opacity-80" @click="viewModelDetail(model.id)">
                  <div class="w-20 h-20 bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden flex-shrink-0">
                    <img v-if="model.thumbnail_url" :src="model.thumbnail_url" class="w-full h-full object-cover" />
                    <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                      <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                  </div>
                  <div>
                    <h3 class="font-semibold text-gray-900 dark:text-white hover:text-primary-600">{{ model.model_name }}</h3>
                    <p class="text-sm text-gray-500 dark:text-gray-400">by {{ model.owner_name || model.owner_email }}</p>
                    <p v-if="model.description" class="text-sm text-gray-600 dark:text-gray-300 mt-2 line-clamp-2">{{ model.description }}</p>
                    <p class="text-xs text-primary-500 mt-1">Click to view details</p>
                  </div>
                </div>
                <div class="flex space-x-2">
                  <button @click="approveModel(model.id)" class="btn-primary text-sm">
                    Approve
                  </button>
                  <button @click="openRejectModal(model)" class="btn-secondary text-sm text-red-600 border-red-300 hover:bg-red-50">
                    Reject
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Orders Tab -->
        <div v-if="activeTab === 'orders'" class="space-y-6 animate-fade-in">
          <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Order Management</h2>
          
          <div v-if="loading" class="text-center py-12">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          </div>
          
          <div v-else-if="pendingOrders.length === 0" class="text-center py-12 bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50">
            <svg class="mx-auto h-16 w-16 text-gray-300 dark:text-gray-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
            </svg>
            <p class="text-gray-500 dark:text-gray-400">No pending orders</p>
          </div>
          
          <div v-else class="bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50 overflow-hidden">
            <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead class="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Order ID</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                <tr v-for="order in pendingOrders" :key="order.id">
                  <td class="px-6 py-4 text-sm text-gray-900 dark:text-white">#{{ order.id?.slice(0, 8) }}</td>
                  <td class="px-6 py-4 text-sm text-gray-500">{{ order.customer_email }}</td>
                  <td class="px-6 py-4">
                    <span class="px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
                      {{ order.status }}
                    </span>
                  </td>
                  <td class="px-6 py-4 text-sm text-gray-900 dark:text-white">${{ order.total_price }}</td>
                  <td class="px-6 py-4 space-x-2">
                    <button @click="updateOrderStatus(order.id, 'PROCESSING')" class="text-blue-600 hover:text-blue-800 text-sm">
                      Process
                    </button>
                    <button @click="updateOrderStatus(order.id, 'SHIPPED')" class="text-green-600 hover:text-green-800 text-sm">
                      Ship
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Materials Tab (Admin only) -->
        <div v-if="activeTab === 'materials' && isAdmin" class="space-y-6 animate-fade-in">
          <div class="flex justify-between items-center">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Materials Management</h2>
            <button class="btn-primary text-sm">+ Add Material</button>
          </div>
          
          <div v-if="materials.length === 0" class="text-center py-12 bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50">
            <p class="text-gray-500">No materials configured</p>
          </div>
          
          <div v-else class="bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50 overflow-hidden">
            <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead class="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Density (g/cm³)</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Price (TWD/g)</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                <tr v-for="material in materials" :key="material.id">
                  <td class="px-6 py-4 text-sm font-medium text-gray-900 dark:text-white">{{ material.name }}</td>
                  <td class="px-6 py-4 text-sm text-gray-500">{{ material.density_g_cm3 }}</td>
                  <td class="px-6 py-4 text-sm text-gray-500">{{ material.price_twd_g }}</td>
                  <td class="px-6 py-4 space-x-2">
                    <button class="text-primary-600 hover:text-primary-800 text-sm">Edit</button>
                    <button class="text-red-600 hover:text-red-800 text-sm">Delete</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Shipping Tab (Admin only) -->
        <div v-if="activeTab === 'shipping' && isAdmin" class="space-y-6 animate-fade-in">
          <div class="flex justify-between items-center">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Shipping Options</h2>
            <button class="btn-primary text-sm">+ Add Option</button>
          </div>
          
          <div v-if="shippingOptions.length === 0" class="text-center py-12 bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50">
            <p class="text-gray-500">No shipping options configured</p>
          </div>
          
          <div v-else class="grid gap-4">
            <div v-for="option in shippingOptions" :key="option.id" class="bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50 p-6">
              <div class="flex justify-between items-start">
                <div>
                  <h3 class="font-semibold text-gray-900 dark:text-white">{{ option.name }}</h3>
                  <p class="text-sm text-gray-500">Type: {{ option.type }}</p>
                  <p class="text-sm text-gray-500">Base Fee: ${{ option.base_fee }}</p>
                </div>
                <div class="flex items-center space-x-2">
                  <span :class="option.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'" class="px-2 py-1 text-xs font-semibold rounded-full">
                    {{ option.is_active ? 'Active' : 'Inactive' }}
                  </span>
                  <button class="text-primary-600 hover:text-primary-800 text-sm">Edit</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Discounts Tab (Admin only) -->
        <div v-if="activeTab === 'discounts' && isAdmin" class="space-y-6 animate-fade-in">
          <div class="flex justify-between items-center">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Discount Management</h2>
            <button class="btn-primary text-sm">+ Add Discount</button>
          </div>
          
          <div class="text-center py-12 bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50">
            <p class="text-gray-500">Discount management coming soon</p>
          </div>
        </div>

        <!-- Employees Tab (Admin only) -->
        <div v-if="activeTab === 'employees' && isAdmin" class="space-y-6 animate-fade-in">
          <div class="flex justify-between items-center">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">Employee Management</h2>
            <button class="btn-primary text-sm">+ Add Employee</button>
          </div>
          
          <div class="text-center py-12 bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50">
            <p class="text-gray-500">Employee management coming soon</p>
            <p class="text-sm text-gray-400 mt-2">Use Django Admin for now: /admin/</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Reject Modal -->
    <div v-if="showRejectModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-dark-surface rounded-xl p-6 max-w-md w-full mx-4">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Reject Model</h3>
        <p class="text-sm text-gray-500 mb-4">Please provide a reason for rejecting "{{ reviewingModel?.model_name }}":</p>
        <textarea
          v-model="rejectReason"
          rows="4"
          class="input-field w-full mb-4"
          placeholder="Enter rejection reason (required)..."
        ></textarea>
        <div class="flex justify-end space-x-2">
          <button @click="showRejectModal = false" class="btn-secondary">Cancel</button>
          <button @click="rejectModel" class="btn-primary bg-red-600 hover:bg-red-700">Reject</button>
        </div>
      </div>
    </div>
  </div>
</template>
