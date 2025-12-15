<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { useI18n } from 'vue-i18n';

const { t } = useI18n();
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
const activeTab = ref('pending') // Changed from 'pending-models'

// Data states
const pendingModels = ref([])
const pendingOrders = ref([])
const allModels = ref([])
const materials = ref([])
const shippingOptions = ref([])
const employees = ref([])
const globalDiscounts = ref([])

const loading = ref(false)
const error = ref('')
const successMessage = ref('')

// Material modal state
const showMaterialModal = ref(false)
const editingMaterial = ref(null)
const materialForm = ref({
  name: '',
  density_g_cm3: '',
  price_twd_g: '',
  is_active: true
})

// Shipping modal state
const showShippingModal = ref(false)
const editingShipping = ref(null)
const shippingForm = ref({
  name: '',
  type: 'HOME_DELIVERY',
  base_fee: '',
  is_active: true
})
const shippingTypes = [
  { value: 'HOME_DELIVERY', label: 'Home Delivery' },
  { value: 'CONVENIENCE_STORE', label: 'Convenience Store' },
  { value: 'SELF_PICKUP', label: 'Self Pickup' }
]

// Model status modal state
const showModelStatusModal = ref(false)
const editingModelStatus = ref(null)
const newModelStatus = ref('')
const modelStatuses = [
  { value: 'PUBLIC', label: 'Public' },
  { value: 'PENDING', label: 'Pending Review' },
  { value: 'REJECTED', label: 'Rejected' },
  { value: 'PRIVATE', label: 'Private' }
]

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
    // Fetch all orders, not just pending ones
    const response = await apiClient.get('/orders/all_orders/')
    pendingOrders.value = response.data || []
  } catch (err) {
    console.error('Failed to fetch orders:', err)
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

const fetchAllModels = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/models/')
    allModels.value = response.data?.results || response.data || []
  } catch (err) {
    error.value = 'Failed to load models'
    allModels.value = []
  } finally {
    loading.value = false
  }
}

// Model review actions
const reviewingModel = ref(null)
const rejectReason = ref('')
const showRejectModal = ref(false)

// New variables for reject modal
const identifyingModel = ref(null);
const rejectionReason = ref('');

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
  identifyingModel.value = model; // Use identifyingModel
  rejectionReason.value = ''; // Use rejectionReason
  showRejectModal.value = true;
}

const confirmReject = async () => { // Renamed from rejectModel
  if (!rejectionReason.value.trim()) {
    error.value = 'Rejection reason is required'
    return
  }
  
  try {
    await axios.post(`/api/models/${identifyingModel.value.id}/reject/`, { // Use identifyingModel
      reason: rejectionReason.value // Use rejectionReason
    }, {
      headers: { Authorization: `Token ${auth.token}` }
    })
    successMessage.value = 'Model rejected'
    pendingModels.value = pendingModels.value.filter(m => m.id !== identifyingModel.value.id) // Use identifyingModel
    showRejectModal.value = false
    identifyingModel.value = null // Use identifyingModel
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

// Get status badge color
const getStatusColor = (status) => {
  const colors = {
    'PENDING': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
    'PROCESSING': 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    'SHIPPED': 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    'DELIVERED': 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400',
    'CANCELLED': 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
  }
  return colors[status] || 'bg-gray-100 text-gray-800'
}

// Material CRUD actions
const openAddMaterial = () => {
  editingMaterial.value = null
  materialForm.value = { name: '', density_g_cm3: '', price_twd_g: '', is_active: true }
  showMaterialModal.value = true
}

const openEditMaterial = (material) => {
  editingMaterial.value = material
  materialForm.value = {
    name: material.name,
    density_g_cm3: material.density_g_cm3,
    price_twd_g: material.price_twd_g,
    is_active: material.is_active
  }
  showMaterialModal.value = true
}

const saveMaterial = async () => {
  try {
    if (editingMaterial.value) {
      await apiClient.put(`/materials/${editingMaterial.value.id}/`, materialForm.value)
      successMessage.value = 'Material updated successfully'
    } else {
      await apiClient.post('/materials/', materialForm.value)
      successMessage.value = 'Material created successfully'
    }
    showMaterialModal.value = false
    await fetchMaterials()
    setTimeout(() => successMessage.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to save material'
  }
}

const deleteMaterial = async (materialId) => {
  if (!confirm('Are you sure you want to delete this material?')) return
  try {
    await apiClient.delete(`/materials/${materialId}/`)
    successMessage.value = 'Material deleted successfully'
    await fetchMaterials()
    setTimeout(() => successMessage.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to delete material'
  }
}

// Shipping CRUD actions
const openAddShipping = () => {
  editingShipping.value = null
  shippingForm.value = { name: '', type: 'HOME_DELIVERY', base_fee: '', is_active: true }
  showShippingModal.value = true
}

const openEditShipping = (option) => {
  editingShipping.value = option
  shippingForm.value = {
    name: option.name,
    type: option.type,
    base_fee: option.base_fee,
    is_active: option.is_active
  }
  showShippingModal.value = true
}

const saveShipping = async () => {
  try {
    if (editingShipping.value) {
      await apiClient.put(`/shipping/options/${editingShipping.value.id}/`, shippingForm.value)
      successMessage.value = 'Shipping option updated successfully'
    } else {
      await apiClient.post('/shipping/options/', shippingForm.value)
      successMessage.value = 'Shipping option created successfully'
    }
    showShippingModal.value = false
    await fetchShippingOptions()
    setTimeout(() => successMessage.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to save shipping option'
  }
}

const deleteShipping = async (optionId) => {
  if (!confirm('Are you sure you want to delete this shipping option?')) return
  try {
    await apiClient.delete(`/shipping/options/${optionId}/`)
    successMessage.value = 'Shipping option deleted successfully'
    await fetchShippingOptions()
    setTimeout(() => successMessage.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to delete shipping option'
  }
}

// Model management actions
const openModelStatusModal = (model) => {
  editingModelStatus.value = model
  newModelStatus.value = model.visibility_status || model.visibility
  showModelStatusModal.value = true
}

const updateModelStatus = async () => {
  if (!editingModelStatus.value || !newModelStatus.value) return

  try {
    await apiClient.patch(`/models/${editingModelStatus.value.id}/`, {
      visibility_status: newModelStatus.value
    })
    successMessage.value = 'Model status updated successfully'
    showModelStatusModal.value = false
    await fetchAllModels()
    setTimeout(() => successMessage.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to update model status'
  }
}

const deleteModel = async (modelId, modelName) => {
  if (!confirm(`Are you sure you want to delete "${modelName}"? This action cannot be undone.`)) return

  try {
    await apiClient.delete(`/models/${modelId}/`)
    successMessage.value = 'Model deleted successfully'
    await fetchAllModels()
    setTimeout(() => successMessage.value = '', 3000)
  } catch (err) {
    console.error('Delete model error:', err.response)
    error.value = err.response?.data?.detail || err.response?.data?.error || JSON.stringify(err.response?.data) || 'Failed to delete model'
    setTimeout(() => error.value = '', 5000)
  }
}

const getVisibilityColor = (visibility) => {
  const colors = {
    'PUBLIC': 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    'PENDING': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
    'REJECTED': 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    'PRIVATE': 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400'
  }
  return colors[visibility] || 'bg-gray-100 text-gray-800'
}

// Tab change handler
const changeTab = (tab) => {
  activeTab.value = tab
  error.value = ''
  successMessage.value = ''

  if (tab === 'pending') fetchPendingModels() // Changed from 'pending-models'
  else if (tab === 'orders') fetchPendingOrders()
  else if (tab === 'models' && isAdmin.value) fetchAllModels()
  else if (tab === 'materials' && isAdmin.value) fetchMaterials()
  else if (tab === 'shipping' && isAdmin.value) fetchShippingOptions()
}

// Initialize
onMounted(() => {
  fetchPendingModels()
})

// Employee tabs
const employeeTabs = computed(() => [
  { id: 'pending', name: t('admin.sidebar.pendingModels'), icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
  { id: 'orders', name: t('admin.sidebar.orders'), icon: 'M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z' },
]);

// Admin-only tabs
const adminTabs = computed(() => [
  { id: 'models', name: t('admin.sidebar.models'), icon: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10' },
  { id: 'materials', name: t('admin.sidebar.materials'), icon: 'M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z' },
  { id: 'shipping', name: t('admin.sidebar.shipping'), icon: 'M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4' },
  { id: 'discounts', name: t('admin.sidebar.discounts'), icon: 'M12 8v13m0-13V6a2 2 0 112 2h-2zm0 0V5.5A2.5 2.5 0 109.5 8H12zm-7 4h14M5 12a2 2 0 110-4h14a2 2 0 110 4M5 12v7a2 2 0 002 2h10a2 2 0 002-2v-7' },
  { id: 'employees', name: t('admin.sidebar.employees'), icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z' },
]);

const allTabs = computed(() => {
  if (isAdmin.value) {
    return [...employeeTabs.value, ...adminTabs.value] // Access .value for computed refs
  }
  return employeeTabs.value // Access .value for computed refs
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

        <!-- Pending Models -->
        <div v-if="activeTab === 'pending'">
          <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-6">{{ $t('admin.pendingReviews.title') }}</h2>
          
          <div v-if="loading" class="text-center py-12">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          </div>

          <div v-else-if="pendingModels.length === 0" class="text-center py-12 bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50">
             <svg class="mx-auto h-16 w-16 text-gray-300 dark:text-gray-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p class="text-gray-500 dark:text-gray-400">{{ $t('admin.pendingReviews.noPending') }}</p>
          </div>

          <div v-else class="space-y-4">
            <div 
              v-for="model in pendingModels" 
              :key="model.id"
              class="bg-white dark:bg-dark-surface p-6 rounded-xl border border-gray-100 dark:border-gray-700/50 flex items-start space-x-4"
            >
              <img 
                :src="model.thumbnail_url" 
                :alt="model.model_name"
                class="w-32 h-24 object-cover rounded-lg bg-gray-100 dark:bg-gray-800"
              >
              
              <div class="flex-1">
                <div class="flex justify-between items-start">
                  <div>
                    <h3 class="text-lg font-semibold text-gray-900 dark:text-white">{{ model.model_name }}</h3>
                    <p class="text-sm text-gray-500 dark:text-gray-400">
                      {{ $t('modelDetail.by') }} {{ model.owner_name || model.owner_email }} • {{ model.category_name }}
                    </p>
                  </div>
                  <div class="flex space-x-2">
                    <button 
                      @click="approveModel(model.id)"
                      class="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg text-sm font-medium transition-colors"
                    >
                      {{ $t('admin.pendingReviews.approve') }}
                    </button>
                    <button 
                      @click="openRejectModal(model)"
                      class="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-sm font-medium transition-colors"
                    >
                      {{ $t('admin.pendingReviews.reject') }}
                    </button>
                  </div>
                </div>
                
                <p class="mt-2 text-gray-600 dark:text-gray-300 line-clamp-2">{{ model.description }}</p>
                
                <div class="mt-4 flex space-x-4 text-sm text-gray-500 dark:text-gray-400">
                  <a :href="model.file_url" download class="text-primary-600 hover:text-primary-500 flex items-center">
                    <svg class="w-4 h-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    Download STL
                  </a>
                  <button @click="viewModelDetail(model.id)" class="text-primary-600 hover:text-primary-500">
                    {{ $t('admin.pendingReviews.clickToView') }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Orders -->
        <div v-if="activeTab === 'orders'">
          <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-6">{{ $t('admin.orders.title') }}</h2>
          <div v-if="loading" class="text-center py-12">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          </div>
          <div v-else class="bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50 overflow-hidden">
            <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead class="bg-gray-50 dark:bg-gray-800">
                <tr>
                   <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ $t('admin.orders.columns.id') }}</th>
                   <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ $t('admin.orders.columns.customer') }}</th>
                   <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ $t('admin.orders.columns.status') }}</th>
                   <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ $t('admin.orders.columns.total') }}</th>
                   <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ $t('admin.orders.columns.actions') }}</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                 <tr v-if="pendingOrders.length === 0">
                   <td colspan="5" class="px-6 py-12 text-center text-gray-500 dark:text-gray-400">
                     {{ $t('admin.orders.noPending') }}
                   </td>
                 </tr>
                 <tr v-for="order in pendingOrders" :key="order.id">
                   <td class="px-6 py-4 whitespace-nowrap text-sm code">#{{ order.id?.slice(0, 8) }}</td>
                   <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{{ order.customer_email }}</td>
                   <td class="px-6 py-4 whitespace-nowrap">
                     <span :class="['px-2 inline-flex text-xs leading-5 font-semibold rounded-full', getStatusColor(order.status)]">
                       {{ order.status }}
                     </span>
                   </td>
                   <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">NT$ {{ order.total_price }}</td>
                   <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                     <button
                       v-if="order.status === 'PENDING'"
                       @click="updateOrderStatus(order.id, 'PROCESSING')"
                       class="text-blue-600 hover:text-blue-800 text-sm"
                     >
                      {{ $t('admin.orders.process') }}
                     </button>
                     <button
                       v-if="order.status === 'PENDING' || order.status === 'PROCESSING'"
                       @click="updateOrderStatus(order.id, 'SHIPPED')"
                       class="text-green-600 hover:text-green-800 text-sm"
                     >
                       {{ $t('admin.orders.ship') }}
                     </button>
                     <button
                       v-if="order.status === 'SHIPPED'"
                       @click="updateOrderStatus(order.id, 'DELIVERED')"
                       class="text-gray-600 hover:text-gray-800 text-sm"
                     >
                       {{ $t('admin.orders.deliver') }}
                     </button>
                   </td>
                 </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Materials -->
        <div v-if="activeTab === 'materials' && isAdmin">
          <div class="flex justify-between items-center mb-6">
            <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ $t('admin.materials.title') }}</h2>
            <button @click="openAddMaterial" class="btn-primary py-2 text-sm">{{ $t('admin.materials.add') }}</button>
          </div>

          <div v-if="loading" class="text-center py-12">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          </div>

          <div v-else class="bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50 overflow-hidden">
             <table class="w-full">
              <thead class="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ $t('admin.materials.columns.name') }}</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ $t('admin.materials.columns.density') }}</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ $t('admin.materials.columns.price') }}</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                  <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ $t('admin.materials.columns.actions') }}</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                <tr v-for="material in materials" :key="material.id">
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">{{ material.name }}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{{ material.density_g_cm3 }} g/cm³</td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">NT$ {{ material.price_twd_g }}/g</td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span :class="material.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'" class="px-2 py-1 text-xs font-semibold rounded-full">
                      {{ material.is_active ? 'Active' : 'Inactive' }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button @click="openEditMaterial(material)" class="text-primary-600 hover:text-primary-900 dark:hover:text-primary-400 mr-4">{{ $t('admin.materials.edit') }}</button>
                    <button @click="deleteMaterial(material.id)" class="text-red-600 hover:text-red-900 dark:hover:text-red-400">{{ $t('admin.materials.delete') }}</button>
                  </td>
                </tr>
              </tbody>
            </table>
            <div v-if="materials.length === 0" class="p-8 text-center text-gray-500 dark:text-gray-400">
              {{ $t('admin.materials.noMaterials') }}
            </div>
          </div>
        </div>

        <!-- Shipping Tab (Admin only) -->
        <div v-if="activeTab === 'shipping' && isAdmin">
          <div class="flex justify-between items-center mb-6">
            <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ $t('admin.shipping.title') }}</h2>
            <button @click="openAddShipping" class="btn-primary py-2 text-sm">{{ $t('admin.shipping.add') }}</button>
          </div>

          <div v-if="loading" class="text-center py-12">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          </div>

          <div v-else-if="shippingOptions.length === 0" class="text-center py-12 bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50">
            <p class="text-gray-500">{{ $t('admin.shipping.noOptions') }}</p>
          </div>

          <div v-else class="grid gap-4">
            <div v-for="option in shippingOptions" :key="option.id" class="bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50 p-6">
              <div class="flex justify-between items-start">
                <div>
                  <h3 class="font-semibold text-gray-900 dark:text-white">{{ option.name }}</h3>
                  <p class="text-sm text-gray-500">{{ $t('admin.shipping.type') }}: {{ option.type }}</p>
                  <p class="text-sm text-gray-500">{{ $t('admin.shipping.baseFee') }}: NT$ {{ option.base_fee }}</p>
                </div>
                <div class="flex items-center space-x-3">
                  <span :class="option.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'" class="px-2 py-1 text-xs font-semibold rounded-full">
                    {{ option.is_active ? $t('admin.shipping.active') : $t('admin.shipping.inactive') }}
                  </span>
                  <button @click="openEditShipping(option)" class="text-primary-600 hover:text-primary-800 text-sm">{{ $t('admin.shipping.edit') }}</button>
                  <button @click="deleteShipping(option.id)" class="text-red-600 hover:text-red-800 text-sm">Delete</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Models Management Tab (Admin only) -->
        <div v-if="activeTab === 'models' && isAdmin">
          <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-6">{{ $t('admin.models.title') }}</h2>

          <div v-if="loading" class="text-center py-12">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          </div>

          <div v-else-if="allModels.length === 0" class="text-center py-12 bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50">
            <p class="text-gray-500 dark:text-gray-400">{{ $t('admin.models.noModels') }}</p>
          </div>

          <div v-else class="bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50 overflow-hidden">
            <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead class="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ $t('admin.models.columns.model') }}</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ $t('admin.models.columns.owner') }}</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ $t('admin.models.columns.category') }}</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ $t('admin.models.columns.status') }}</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ $t('admin.models.columns.price') }}</th>
                  <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ $t('admin.models.columns.actions') }}</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                <tr v-for="model in allModels" :key="model.id">
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                      <img
                        :src="model.thumbnail_url || `https://placehold.co/100x80/6366f1/fff?text=${encodeURIComponent(model.model_name?.slice(0, 3) || 'M')}`"
                        :alt="model.model_name"
                        class="w-16 h-12 object-cover rounded-lg bg-gray-100 dark:bg-gray-800 mr-3"
                      />
                      <div>
                        <div class="text-sm font-medium text-gray-900 dark:text-white">{{ model.model_name }}</div>
                        <div class="text-xs text-gray-500 dark:text-gray-400">#{{ model.id?.toString().slice(0, 8) }}</div>
                      </div>
                    </div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {{ model.owner_name || model.owner_email?.split('@')[0] || 'Unknown' }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    {{ model.category_display || model.category }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span :class="['px-2 inline-flex text-xs leading-5 font-semibold rounded-full', getVisibilityColor(model.visibility_status || model.visibility)]">
                      {{ model.visibility_status || model.visibility }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                    NT$ {{ model.price || '0.00' }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                    <button
                      @click="openModelStatusModal(model)"
                      class="text-blue-600 hover:text-blue-800 dark:hover:text-blue-400"
                    >
                      {{ $t('admin.models.editStatus') }}
                    </button>
                    <button
                      @click="deleteModel(model.id, model.model_name)"
                      class="text-red-600 hover:text-red-800 dark:hover:text-red-400"
                    >
                      {{ $t('admin.models.delete') }}
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Other Tabs -->
        <div v-if="['discounts', 'employees'].includes(activeTab) && isAdmin">
          <div class="text-center py-24 bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50">
            <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-2">
              {{ $t('admin.common.comingSoon', { feature: activeTab.charAt(0).toUpperCase() + activeTab.slice(1) }) }}
            </h2>
            <p class="text-gray-500 dark:text-gray-400">
              {{ $t('admin.common.useDjangoAdmin') }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Material Modal -->
    <div v-if="showMaterialModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-dark-surface rounded-xl p-6 max-w-md w-full mx-4">
        <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-4">
          {{ editingMaterial ? 'Edit Material' : 'Add Material' }}
        </h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
            <input v-model="materialForm.name" type="text" class="input-field w-full" placeholder="e.g. PLA" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Density (g/cm³)</label>
            <input v-model="materialForm.density_g_cm3" type="number" step="0.00001" class="input-field w-full" placeholder="e.g. 1.24" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Price (TWD/g)</label>
            <input v-model="materialForm.price_twd_g" type="number" step="0.01" class="input-field w-full" placeholder="e.g. 0.80" />
          </div>
          <div class="flex items-center">
            <input v-model="materialForm.is_active" type="checkbox" id="is_active" class="mr-2" />
            <label for="is_active" class="text-sm text-gray-700 dark:text-gray-300">Active</label>
          </div>
        </div>
        <div class="flex justify-end space-x-4 mt-6">
          <button @click="showMaterialModal = false" class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
            Cancel
          </button>
          <button @click="saveMaterial" class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors">
            {{ editingMaterial ? 'Update' : 'Create' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Shipping Modal -->
    <div v-if="showShippingModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-dark-surface rounded-xl p-6 max-w-md w-full mx-4">
        <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-4">
          {{ editingShipping ? 'Edit Shipping Option' : 'Add Shipping Option' }}
        </h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
            <input v-model="shippingForm.name" type="text" class="input-field w-full" placeholder="e.g. Black Cat Delivery" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Type</label>
            <select v-model="shippingForm.type" class="input-field w-full">
              <option v-for="t in shippingTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Base Fee (TWD)</label>
            <input v-model="shippingForm.base_fee" type="number" step="0.01" class="input-field w-full" placeholder="e.g. 60" />
          </div>
          <div class="flex items-center">
            <input v-model="shippingForm.is_active" type="checkbox" id="shipping_is_active" class="mr-2" />
            <label for="shipping_is_active" class="text-sm text-gray-700 dark:text-gray-300">Active</label>
          </div>
        </div>
        <div class="flex justify-end space-x-4 mt-6">
          <button @click="showShippingModal = false" class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
            Cancel
          </button>
          <button @click="saveShipping" class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors">
            {{ editingShipping ? 'Update' : 'Create' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Reject Modal -->
    <div v-if="showRejectModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-dark-surface rounded-xl p-6 max-w-md w-full mx-4">
        <div class="p-6">
          <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-4">{{ $t('admin.pendingReviews.rejectTitle') }}</h3>
          <p class="mb-4 text-gray-600 dark:text-gray-300">
            {{ $t('admin.pendingReviews.rejectReason', { name: identifyingModel?.model_name }) }}
          </p>
          <textarea
            v-model="rejectionReason"
            class="input-field w-full mb-6"
            rows="4"
            :placeholder="$t('admin.pendingReviews.enterReason')"
          ></textarea>
          <div class="flex justify-end space-x-4">
            <button
              @click="showRejectModal = false"
              class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            >
              {{ $t('admin.pendingReviews.cancel') }}
            </button>
            <button
              @click="confirmReject"
              class="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors"
              :disabled="!rejectionReason"
            >
              {{ $t('admin.pendingReviews.confirmReject') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Model Status Modal -->
    <div v-if="showModelStatusModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-dark-surface rounded-xl p-6 max-w-md w-full mx-4">
        <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-4">
          {{ $t('admin.models.changeStatus') }}
        </h3>
        <p class="mb-4 text-gray-600 dark:text-gray-300">
          {{ $t('admin.models.changeStatusFor', { name: editingModelStatus?.model_name }) }}
        </p>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ $t('admin.models.newStatus') }}
            </label>
            <select v-model="newModelStatus" class="input-field w-full">
              <option v-for="status in modelStatuses" :key="status.value" :value="status.value">
                {{ status.label }}
              </option>
            </select>
          </div>
        </div>
        <div class="flex justify-end space-x-4 mt-6">
          <button
            @click="showModelStatusModal = false"
            class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            {{ $t('common.cancel') }}
          </button>
          <button
            @click="updateModelStatus"
            class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
          >
            {{ $t('admin.models.updateStatus') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

