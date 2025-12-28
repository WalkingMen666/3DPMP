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
const coupons = ref([])

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

// Slicing edit modal state
const showSlicingEditModal = ref(false)
const editingSlicingModel = ref(null)
const slicingForm = ref({
  filament_used_mm: '',
  filament_used_cm3: ''
})

// GlobalDiscount modal state
const showGlobalDiscountModal = ref(false)
const editingGlobalDiscount = ref(null)
const globalDiscountForm = ref({
  name: '',
  discount_type: 'PERCENTAGE',
  discount_value: '',
  min_order_amount: '',
  start_date: '',
  end_date: '',
  is_active: true
})
const discountTypes = [
  { value: 'PERCENTAGE', label: 'Percentage (%)' },
  { value: 'FIXED', label: 'Fixed Amount (NT$)' }
]

// Coupon modal state
const showCouponModal = ref(false)
const editingCoupon = ref(null)
const couponForm = ref({
  name: '',
  code: '',
  discount_type: 'PERCENTAGE',
  discount_value: '',
  min_order_amount: '',
  max_uses: '',
  start_date: '',
  end_date: '',
  is_active: true
})

// Discount validation helpers
const getDiscountWarnings = (discountValue, discountType) => {
  const value = parseFloat(discountValue)
  const warnings = []
  
  if (isNaN(value) || discountValue === '') {
    return warnings
  }
  
  // Negative value warning
  if (value < 0) {
    warnings.push({
      type: 'error',
      icon: '⚠️',
      message: '負數折扣將會增加訂單金額，而非減少！'
    })
  }
  
  if (discountType === 'PERCENTAGE') {
    // Percentage over 100% warning
    if (value > 100) {
      warnings.push({
        type: 'error',
        icon: '❌',
        message: '百分比折扣不能超過 100%'
      })
    }
    
    // Small decimal warning (e.g., 0.1 might mean 10%)
    if (value > 0 && value < 1) {
      warnings.push({
        type: 'info',
        icon: '💡',
        message: `您輸入了 ${value}%，是否想輸入 ${value * 100}%？（例如：輸入 10 表示 10% 折扣）`
      })
    }
    
    // Show discount preview for valid percentages
    if (value > 0 && value <= 100) {
      const samplePrice = 1000
      const discountAmount = samplePrice * (value / 100)
      warnings.push({
        type: 'preview',
        icon: '📊',
        message: `預覽：NT$${samplePrice} 的訂單將折扣 NT$${discountAmount.toFixed(0)}（最終價格 NT$${(samplePrice - discountAmount).toFixed(0)}）`
      })
    }
  } else {
    // FIXED discount type
    if (value > 0) {
      warnings.push({
        type: 'preview',
        icon: '📊',
        message: `預覽：訂單將減少 NT$${value.toFixed(0)}`
      })
    }
  }
  
  return warnings
}

// Coupon warnings
const couponWarnings = computed(() => {
  return getDiscountWarnings(couponForm.value.discount_value, couponForm.value.discount_type)
})

// Global discount warnings  
const globalDiscountWarnings = computed(() => {
  return getDiscountWarnings(globalDiscountForm.value.discount_value, globalDiscountForm.value.discount_type)
})

// Helper functions for coupon/discount status
const formatDate = (dateStr) => {
  if (!dateStr) return null
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-TW', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

const getCouponDateRange = (coupon) => {
  const start = formatDate(coupon.start_date) || formatDate(coupon.created_at) || '---'
  const end = formatDate(coupon.end_date) || '無期限'
  return `${start} ~ ${end}`
}

const getCouponStatus = (coupon) => {
  const now = new Date()
  
  // Check if manually deactivated
  if (!coupon.is_active) {
    return { status: 'inactive', label: '已停用', class: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300' }
  }
  
  // Check if not yet started
  if (coupon.start_date) {
    const startDate = new Date(coupon.start_date)
    if (now < startDate) {
      return { status: 'pending', label: '尚未開始', class: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' }
    }
  }
  
  // Check if expired
  if (coupon.end_date) {
    const endDate = new Date(coupon.end_date)
    if (now > endDate) {
      return { status: 'expired', label: '已過期', class: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' }
    }
  }
  
  // Check if usage limit reached
  if (coupon.max_uses && coupon.times_used >= coupon.max_uses) {
    return { status: 'limit_reached', label: '已達上限', class: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400' }
  }
  
  // Active and valid
  return { status: 'active', label: '有效', class: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' }
}


// Employee modal state
const showEmployeeModal = ref(false)
const editingEmployee = ref(null)
const employeeForm = ref({
  email: '',
  password: '',
  employee_name: '',
  is_admin: false
})

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
    error.value = t('admin.messages.loadFailed')
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
    error.value = t('admin.messages.loadFailed')
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
    error.value = t('admin.messages.loadFailed')
    allModels.value = []
  } finally {
    loading.value = false
  }
}

// Fetch global discounts
const fetchGlobalDiscounts = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/discounts/global-discounts/')
    globalDiscounts.value = response.data?.results || response.data || []
  } catch (err) {
    globalDiscounts.value = []
  } finally {
    loading.value = false
  }
}

// Fetch coupons
const fetchCoupons = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/discounts/coupons/')
    coupons.value = response.data?.results || response.data || []
  } catch (err) {
    coupons.value = []
  } finally {
    loading.value = false
  }
}

// Fetch employees
const fetchEmployees = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/auth/employees/')
    employees.value = response.data?.results || response.data || []
  } catch (err) {
    employees.value = []
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
    successMessage.value = t('admin.messages.approveSuccess')
    pendingModels.value = pendingModels.value.filter(m => m.id !== modelId)
    setTimeout(() => successMessage.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.error || t('admin.messages.approveFailed')
  }
}

const openRejectModal = (model) => {
  identifyingModel.value = model; // Use identifyingModel
  rejectionReason.value = ''; // Use rejectionReason
  showRejectModal.value = true;
}

const confirmReject = async () => { // Renamed from rejectModel
  if (!rejectionReason.value.trim()) {
    error.value = t('admin.messages.rejectReasonRequired')
    return
  }
  
  try {
    await axios.post(`/api/models/${identifyingModel.value.id}/reject/`, { // Use identifyingModel
      reason: rejectionReason.value // Use rejectionReason
    }, {
      headers: { Authorization: `Token ${auth.token}` }
    })
    successMessage.value = t('admin.messages.rejectSuccess')
    pendingModels.value = pendingModels.value.filter(m => m.id !== identifyingModel.value.id) // Use identifyingModel
    showRejectModal.value = false
    identifyingModel.value = null // Use identifyingModel
    setTimeout(() => successMessage.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.error || t('admin.messages.rejectFailed')
  }
}

// Order detail modal state
const showOrderDetailModal = ref(false)
const selectedOrder = ref(null)

// Order actions
const viewOrderDetail = async (orderId) => {
  try {
    const response = await apiClient.get(`/orders/${orderId}/`)
    selectedOrder.value = response.data
    showOrderDetailModal.value = true
  } catch (err) {
    error.value = t('admin.messages.loadFailed')
  }
}

const updateOrderStatus = async (orderId, newStatus) => {
  try {
    await apiClient.patch(`/orders/${orderId}/update_status/`, { status: newStatus })
    successMessage.value = t('admin.messages.statusUpdateSuccess', { status: newStatus })
    await fetchPendingOrders()
    setTimeout(() => successMessage.value = '', 3000)
  } catch (err) {
    error.value = t('admin.messages.statusUpdateFailed')
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
      successMessage.value = t('admin.messages.materialSaved')
    }
    showMaterialModal.value = false
    await fetchMaterials()
    setTimeout(() => successMessage.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.detail || t('admin.messages.materialSaveFailed')
  }
}

const deleteMaterial = async (materialId) => {
  if (!confirm(t('admin.messages.confirmDeleteMaterial'))) return
  try {
    await apiClient.delete(`/materials/${materialId}/`)
    successMessage.value = t('admin.messages.materialDeleted')
    await fetchMaterials()
    setTimeout(() => successMessage.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.detail || t('admin.messages.materialDeleteFailed')
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
  if (!confirm(t('admin.messages.confirmDeleteShipping'))) return
  try {
    await apiClient.delete(`/shipping/options/${optionId}/`)
    successMessage.value = t('admin.messages.shippingDeleted')
    await fetchShippingOptions()
    setTimeout(() => successMessage.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.detail || t('admin.messages.shippingDeleteFailed')
  }
}

// Global Discount CRUD actions
const openAddGlobalDiscount = () => {
  editingGlobalDiscount.value = null
  globalDiscountForm.value = {
    name: '',
    discount_type: 'PERCENTAGE',
    discount_value: '',
    min_order_amount: '',
    start_date: '',
    end_date: '',
    is_active: true
  }
  showGlobalDiscountModal.value = true
}

const openEditGlobalDiscount = (discount) => {
  editingGlobalDiscount.value = discount
  globalDiscountForm.value = {
    name: discount.name,
    discount_type: discount.discount_type,
    discount_value: discount.discount_value,
    min_order_amount: discount.min_order_amount || '',
    start_date: discount.start_date?.split('T')[0] || '',
    end_date: discount.end_date?.split('T')[0] || '',
    is_active: discount.is_active
  }
  showGlobalDiscountModal.value = true
}

const saveGlobalDiscount = async () => {
  try {
    const payload = { ...globalDiscountForm.value }
    if (!payload.min_order_amount) delete payload.min_order_amount
    if (!payload.start_date) delete payload.start_date
    if (!payload.end_date) delete payload.end_date

    if (editingGlobalDiscount.value) {
      await apiClient.put(`/discounts/global-discounts/${editingGlobalDiscount.value.id}/`, payload)
      successMessage.value = 'Global discount updated successfully'
    } else {
      await apiClient.post('/discounts/global-discounts/', payload)
      successMessage.value = 'Global discount created successfully'
    }
    showGlobalDiscountModal.value = false
    await fetchGlobalDiscounts()
    setTimeout(() => successMessage.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to save global discount'
  }
}

const deleteGlobalDiscount = async (discountId) => {
  if (!confirm('Are you sure you want to delete this global discount?')) return
  try {
    await apiClient.delete(`/discounts/global-discounts/${discountId}/`)
    successMessage.value = 'Global discount deleted successfully'
    await fetchGlobalDiscounts()
    setTimeout(() => successMessage.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to delete global discount'
  }
}

// Coupon CRUD actions
const openAddCoupon = () => {
  editingCoupon.value = null
  couponForm.value = {
    name: '',
    code: '',
    discount_type: 'PERCENTAGE',
    discount_value: '',
    min_order_amount: '',
    max_uses: '',
    start_date: '',
    end_date: '',
    is_active: true
  }
  showCouponModal.value = true
}

const openEditCoupon = (coupon) => {
  editingCoupon.value = coupon
  couponForm.value = {
    name: coupon.name,
    code: coupon.code,
    discount_type: coupon.discount_type,
    discount_value: coupon.discount_value,
    min_order_amount: coupon.min_order_amount || '',
    max_uses: coupon.max_uses || '',
    start_date: coupon.start_date?.split('T')[0] || '',
    end_date: coupon.end_date?.split('T')[0] || '',
    is_active: coupon.is_active
  }
  showCouponModal.value = true
}

const saveCoupon = async () => {
  try {
    const payload = { ...couponForm.value }
    if (!payload.min_order_amount) delete payload.min_order_amount
    if (!payload.max_uses) delete payload.max_uses
    if (!payload.start_date) delete payload.start_date
    if (!payload.end_date) delete payload.end_date

    if (editingCoupon.value) {
      await apiClient.put(`/discounts/coupons/${editingCoupon.value.id}/`, payload)
      successMessage.value = 'Coupon updated successfully'
    } else {
      await apiClient.post('/discounts/coupons/', payload)
      successMessage.value = 'Coupon created successfully'
    }
    showCouponModal.value = false
    await fetchCoupons()
    setTimeout(() => successMessage.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to save coupon'
  }
}

const deleteCoupon = async (couponId) => {
  if (!confirm('Are you sure you want to delete this coupon?')) return
  try {
    await apiClient.delete(`/discounts/coupons/${couponId}/`)
    successMessage.value = 'Coupon deleted successfully'
    await fetchCoupons()
    setTimeout(() => successMessage.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to delete coupon'
  }
}

// Employee CRUD actions
const openAddEmployee = () => {
  editingEmployee.value = null
  employeeForm.value = {
    email: '',
    password: '',
    employee_name: '',
    is_admin: false
  }
  showEmployeeModal.value = true
}

const openEditEmployee = (employee) => {
  editingEmployee.value = employee
  employeeForm.value = {
    email: employee.email,
    password: '',
    employee_name: employee.employee_name,
    is_admin: employee.is_admin
  }
  showEmployeeModal.value = true
}

const saveEmployee = async () => {
  try {
    if (editingEmployee.value) {
      await apiClient.patch(`/auth/employees/${editingEmployee.value.id}/`, {
        employee_name: employeeForm.value.employee_name,
        is_admin: employeeForm.value.is_admin
      })
      successMessage.value = 'Employee updated successfully'
    } else {
      await apiClient.post('/auth/employees/', employeeForm.value)
      successMessage.value = 'Employee created successfully'
    }
    showEmployeeModal.value = false
    await fetchEmployees()
    setTimeout(() => successMessage.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.email?.[0] || err.response?.data?.detail || 'Failed to save employee'
  }
}

const deleteEmployee = async (employeeId) => {
  if (!confirm('Are you sure you want to deactivate this employee?')) return
  try {
    await apiClient.delete(`/auth/employees/${employeeId}/`)
    successMessage.value = 'Employee deactivated successfully'
    await fetchEmployees()
    setTimeout(() => successMessage.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to deactivate employee'
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
    successMessage.value = t('admin.messages.modelStatusUpdated')
    showModelStatusModal.value = false
    await fetchAllModels()
    setTimeout(() => successMessage.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to update model status'
  }
}

const deleteModel = async (modelId, modelName) => {
  if (!confirm(t('admin.messages.confirmDeleteModel', { name: modelName }))) return

  try {
    await apiClient.delete(`/models/${modelId}/`)
    successMessage.value = t('admin.messages.modelDeleted')
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

const getSlicingStatusColor = (status) => {
  const colors = {
    'PENDING': 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400',
    'PROCESSING': 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    'COMPLETED': 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    'FAILED': 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
  }
  return colors[status] || 'bg-gray-100 text-gray-800'
}

// Slicing actions
const triggerReslice = async (model) => {
  try {
    await apiClient.post(`/models/${model.id}/reslice/`)
    successMessage.value = t('admin.messages.resliceTriggered') || 'Slicing task queued'
    // Update local state
    model.slicing_status = 'PROCESSING'
    setTimeout(() => successMessage.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to trigger reslice'
    setTimeout(() => error.value = '', 5000)
  }
}

const openSlicingEditModal = (model) => {
  editingSlicingModel.value = model
  slicingForm.value = {
    filament_used_mm: model.slicing_info?.filament_used_mm || '',
    filament_used_cm3: model.slicing_info?.filament_used_cm3 || ''
  }
  showSlicingEditModal.value = true
}

const saveSlicingInfo = async () => {
  if (!editingSlicingModel.value) return
  
  // Validate at least one value is provided
  if (!slicingForm.value.filament_used_mm && !slicingForm.value.filament_used_cm3) {
    error.value = t('admin.messages.slicingValueRequired') || 'At least one value is required'
    return
  }
  
  try {
    const payload = {}
    if (slicingForm.value.filament_used_mm) {
      payload.filament_used_mm = parseFloat(slicingForm.value.filament_used_mm)
    }
    if (slicingForm.value.filament_used_cm3) {
      payload.filament_used_cm3 = parseFloat(slicingForm.value.filament_used_cm3)
    }
    
    await apiClient.patch(`/models/${editingSlicingModel.value.id}/update_slicing_info/`, payload)
    successMessage.value = t('admin.messages.slicingInfoSaved') || 'Slicing info saved'
    showSlicingEditModal.value = false
    await fetchAllModels()
    setTimeout(() => successMessage.value = '', 3000)
  } catch (err) {
    error.value = err.response?.data?.error || 'Failed to save slicing info'
  }
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
  else if (tab === 'discounts' && isAdmin.value) {
    fetchGlobalDiscounts()
    fetchCoupons()
  }
  else if (tab === 'employees' && isAdmin.value) fetchEmployees()
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
                      {{ $t('modelDetail.by') }} {{ model.owner_name || model.owner_email }} • {{ $t('marketplace.categoriesList.' + model.category) }}
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
                    {{ $t('admin.messages.downloadSTL') }}
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
                       @click="viewOrderDetail(order.id)"
                       class="text-primary-600 hover:text-primary-800 text-sm"
                     >
                       {{ $t('admin.orders.viewDetail') }}
                     </button>
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

          <div v-else class="bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50 overflow-hidden overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead class="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ $t('admin.models.columns.model') }}</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ $t('admin.models.columns.owner') }}</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ $t('admin.models.columns.status') }}</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">{{ $t('admin.models.columns.slicing') || 'Slicing' }}</th>
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
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span :class="['px-2 inline-flex text-xs leading-5 font-semibold rounded-full', getVisibilityColor(model.visibility_status || model.visibility)]">
                      {{ model.visibility_status || model.visibility }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex flex-col space-y-1">
                      <span :class="['px-2 inline-flex text-xs leading-5 font-semibold rounded-full w-fit', getSlicingStatusColor(model.slicing_status)]">
                        {{ model.slicing_status || 'PENDING' }}
                        <span v-if="model.slicing_info?.source" class="ml-1 opacity-70">({{ model.slicing_info.source }})</span>
                      </span>
                      <div v-if="model.slicing_info" class="text-xs text-gray-500 dark:text-gray-400">
                        <span v-if="model.slicing_info.filament_used_mm">{{ model.slicing_info.filament_used_mm.toFixed(1) }}mm</span>
                        <span v-if="model.slicing_info.filament_used_cm3"> / {{ model.slicing_info.filament_used_cm3.toFixed(2) }}cm³</span>
                      </div>
                      <div v-if="model.slicing_error" class="text-xs text-red-500 truncate max-w-32" :title="model.slicing_error">
                        {{ model.slicing_error.slice(0, 30) }}...
                      </div>
                    </div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                    <button
                      @click="triggerReslice(model)"
                      class="text-purple-600 hover:text-purple-800 dark:hover:text-purple-400"
                      :disabled="model.slicing_status === 'PROCESSING'"
                    >
                      {{ $t('admin.models.reslice') || 'Reslice' }}
                    </button>
                    <button
                      @click="openSlicingEditModal(model)"
                      class="text-green-600 hover:text-green-800 dark:hover:text-green-400"
                    >
                      {{ $t('admin.models.editSlicing') || 'Edit' }}
                    </button>
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


        <!-- Discounts Tab (Admin only) -->
        <div v-if="activeTab === 'discounts' && isAdmin">
          <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-6">Discounts Management</h2>

          <!-- Global Discounts Section -->
          <div class="mb-8">
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Global Discounts</h3>
              <button @click="openAddGlobalDiscount" class="btn-primary py-2 text-sm">+ Add Global Discount</button>
            </div>

            <div v-if="loading" class="text-center py-8">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            </div>

            <div v-else-if="globalDiscounts.length === 0" class="text-center py-8 bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50">
              <p class="text-gray-500">No global discounts found</p>
            </div>

            <div v-else class="grid gap-4">
              <div v-for="discount in globalDiscounts" :key="discount.id" class="bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50 p-4">
                <div class="flex justify-between items-start">
                  <div>
                    <h4 class="font-semibold text-gray-900 dark:text-white">{{ discount.name }}</h4>
                    <p class="text-sm" :class="parseFloat(discount.discount_value) < 0 ? 'text-red-500' : 'text-gray-500'">
                      {{ discount.discount_type === 'PERCENTAGE' ? `${discount.discount_value}% 折扣` : `NT$ ${discount.discount_value} 折扣` }}
                      <span v-if="parseFloat(discount.discount_value) < 0" class="text-xs text-red-400">(加價)</span>
                    </p>
                    <p v-if="discount.min_order_amount" class="text-xs text-gray-400">最低訂購金額: NT$ {{ discount.min_order_amount }}</p>
                    <p class="text-xs text-gray-400">
                      有效期間: {{ getCouponDateRange(discount) }}
                    </p>
                  </div>
                  <div class="flex items-center space-x-3">
                    <span :class="getCouponStatus(discount).class" class="px-2 py-1 text-xs font-semibold rounded-full">
                      {{ getCouponStatus(discount).label }}
                    </span>
                    <button @click="openEditGlobalDiscount(discount)" class="text-primary-600 hover:text-primary-800 text-sm">編輯</button>
                    <button @click="deleteGlobalDiscount(discount.id)" class="text-red-600 hover:text-red-800 text-sm">刪除</button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Coupons Section -->
          <div>
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Coupons</h3>
              <button @click="openAddCoupon" class="btn-primary py-2 text-sm">+ Add Coupon</button>
            </div>

            <div v-if="loading" class="text-center py-8">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            </div>

            <div v-else-if="coupons.length === 0" class="text-center py-8 bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50">
              <p class="text-gray-500">No coupons found</p>
            </div>

            <div v-else class="bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50 overflow-hidden overflow-x-auto">
              <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead class="bg-gray-50 dark:bg-gray-800">
                  <tr>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">名稱</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">代碼</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">折扣</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">有效期間</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">使用次數</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">狀態</th>
                    <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">操作</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                  <tr v-for="coupon in coupons" :key="coupon.id">
                    <td class="px-4 py-3 text-sm text-gray-900 dark:text-white">{{ coupon.name }}</td>
                    <td class="px-4 py-3 text-sm font-mono text-primary-600">{{ coupon.code }}</td>
                    <td class="px-4 py-3 text-sm text-gray-500">
                      <span :class="parseFloat(coupon.discount_value) < 0 ? 'text-red-500' : ''">
                        {{ coupon.discount_type === 'PERCENTAGE' ? `${coupon.discount_value}%` : `NT$ ${coupon.discount_value}` }}
                      </span>
                      <span v-if="parseFloat(coupon.discount_value) < 0" class="ml-1 text-xs text-red-400">(加價)</span>
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-500 whitespace-nowrap">
                      {{ getCouponDateRange(coupon) }}
                    </td>
                    <td class="px-4 py-3 text-sm text-gray-500">{{ coupon.times_used || 0 }} / {{ coupon.max_uses || '∞' }}</td>
                    <td class="px-4 py-3">
                      <span :class="getCouponStatus(coupon).class" class="px-2 py-1 text-xs font-semibold rounded-full">
                        {{ getCouponStatus(coupon).label }}
                      </span>
                    </td>
                    <td class="px-4 py-3 text-right text-sm space-x-2">
                      <button @click="openEditCoupon(coupon)" class="text-primary-600 hover:text-primary-800">編輯</button>
                      <button @click="deleteCoupon(coupon.id)" class="text-red-600 hover:text-red-800">刪除</button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <!-- Employees Tab (Admin only) -->
        <div v-if="activeTab === 'employees' && isAdmin">
          <div class="flex justify-between items-center mb-6">
            <h2 class="text-xl font-bold text-gray-900 dark:text-white">Employees Management</h2>
            <button @click="openAddEmployee" class="btn-primary py-2 text-sm">+ Add Employee</button>
          </div>

          <div v-if="loading" class="text-center py-12">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          </div>

          <div v-else-if="employees.length === 0" class="text-center py-12 bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50">
            <p class="text-gray-500">No employees found</p>
          </div>

          <div v-else class="bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50 overflow-hidden">
            <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead class="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Employee</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Email</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Role</th>
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                  <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                <tr v-for="employee in employees" :key="employee.id">
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="flex items-center">
                      <div class="w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center mr-3">
                        <span class="text-primary-600 dark:text-primary-400 font-medium">
                          {{ employee.employee_name?.charAt(0)?.toUpperCase() || 'E' }}
                        </span>
                      </div>
                      <div class="text-sm font-medium text-gray-900 dark:text-white">{{ employee.employee_name }}</div>
                    </div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{{ employee.email }}</td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span :class="employee.is_admin ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400' : 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'" class="px-2 py-1 text-xs font-semibold rounded-full">
                      {{ employee.is_admin ? 'Admin' : 'Employee' }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span :class="employee.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'" class="px-2 py-1 text-xs font-semibold rounded-full">
                      {{ employee.is_active ? 'Active' : 'Inactive' }}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                    <button @click="openEditEmployee(employee)" class="text-primary-600 hover:text-primary-800 dark:hover:text-primary-400">Edit</button>
                    <button @click="deleteEmployee(employee.id)" class="text-red-600 hover:text-red-800 dark:hover:text-red-400">Deactivate</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Material Modal -->
    <div v-if="showMaterialModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-dark-surface rounded-xl p-6 max-w-md w-full mx-4">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100">
            {{ editingMaterial ? $t('admin.modals.editMaterial') : $t('admin.modals.addMaterial') }}
          </h3>
          <button @click="showMaterialModal = false" class="text-gray-400 hover:text-gray-500">
            <span class="sr-only">{{ $t('common.close') }}</span>
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ $t('admin.materials.columns.name') }}</label>
            <input v-model="materialForm.name" type="text" class="input-field w-full" :placeholder="$t('admin.modals.namePlaceholder')" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ $t('admin.materials.columns.density') }}</label>
            <input v-model="materialForm.density_g_cm3" type="number" step="0.00001" class="input-field w-full" :placeholder="$t('admin.modals.densityPlaceholder')" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ $t('admin.materials.columns.price') }}</label>
            <input v-model="materialForm.price_twd_g" type="number" step="0.01" class="input-field w-full" :placeholder="$t('admin.modals.pricePlaceholder')" />
          </div>
          <div class="flex items-center">
            <input v-model="materialForm.is_active" type="checkbox" id="is_active" class="mr-2" />
            <label for="is_active" class="text-sm text-gray-700 dark:text-gray-300">{{ $t('admin.modals.active') }}</label>
          </div>
        </div>
        <div class="flex justify-end space-x-4 mt-6">
          <button type="button" @click="showMaterialModal = false" class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
            {{ $t('admin.modals.cancel') }}
          </button>
          <button type="button" @click="saveMaterial" class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors">
            {{ editingMaterial ? $t('admin.modals.update') : $t('admin.modals.create') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Shipping Modal -->
    <div v-if="showShippingModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-dark-surface rounded-xl p-6 max-w-md w-full mx-4">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100">
            {{ editingShipping ? $t('admin.modals.editShipping') : $t('admin.modals.addShipping') }}
          </h3>
          <button @click="showShippingModal = false" class="text-gray-400 hover:text-gray-500">
            <span class="sr-only">{{ $t('common.close') }}</span>
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ $t('admin.materials.columns.name') }}</label>
            <input v-model="shippingForm.name" type="text" class="input-field w-full" :placeholder="$t('admin.modals.namePlaceholder')" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ $t('admin.shipping.type') }}</label>
            <select v-model="shippingForm.type" class="input-field w-full">
              <option v-for="t in shippingTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ $t('admin.shipping.baseFee') }} (TWD)</label>
            <input v-model="shippingForm.base_fee" type="number" step="0.01" class="input-field w-full" :placeholder="$t('admin.modals.feePlaceholder')" />
          </div>
          <div class="flex items-center">
            <input v-model="shippingForm.is_active" type="checkbox" id="shipping_is_active" class="mr-2" />
            <label for="shipping_is_active" class="text-sm text-gray-700 dark:text-gray-300">{{ $t('admin.modals.active') }}</label>
          </div>
        </div>
        <div class="flex justify-end space-x-4 mt-6">
          <button type="button" @click="showShippingModal = false" class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors">
            {{ $t('admin.modals.cancel') }}
          </button>
          <button type="button" @click="saveShipping" class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors">
            {{ editingShipping ? $t('admin.modals.update') : $t('admin.modals.create') }}
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

    <!-- Order Detail Modal -->
    <div v-if="showOrderDetailModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white dark:bg-dark-surface rounded-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div class="sticky top-0 bg-white dark:bg-dark-surface border-b border-gray-200 dark:border-gray-700 p-6 flex justify-between items-center">
          <h3 class="text-2xl font-bold text-gray-900 dark:text-white">
            {{ $t('admin.orders.orderDetails') }} #{{ selectedOrder?.id?.slice(0, 8) }}
          </h3>
          <button @click="showOrderDetailModal = false" class="text-gray-400 hover:text-gray-500">
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <div v-if="selectedOrder" class="p-6 space-y-6">
          <!-- Order Info -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="space-y-3">
              <h4 class="font-semibold text-gray-900 dark:text-white text-lg">{{ $t('admin.orders.orderInfo') }}</h4>
              <div class="space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-gray-600 dark:text-gray-400">{{ $t('admin.orders.columns.id') }}:</span>
                  <span class="text-gray-900 dark:text-white font-mono">#{{ selectedOrder.id?.slice(0, 8) }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600 dark:text-gray-400">{{ $t('admin.orders.columns.status') }}:</span>
                  <span :class="['px-2 py-1 text-xs font-semibold rounded-full', getStatusColor(selectedOrder.status)]">
                    {{ selectedOrder.status }}
                  </span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600 dark:text-gray-400">{{ $t('admin.orders.creationDate') }}:</span>
                  <span class="text-gray-900 dark:text-white">{{ new Date(selectedOrder.creation_date).toLocaleString() }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600 dark:text-gray-400">{{ $t('admin.orders.columns.customer') }}:</span>
                  <span class="text-gray-900 dark:text-white">{{ selectedOrder.customer_email }}</span>
                </div>
              </div>
            </div>

            <div class="space-y-3">
              <h4 class="font-semibold text-gray-900 dark:text-white text-lg">{{ $t('admin.orders.shippingInfo') }}</h4>
              <div v-if="selectedOrder.ship_snapshot" class="space-y-2 text-sm">
                <div class="flex justify-between">
                  <span class="text-gray-600 dark:text-gray-400">{{ $t('admin.orders.shippingMethod') }}:</span>
                  <span class="text-gray-900 dark:text-white">{{ selectedOrder.ship_snapshot.shipping_name }}</span>
                </div>
                <div class="flex justify-between">
                  <span class="text-gray-600 dark:text-gray-400">{{ $t('admin.orders.shippingFee') }}:</span>
                  <span class="text-gray-900 dark:text-white">NT$ {{ selectedOrder.ship_snapshot.base_fee }}</span>
                </div>
                <div v-if="selectedOrder.ship_snapshot.address" class="mt-2">
                  <span class="text-gray-600 dark:text-gray-400">{{ $t('admin.orders.address') }}:</span>
                  <p class="text-gray-900 dark:text-white mt-1">
                    {{ selectedOrder.ship_snapshot.address.recipient_name }}<br>
                    {{ selectedOrder.ship_snapshot.address.phone }}<br>
                    {{ selectedOrder.ship_snapshot.address.address }}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- Order Items -->
          <div>
            <h4 class="font-semibold text-gray-900 dark:text-white text-lg mb-3">{{ $t('admin.orders.items') }}</h4>
            <div class="bg-gray-50 dark:bg-gray-800 rounded-lg overflow-hidden">
              <table class="w-full">
                <thead class="bg-gray-100 dark:bg-gray-700">
                  <tr>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-400 uppercase">{{ $t('admin.orders.modelName') }}</th>
                    <th class="px-4 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-400 uppercase">{{ $t('admin.orders.material') }}</th>
                    <th class="px-4 py-3 text-center text-xs font-medium text-gray-600 dark:text-gray-400 uppercase">{{ $t('admin.orders.quantity') }}</th>
                    <th class="px-4 py-3 text-right text-xs font-medium text-gray-600 dark:text-gray-400 uppercase">{{ $t('admin.orders.price') }}</th>
                    <th class="px-4 py-3 text-right text-xs font-medium text-gray-600 dark:text-gray-400 uppercase">{{ $t('admin.orders.subtotal') }}</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-gray-200 dark:divide-gray-700">
                  <tr v-for="item in selectedOrder.items" :key="item.id" class="text-sm">
                    <td class="px-4 py-3 text-gray-900 dark:text-white">{{ item.model_name }}</td>
                    <td class="px-4 py-3 text-gray-600 dark:text-gray-400">{{ item.material_name }}</td>
                    <td class="px-4 py-3 text-center text-gray-900 dark:text-white">{{ item.quantity }}</td>
                    <td class="px-4 py-3 text-right text-gray-900 dark:text-white">NT$ {{ item.price_snapshot }}</td>
                    <td class="px-4 py-3 text-right font-medium text-gray-900 dark:text-white">NT$ {{ item.subtotal }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Order Total -->
          <div class="border-t border-gray-200 dark:border-gray-700 pt-4">
            <div class="flex justify-between items-center">
              <span class="text-xl font-bold text-gray-900 dark:text-white">{{ $t('admin.orders.total') }}</span>
              <span class="text-2xl font-bold text-primary-600 dark:text-primary-400">NT$ {{ selectedOrder.total_price }}</span>
            </div>
          </div>

          <!-- Notes -->
          <div v-if="selectedOrder.notes" class="border-t border-gray-200 dark:border-gray-700 pt-4">
            <h4 class="font-semibold text-gray-900 dark:text-white mb-2">{{ $t('admin.orders.notes') }}</h4>
            <p class="text-gray-600 dark:text-gray-400 text-sm">{{ selectedOrder.notes }}</p>
          </div>

          <!-- Actions -->
          <div class="border-t border-gray-200 dark:border-gray-700 pt-6 flex justify-end space-x-3">
            <button
              v-if="selectedOrder.status === 'PENDING'"
              @click="updateOrderStatus(selectedOrder.id, 'PROCESSING'); showOrderDetailModal = false"
              class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
            >
              {{ $t('admin.orders.process') }}
            </button>
            <button
              v-if="selectedOrder.status === 'PENDING' || selectedOrder.status === 'PROCESSING'"
              @click="updateOrderStatus(selectedOrder.id, 'SHIPPED'); showOrderDetailModal = false"
              class="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors"
            >
              {{ $t('admin.orders.ship') }}
            </button>
            <button
              v-if="selectedOrder.status === 'SHIPPED'"
              @click="updateOrderStatus(selectedOrder.id, 'DELIVERED'); showOrderDetailModal = false"
              class="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg text-sm font-medium transition-colors"
            >
              {{ $t('admin.orders.deliver') }}
            </button>
            <button
              @click="showOrderDetailModal = false"
              class="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg text-sm font-medium transition-colors"
            >
              {{ $t('common.close') }}
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

    <!-- Slicing Edit Modal -->
    <div v-if="showSlicingEditModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-dark-surface rounded-xl p-6 max-w-md w-full mx-4">
        <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-4">
          {{ $t('admin.models.editSlicingTitle') || 'Edit Slicing Info' }}
        </h3>
        <p class="mb-4 text-gray-600 dark:text-gray-300">
          {{ editingSlicingModel?.model_name }}
        </p>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ $t('admin.models.filamentMm') || 'Filament Used (mm)' }}
            </label>
            <input
              v-model="slicingForm.filament_used_mm"
              type="number"
              step="0.01"
              min="0"
              class="input-field w-full"
              placeholder="e.g. 4479.14"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ $t('admin.models.filamentCm3') || 'Filament Used (cm³)' }}
            </label>
            <input
              v-model="slicingForm.filament_used_cm3"
              type="number"
              step="0.01"
              min="0"
              class="input-field w-full"
              placeholder="e.g. 10.77"
            />
          </div>
          <p class="text-xs text-gray-500 dark:text-gray-400">
            {{ $t('admin.models.slicingHint') || 'Enter at least one value. This will be marked as manual input.' }}
          </p>
        </div>
        <div class="flex justify-end space-x-4 mt-6">
          <button
            @click="showSlicingEditModal = false"
            class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            {{ $t('common.cancel') }}
          </button>
          <button
            @click="saveSlicingInfo"
            class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
          >
            {{ $t('common.save') }}
          </button>
        </div>
      </div>
    </div>


    <div v-if="showGlobalDiscountModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-dark-surface rounded-xl p-6 max-w-md w-full mx-4">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100">
            {{ editingGlobalDiscount ? 'Edit Global Discount' : 'Add Global Discount' }}
          </h3>
          <button @click="showGlobalDiscountModal = false" class="text-gray-400 hover:text-gray-500">
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
            <input v-model="globalDiscountForm.name" type="text" class="input-field w-full" placeholder="e.g., Summer Sale" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Type</label>
              <select v-model="globalDiscountForm.discount_type" class="input-field w-full">
                <option v-for="t in discountTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Value</label>
              <input v-model="globalDiscountForm.discount_value" type="number" step="0.01" class="input-field w-full" placeholder="10" />
              <div v-if="globalDiscountWarnings.length > 0" class="mt-2 space-y-1">
                <p v-for="(warning, idx) in globalDiscountWarnings" :key="idx" 
                   :class="[
                     'text-xs flex items-start gap-1',
                     warning.type === 'error' ? 'text-red-500 dark:text-red-400' :
                     warning.type === 'info' ? 'text-amber-500 dark:text-amber-400' :
                     'text-blue-500 dark:text-blue-400'
                   ]">
                  <span>{{ warning.icon }}</span>
                  <span>{{ warning.message }}</span>
                </p>
              </div>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Min Order Amount (optional)</label>
            <input v-model="globalDiscountForm.min_order_amount" type="number" step="0.01" class="input-field w-full" placeholder="100" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Start Date</label>
              <input v-model="globalDiscountForm.start_date" type="date" class="input-field w-full" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">End Date</label>
              <input v-model="globalDiscountForm.end_date" type="date" class="input-field w-full" />
            </div>
          </div>
          <div class="flex items-center">
            <input v-model="globalDiscountForm.is_active" type="checkbox" id="discount_is_active" class="mr-2" />
            <label for="discount_is_active" class="text-sm text-gray-700 dark:text-gray-300">Active</label>
          </div>
        </div>
        <div class="flex justify-end space-x-4 mt-6">
          <button @click="showGlobalDiscountModal = false" class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">Cancel</button>
          <button @click="saveGlobalDiscount" class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg">
            {{ editingGlobalDiscount ? 'Update' : 'Create' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Coupon Modal -->
    <div v-if="showCouponModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-dark-surface rounded-xl p-6 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100">
            {{ editingCoupon ? 'Edit Coupon' : 'Add Coupon' }}
          </h3>
          <button @click="showCouponModal = false" class="text-gray-400 hover:text-gray-500">
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
            <input v-model="couponForm.name" type="text" class="input-field w-full" placeholder="e.g., Welcome Discount" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Code</label>
            <input v-model="couponForm.code" type="text" class="input-field w-full font-mono uppercase" placeholder="WELCOME10" :disabled="editingCoupon" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Type</label>
              <select v-model="couponForm.discount_type" class="input-field w-full">
                <option v-for="t in discountTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Value</label>
              <input v-model="couponForm.discount_value" type="number" step="0.01" class="input-field w-full" placeholder="10" />
              <div v-if="couponWarnings.length > 0" class="mt-2 space-y-1">
                <p v-for="(warning, idx) in couponWarnings" :key="idx" 
                   :class="[
                     'text-xs flex items-start gap-1',
                     warning.type === 'error' ? 'text-red-500 dark:text-red-400' :
                     warning.type === 'info' ? 'text-amber-500 dark:text-amber-400' :
                     'text-blue-500 dark:text-blue-400'
                   ]">
                  <span>{{ warning.icon }}</span>
                  <span>{{ warning.message }}</span>
                </p>
              </div>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Min Order (optional)</label>
              <input v-model="couponForm.min_order_amount" type="number" step="0.01" class="input-field w-full" placeholder="100" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Max Uses (optional)</label>
              <input v-model="couponForm.max_uses" type="number" class="input-field w-full" placeholder="100" />
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Start Date</label>
              <input v-model="couponForm.start_date" type="date" class="input-field w-full" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">End Date</label>
              <input v-model="couponForm.end_date" type="date" class="input-field w-full" />
            </div>
          </div>
          <div class="flex items-center">
            <input v-model="couponForm.is_active" type="checkbox" id="coupon_is_active" class="mr-2" />
            <label for="coupon_is_active" class="text-sm text-gray-700 dark:text-gray-300">Active</label>
          </div>
        </div>
        <div class="flex justify-end space-x-4 mt-6">
          <button @click="showCouponModal = false" class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">Cancel</button>
          <button @click="saveCoupon" class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg">
            {{ editingCoupon ? 'Update' : 'Create' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Employee Modal -->
    <div v-if="showEmployeeModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div class="bg-white dark:bg-dark-surface rounded-xl p-6 max-w-md w-full mx-4">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-medium text-gray-900 dark:text-gray-100">
            {{ editingEmployee ? 'Edit Employee' : 'Add Employee' }}
          </h3>
          <button @click="showEmployeeModal = false" class="text-gray-400 hover:text-gray-500">
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
            <input v-model="employeeForm.email" type="email" class="input-field w-full" placeholder="employee@example.com" :disabled="editingEmployee" />
          </div>
          <div v-if="!editingEmployee">
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Password</label>
            <input v-model="employeeForm.password" type="password" class="input-field w-full" placeholder="Minimum 8 characters" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Employee Name</label>
            <input v-model="employeeForm.employee_name" type="text" class="input-field w-full" placeholder="John Doe" />
          </div>
          <div class="flex items-center">
            <input v-model="employeeForm.is_admin" type="checkbox" id="employee_is_admin" class="mr-2" />
            <label for="employee_is_admin" class="text-sm text-gray-700 dark:text-gray-300">Administrator (full access)</label>
          </div>
        </div>
        <div class="flex justify-end space-x-4 mt-6">
          <button @click="showEmployeeModal = false" class="px-4 py-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">Cancel</button>
          <button @click="saveEmployee" class="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg">
            {{ editingEmployee ? 'Update' : 'Create' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

