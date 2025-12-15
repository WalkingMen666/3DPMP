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

// Tab change handler
const changeTab = (tab) => {
  activeTab.value = tab
  error.value = ''
  successMessage.value = ''
  
  if (tab === 'pending') fetchPendingModels() // Changed from 'pending-models'
  else if (tab === 'orders') fetchPendingOrders()
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
                     <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">
                       {{ order.status }}
                     </span>
                   </td>
                   <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">${{ order.total_price }}</td>
                   <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
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

        <!-- Materials -->
        <div v-if="activeTab === 'materials' && isAdmin">
          <div class="flex justify-between items-center mb-6">
            <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ $t('admin.materials.title') }}</h2>
            <button class="btn-primary py-2 text-sm">{{ $t('admin.materials.add') }}</button>
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
                  <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ $t('admin.materials.columns.actions') }}</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                <tr v-for="material in materials" :key="material.id">
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">{{ material.name }}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{{ material.density_g_cm3 }}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{{ material.price_twd_g }}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button class="text-primary-600 hover:text-primary-900 dark:hover:text-primary-400 mr-4">{{ $t('admin.materials.edit') }}</button>
                    <button class="text-red-600 hover:text-red-900 dark:hover:text-red-400">{{ $t('admin.materials.delete') }}</button>
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
            <button class="btn-primary py-2 text-sm">{{ $t('admin.shipping.add') }}</button>
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
                  <p class="text-sm text-gray-500">{{ $t('admin.shipping.baseFee') }}: ${{ option.base_fee }}</p>
                </div>
                <div class="flex items-center space-x-2">
                  <span :class="option.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'" class="px-2 py-1 text-xs font-semibold rounded-full">
                    {{ option.is_active ? $t('admin.shipping.active') : $t('admin.shipping.inactive') }}
                  </span>
                  <button class="text-primary-600 hover:text-primary-800 text-sm">{{ $t('admin.shipping.edit') }}</button>
                </div>
              </div>
            </div>
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
  </div>
</template>

