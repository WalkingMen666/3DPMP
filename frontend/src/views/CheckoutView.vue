<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCartStore } from '../stores/cart'
import { useAuthStore } from '../stores/auth'
import axios from 'axios'

const router = useRouter()
const cart = useCartStore()
const auth = useAuthStore()

const loading = ref(false)
const error = ref('')
const success = ref(false)

// Shipping options and addresses
const shippingOptions = ref([])
const savedAddresses = ref([])
const selectedShipping = ref(null)
const selectedAddress = ref(null)
const orderNotes = ref('')

// Coupon and discounts
const couponCode = ref('')
const couponLoading = ref(false)
const couponError = ref('')
const appliedCoupon = ref(null)
const globalDiscounts = ref([])

// New address form
const showAddressForm = ref(false)
const newAddress = ref({
  name: '',
  address_type: 'HOME_DELIVERY',
  address_details: ''
})

const addressTypes = [
  { value: 'HOME_DELIVERY', label: 'checkout.addressTypes.HOME_DELIVERY' },
  { value: 'CONVENIENCE_STORE', label: 'checkout.addressTypes.CONVENIENCE_STORE' },
  { value: 'SELF_PICKUP', label: 'checkout.addressTypes.SELF_PICKUP' }
]

// API client
const apiClient = axios.create({ baseURL: '/api' })
apiClient.interceptors.request.use(config => {
  if (auth.token) {
    config.headers.Authorization = `Token ${auth.token}`
  }
  return config
})

// Fetch data on mount
onMounted(async () => {
  if (!auth.isAuthenticated) {
    router.push('/login')
    return
  }

  await Promise.all([
    fetchShippingOptions(),
    fetchSavedAddresses(),
    fetchGlobalDiscounts(),
    cart.fetchCart()
  ])

  // Redirect if cart is empty
  if (cart.items.length === 0) {
    router.push('/cart')
  }
})

const fetchShippingOptions = async () => {
  try {
    const response = await apiClient.get('/shipping/options/')
    shippingOptions.value = response.data || []
    if (shippingOptions.value.length > 0) {
      selectedShipping.value = shippingOptions.value[0].id
    }
  } catch (err) {
    console.error('Failed to fetch shipping options:', err)
  }
}

const fetchSavedAddresses = async () => {
  try {
    const response = await apiClient.get('/shipping/addresses/')
    savedAddresses.value = response.data || []
    if (savedAddresses.value.length > 0) {
      selectedAddress.value = savedAddresses.value[0].id
    }
  } catch (err) {
    console.error('Failed to fetch addresses:', err)
  }
}

const fetchGlobalDiscounts = async () => {
  try {
    const response = await apiClient.get('/discounts/active/')
    globalDiscounts.value = response.data || []
  } catch (err) {
    // Global discounts endpoint might not exist yet, ignore error
    globalDiscounts.value = []
  }
}

const applyCoupon = async () => {
  if (!couponCode.value.trim()) {
    couponError.value = 'Please enter a coupon code'
    return
  }

  couponLoading.value = true
  couponError.value = ''

  try {
    const response = await apiClient.post('/discounts/coupons/validate/', {
      code: couponCode.value.trim().toUpperCase()
    })

    if (response.data.valid) {
      appliedCoupon.value = response.data.coupon
      couponError.value = ''
    } else {
      couponError.value = response.data.error || 'Invalid coupon code'
      appliedCoupon.value = null
    }
  } catch (err) {
    couponError.value = err.response?.data?.error || 'Invalid coupon code'
    appliedCoupon.value = null
  } finally {
    couponLoading.value = false
  }
}

const removeCoupon = () => {
  appliedCoupon.value = null
  couponCode.value = ''
  couponError.value = ''
}

const saveNewAddress = async () => {
  if (!newAddress.value.name || !newAddress.value.address_details) {
    error.value = 'checkout.errors.addressFieldsRequired'
    return
  }

  try {
    const response = await apiClient.post('/shipping/addresses/', newAddress.value)
    savedAddresses.value.push(response.data)
    selectedAddress.value = response.data.id
    showAddressForm.value = false
    newAddress.value = { name: '', address_type: 'HOME_DELIVERY', address_details: '' }
    error.value = ''
  } catch (err) {
    error.value = 'checkout.errors.saveAddressFailed'
  }
}

const selectedShippingOption = computed(() => {
  return shippingOptions.value.find(o => o.id === selectedShipping.value)
})

const shippingFee = computed(() => {
  return selectedShippingOption.value ? parseFloat(selectedShippingOption.value.base_fee) : 0
})

// Calculate discount from coupon
const couponDiscount = computed(() => {
  if (!appliedCoupon.value) return 0

  const subtotal = cart.subtotal
  const minOrder = parseFloat(appliedCoupon.value.min_order_amount) || 0

  if (subtotal < minOrder) return 0

  if (appliedCoupon.value.discount_type === 'PERCENTAGE') {
    return subtotal * (parseFloat(appliedCoupon.value.discount_value) / 100)
  } else {
    return Math.min(parseFloat(appliedCoupon.value.discount_value), subtotal)
  }
})

// Calculate discount from global discounts (auto-applied)
const globalDiscountTotal = computed(() => {
  let discount = 0
  const subtotal = cart.subtotal

  for (const gd of globalDiscounts.value) {
    const minOrder = parseFloat(gd.min_order_amount) || 0
    if (subtotal < minOrder) continue

    if (gd.discount_type === 'PERCENTAGE') {
      discount += subtotal * (parseFloat(gd.discount_value) / 100)
    } else {
      discount += parseFloat(gd.discount_value)
    }
  }

  return Math.min(discount, subtotal)
})

const totalDiscount = computed(() => {
  return couponDiscount.value + globalDiscountTotal.value
})

const orderTotal = computed(() => {
  return Math.max(0, cart.subtotal - totalDiscount.value + shippingFee.value)
})

// Filter addresses by selected shipping type
const compatibleAddresses = computed(() => {
  if (!selectedShippingOption.value) return savedAddresses.value

  return savedAddresses.value.filter(addr =>
    addr.address_type === selectedShippingOption.value.type
  )
})

// Auto-select compatible address when shipping changes
const updateSelectedShipping = (value) => {
  selectedShipping.value = value

  // Check if current address is compatible
  const currentAddr = savedAddresses.value.find(a => a.id === selectedAddress.value)
  if (currentAddr && currentAddr.address_type !== selectedShippingOption.value?.type) {
    // Auto-select first compatible address
    if (compatibleAddresses.value.length > 0) {
      selectedAddress.value = compatibleAddresses.value[0].id
    } else {
      selectedAddress.value = null
    }
  }
}

const placeOrder = async () => {
  if (!selectedShipping.value) {
    error.value = 'checkout.errors.selectShipping'
    return
  }
  if (!selectedAddress.value) {
    error.value = 'checkout.errors.selectAddress'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const orderData = {
      shipping_option_id: selectedShipping.value,
      saved_address_id: selectedAddress.value,
      notes: orderNotes.value
    }

    // Include coupon code if applied
    if (appliedCoupon.value) {
      orderData.coupon_code = appliedCoupon.value.code
    }

    await apiClient.post('/orders/', orderData)

    success.value = true
    cart.clearCart()

    // Redirect to dashboard after 2 seconds
    setTimeout(() => {
      router.push('/dashboard')
    }, 2000)
  } catch (err) {
    error.value = err.response?.data?.detail || err.response?.data?.[0] || 'checkout.errors.placeOrderFailed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-8">{{ $t('checkout.title') }}</h1>

    <!-- Success Message -->
    <div v-if="success" class="text-center py-12 bg-green-50 dark:bg-green-900/20 rounded-xl border border-green-200 dark:border-green-800">
      <svg class="mx-auto h-16 w-16 text-green-500 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <h2 class="text-2xl font-bold text-green-700 dark:text-green-400 mb-2">{{ $t('checkout.success.title') }}</h2>
      <p class="text-green-600 dark:text-green-300">{{ $t('checkout.success.message') }}</p>
    </div>

    <div v-else class="space-y-8">
      <!-- Error Message -->
      <div v-if="error" class="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 rounded-lg">
        {{ error.startsWith('checkout.') ? $t(error) : error }}
      </div>

      <!-- Shipping Options -->
      <div class="bg-white dark:bg-dark-surface rounded-xl p-6 border border-gray-100 dark:border-gray-700/50">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-4">{{ $t('checkout.shipping.title') }}</h2>

        <div v-if="shippingOptions.length === 0" class="text-gray-500 dark:text-gray-400">
          {{ $t('checkout.shipping.noOptions') }}
        </div>

        <div v-else class="space-y-3">
          <label
            v-for="option in shippingOptions"
            :key="option.id"
            class="flex items-center p-4 border rounded-lg cursor-pointer transition-colors"
            :class="selectedShipping === option.id
              ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
              : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'"
          >
            <input
              type="radio"
              :value="option.id"
              :checked="selectedShipping === option.id"
              @change="updateSelectedShipping(option.id)"
              class="mr-3"
            />
            <div class="flex-1">
              <div class="font-medium text-gray-900 dark:text-white">{{ option.name }}</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">{{ $t(`checkout.addressTypes.${option.type}`) }}</div>
            </div>
            <div class="font-bold text-gray-900 dark:text-white">NT$ {{ option.base_fee }}</div>
          </label>
        </div>
      </div>

      <!-- Delivery Address -->
      <div class="bg-white dark:bg-dark-surface rounded-xl p-6 border border-gray-100 dark:border-gray-700/50">
        <div class="flex justify-between items-center mb-4">
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">{{ $t('checkout.address.title') }}</h2>
          <button
            @click="showAddressForm = !showAddressForm"
            class="text-primary-600 hover:text-primary-700 text-sm font-medium"
          >
            {{ showAddressForm ? $t('checkout.address.cancel') : $t('checkout.address.addNew') }}
          </button>
        </div>

        <!-- New Address Form -->
        <div v-if="showAddressForm" class="mb-6 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ $t('checkout.address.form.name') }}</label>
            <input v-model="newAddress.name" type="text" class="input-field w-full" :placeholder="$t('checkout.address.form.namePlaceholder')" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ $t('checkout.address.form.type') }}</label>
            <select v-model="newAddress.address_type" class="input-field w-full">
              <option v-for="t in addressTypes" :key="t.value" :value="t.value">{{ $t(t.label) }}</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{{ $t('checkout.address.form.details') }}</label>
            <textarea v-model="newAddress.address_details" class="input-field w-full" rows="3" :placeholder="$t('checkout.address.form.detailsPlaceholder')"></textarea>
          </div>
          <button @click="saveNewAddress" class="btn-primary py-2">{{ $t('checkout.address.form.save') }}</button>
        </div>

        <!-- Compatible Addresses Warning -->
        <div v-if="selectedShippingOption && compatibleAddresses.length === 0 && savedAddresses.length > 0" class="mb-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
          <p class="text-sm text-yellow-800 dark:text-yellow-200">
            {{ $t('checkout.address.noCompatibleAddressWarning', { type: $t(`checkout.addressTypes.${selectedShippingOption.type}`) }) }}
          </p>
        </div>

        <!-- Saved Addresses -->
        <div v-if="savedAddresses.length === 0 && !showAddressForm" class="text-gray-500 dark:text-gray-400">
          {{ $t('checkout.address.noAddresses') }}
        </div>

        <div v-else-if="compatibleAddresses.length > 0" class="space-y-3">
          <label
            v-for="address in compatibleAddresses"
            :key="address.id"
            class="flex items-start p-4 border rounded-lg cursor-pointer transition-colors"
            :class="selectedAddress === address.id
              ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
              : 'border-gray-200 dark:border-gray-700 hover:border-gray-300'"
          >
            <input
              type="radio"
              :value="address.id"
              v-model="selectedAddress"
              class="mr-3 mt-1"
            />
            <div>
              <div class="font-medium text-gray-900 dark:text-white">{{ address.name }}</div>
              <div class="text-sm text-gray-500 dark:text-gray-400">{{ $t(`checkout.addressTypes.${address.address_type}`) }}</div>
              <div class="text-sm text-gray-600 dark:text-gray-300 mt-1">{{ address.address_details }}</div>
            </div>
          </label>
        </div>
      </div>

      <!-- Order Notes -->
      <div class="bg-white dark:bg-dark-surface rounded-xl p-6 border border-gray-100 dark:border-gray-700/50">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-4">{{ $t('checkout.notes.title') }}</h2>
        <textarea
          v-model="orderNotes"
          class="input-field w-full"
          rows="3"
          :placeholder="$t('checkout.notes.placeholder')"
        ></textarea>
      </div>

      <!-- Coupon Code -->
      <div class="bg-white dark:bg-dark-surface rounded-xl p-6 border border-gray-100 dark:border-gray-700/50">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-4">{{ $t('checkout.coupon.title') }}</h2>

        <!-- Applied Coupon -->
        <div v-if="appliedCoupon" class="flex items-center justify-between p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
          <div class="flex items-center space-x-3">
            <svg class="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <div class="font-medium text-green-800 dark:text-green-300">{{ appliedCoupon.code }}</div>
              <div class="text-sm text-green-600 dark:text-green-400">
                {{ appliedCoupon.discount_type === 'PERCENTAGE'
                  ? `${appliedCoupon.discount_value}% ${$t('checkout.coupon.off')}`
                  : `NT$ ${appliedCoupon.discount_value} ${$t('checkout.coupon.off')}` }}
              </div>
            </div>
          </div>
          <button @click="removeCoupon" class="text-red-500 hover:text-red-700">
            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Coupon Input -->
        <div v-else class="space-y-3">
          <div class="flex space-x-3">
            <input
              v-model="couponCode"
              type="text"
              class="input-field flex-1"
              :placeholder="$t('checkout.coupon.placeholder')"
              @keyup.enter="applyCoupon"
            />
            <button
              @click="applyCoupon"
              :disabled="couponLoading || !couponCode.trim()"
              class="btn-secondary px-6 disabled:opacity-50"
            >
              <span v-if="couponLoading">...</span>
              <span v-else>{{ $t('checkout.coupon.apply') }}</span>
            </button>
          </div>
          <p v-if="couponError" class="text-sm text-red-500">{{ couponError }}</p>
        </div>

        <!-- Active Global Discounts Info -->
        <div v-if="globalDiscounts.length > 0" class="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div class="text-sm text-gray-600 dark:text-gray-400 mb-2">{{ $t('checkout.coupon.autoApplied') }}:</div>
          <div class="space-y-2">
            <div v-for="gd in globalDiscounts" :key="gd.id" class="flex items-center space-x-2 text-sm">
              <svg class="w-4 h-4 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              <span class="text-gray-700 dark:text-gray-300">
                {{ gd.name }}
                <span class="text-primary-600 dark:text-primary-400">
                  ({{ gd.discount_type === 'PERCENTAGE'
                    ? `-${gd.discount_value}%`
                    : `-NT$ ${gd.discount_value}` }})
                </span>
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Order Summary -->
      <div class="bg-white dark:bg-dark-surface rounded-xl p-6 border border-gray-100 dark:border-gray-700/50">
        <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-4">{{ $t('checkout.summary.title') }}</h2>

        <div class="space-y-3 mb-6">
          <div v-for="item in cart.items" :key="item.id" class="flex justify-between text-gray-600 dark:text-gray-400">
            <span>{{ item.name }} x {{ item.quantity }}</span>
            <span>NT$ {{ (item.price * item.quantity).toFixed(2) }}</span>
          </div>
        </div>

        <div class="space-y-2 pt-4 border-t border-gray-100 dark:border-gray-700">
          <div class="flex justify-between text-gray-600 dark:text-gray-400">
            <span>{{ $t('checkout.summary.subtotal') }}</span>
            <span>NT$ {{ cart.subtotal.toFixed(2) }}</span>
          </div>

          <!-- Global Discounts -->
          <div v-if="globalDiscountTotal > 0" class="flex justify-between text-green-600 dark:text-green-400">
            <span>{{ $t('checkout.summary.globalDiscount') }}</span>
            <span>- NT$ {{ globalDiscountTotal.toFixed(2) }}</span>
          </div>

          <!-- Coupon Discount -->
          <div v-if="couponDiscount > 0" class="flex justify-between text-green-600 dark:text-green-400">
            <span>{{ $t('checkout.summary.couponDiscount') }} ({{ appliedCoupon?.code }})</span>
            <span>- NT$ {{ couponDiscount.toFixed(2) }}</span>
          </div>

          <div class="flex justify-between text-gray-600 dark:text-gray-400">
            <span>{{ $t('checkout.summary.shipping') }}</span>
            <span>NT$ {{ shippingFee.toFixed(2) }}</span>
          </div>
          <div class="flex justify-between font-bold text-lg text-gray-900 dark:text-white pt-2">
            <span>{{ $t('checkout.summary.total') }}</span>
            <span>NT$ {{ orderTotal.toFixed(2) }}</span>
          </div>
        </div>
      </div>

      <!-- Place Order Button -->
      <button
        @click="placeOrder"
        :disabled="loading || cart.items.length === 0 || !selectedShipping || !selectedAddress"
        class="w-full btn-primary py-4 text-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <span v-if="loading">{{ $t('checkout.processing') }}</span>
        <span v-else>{{ $t('checkout.placeOrder') }}</span>
      </button>
    </div>
  </div>
</template>
