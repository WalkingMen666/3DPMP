<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { useRoute } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { useCartStore } from "../stores/cart";
import { useOrdersStore } from "../stores/orders";
import { useModelsStore } from "../stores/models";

const route = useRoute();
const auth = useAuthStore();
const cart = useCartStore();
const ordersStore = useOrdersStore();
const modelsStore = useModelsStore();
const activeTab = ref("overview");
const loading = ref(true);
const deletingModel = ref(null);
const submittingForReview = ref(null);

// Avatar state
const avatarChoices = ref([]);
const selectedAvatar = ref(auth.user?.avatar_type || 'default');
const customAvatarFile = ref(null);
const customAvatarPreview = ref(null);
const savingAvatar = ref(false);
const avatarFileInput = ref(null);

// Check for tab from route
onMounted(async () => {
  if (route.meta.tab) {
    activeTab.value = route.meta.tab;
  }
  displayName.value = auth.user?.name || "";
  selectedAvatar.value = auth.user?.avatar_type || 'default';
  
  // Fetch real data from backend
  loading.value = true;
  try {
    await Promise.all([
      ordersStore.fetchOrders(),
      modelsStore.fetchMyModels(),
      auth.fetchAvatarChoices()
    ]);
    avatarChoices.value = auth.avatarChoices;
  } catch (error) {
    // Silently fail - stores handle their own errors
  } finally {
    loading.value = false;
  }
});

// Watch for route changes
watch(
  () => route.meta.tab,
  (newTab) => {
    if (newTab) {
      activeTab.value = newTab;
    }
  }
);

const tabs = [
  {
    id: "overview",
    name: "Overview",
    icon: "M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z",
  },
  {
    id: "orders",
    name: "My Orders",
    icon: "M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z",
  },
  {
    id: "models",
    name: "My Models",
    icon: "M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10",
  },
  {
    id: "settings",
    name: "Settings",
    icon: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z",
  },
];

// Real data - from stores
const orders = computed(() => ordersStore.orders);
const myModels = computed(() => modelsStore.myModels);

// Computed stats based on actual data
const stats = computed(() => ({
  totalOrders: orders.value.length,
  modelsUploaded: myModels.value.length,
  balance: "$0.00",
}));

// Helper to get model thumbnail
const getModelThumbnail = (model) => {
  if (model.thumbnail_url) return model.thumbnail_url;
  if (model.thumbnail) return model.thumbnail;
  if (model.images && model.images.length > 0) {
    const img = model.images[0];
    return img.url || img.image_url || img.image || null;
  }
  return null;
};

// Delete model
const deleteModel = async (modelId) => {
  if (!confirm('Are you sure you want to delete this model? This action cannot be undone.')) {
    return;
  }
  
  deletingModel.value = modelId;
  try {
    await modelsStore.deleteModel(modelId);
  } catch (error) {
    alert(error.message || 'Failed to delete model');
  } finally {
    deletingModel.value = null;
  }
};

// Submit model for public review
const submitForReview = async (modelId) => {
  if (!confirm('Submit this model for public review? An admin will review and approve it for the marketplace.')) {
    return;
  }
  
  submittingForReview.value = modelId;
  try {
    await modelsStore.submitForReview(modelId);
    alert('Model submitted for review successfully!');
  } catch (error) {
    alert(error.message || 'Failed to submit for review');
  } finally {
    submittingForReview.value = null;
  }
};

// Show rejection reason
const showRejectionReason = async (model) => {
  try {
    const logs = await modelsStore.fetchReviewLogs(model.id);
    console.log('Review logs:', logs); // Debug log
    const rejectionLog = logs.find(log => log.new_status === 'REJECTED');
    if (rejectionLog) {
      alert(`Rejection Reason:\n\n${rejectionLog.reason || 'No reason provided'}\n\nReviewed by: ${rejectionLog.reviewer_name || 'Unknown'}\nDate: ${new Date(rejectionLog.timestamp).toLocaleString()}`);
    } else {
      alert('No rejection details found.');
    }
  } catch (error) {
    console.error('Failed to load rejection details:', error);
    alert('Failed to load rejection details.');
  }
};

// Settings state - load from localStorage
const displayName = ref(auth.user?.name || "");
const settings = ref({
  emailNotifications: JSON.parse(
    localStorage.getItem("settings_emailNotifications") ?? "true"
  ),
  marketingEmails: JSON.parse(
    localStorage.getItem("settings_marketingEmails") ?? "false"
  ),
  language: localStorage.getItem("settings_language") || "en",
});
const settingsSaved = ref(false);

// Watch for settings changes and persist
watch(
  () => settings.value.emailNotifications,
  (val) => {
    localStorage.setItem("settings_emailNotifications", JSON.stringify(val));
  }
);
watch(
  () => settings.value.marketingEmails,
  (val) => {
    localStorage.setItem("settings_marketingEmails", JSON.stringify(val));
  }
);
watch(
  () => settings.value.language,
  (val) => {
    localStorage.setItem("settings_language", val);
  }
);

const saveSettings = async () => {
  // Update display name in backend
  if (displayName.value !== (auth.user?.display_name || '')) {
    try {
      await auth.updateProfile(displayName.value);
    } catch (error) {
      alert(error.message || 'Failed to save display name');
      return;
    }
  }

  // Show success feedback
  settingsSaved.value = true;
  setTimeout(() => {
    settingsSaved.value = false;
  }, 3000);
};

const cancelOrder = async (orderId) => {
  if (confirm('Are you sure you want to cancel this order?')) {
    try {
      await ordersStore.cancelOrder(orderId);
    } catch (error) {
      alert(error.message);
    }
  }
};

// Avatar functions
const handleAvatarSelect = (avatarId) => {
  selectedAvatar.value = avatarId;
  if (avatarId !== 'custom') {
    customAvatarFile.value = null;
    customAvatarPreview.value = null;
  }
};

const triggerFileInput = () => {
  avatarFileInput.value?.click();
};

const handleCustomAvatarUpload = (event) => {
  const file = event.target.files[0];
  if (file) {
    if (!file.type.startsWith('image/')) {
      alert('Please upload an image file');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      alert('Image size should be less than 5MB');
      return;
    }
    customAvatarFile.value = file;
    customAvatarPreview.value = URL.createObjectURL(file);
    selectedAvatar.value = 'custom';
  }
};

const saveAvatar = async () => {
  savingAvatar.value = true;
  try {
    await auth.updateAvatar(selectedAvatar.value, customAvatarFile.value);
    settingsSaved.value = true;
    setTimeout(() => {
      settingsSaved.value = false;
    }, 3000);
  } catch (error) {
    alert(error.message || 'Failed to update avatar');
  } finally {
    savingAvatar.value = false;
  }
};

const getAvatarDisplayUrl = (avatarId) => {
  if (avatarId === 'default') {
    return `https://api.dicebear.com/7.x/avataaars/svg?seed=${auth.user?.email}`;
  }
  // For custom avatars, we show the uploaded image
  if (avatarId === 'custom' && customAvatarPreview.value) {
    return customAvatarPreview.value;
  }
  return auth.user?.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${auth.user?.email}`;
};
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <div class="flex flex-col md:flex-row gap-8">
      <!-- Sidebar -->
      <div class="w-full md:w-64 flex-shrink-0">
        <div
          class="bg-white dark:bg-dark-surface rounded-xl shadow-sm border border-gray-100 dark:border-gray-700/50 overflow-hidden"
        >
          <div class="p-6 border-b border-gray-100 dark:border-gray-700">
            <div class="flex items-center space-x-3">
              <img :src="auth.user?.avatar" class="w-12 h-12 rounded-full" />
              <div>
                <div class="font-bold text-gray-900 dark:text-white">
                  {{ auth.user?.name }}
                </div>
                <div
                  class="text-sm text-gray-500 dark:text-gray-400 capitalize"
                >
                  {{ auth.user?.role }}
                </div>
              </div>
            </div>
          </div>
          <nav class="p-2">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              :class="[
                'w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors text-sm font-medium',
                activeTab === tab.id
                  ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800',
              ]"
            >
              <svg
                class="w-5 h-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  :d="tab.icon"
                />
              </svg>
              <span>{{ tab.name }}</span>
            </button>
          </nav>
        </div>
      </div>

      <!-- Content -->
      <div class="flex-1">
        <!-- Overview Tab -->
        <div v-if="activeTab === 'overview'" class="space-y-6 animate-fade-in">
          <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
            Dashboard Overview
          </h2>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div class="card p-6">
              <div class="text-sm text-gray-500 dark:text-gray-400 mb-1">
                Total Orders
              </div>
              <div class="text-3xl font-bold text-gray-900 dark:text-white">
                {{ stats.totalOrders }}
              </div>
            </div>
            <div class="card p-6">
              <div class="text-sm text-gray-500 dark:text-gray-400 mb-1">
                Models Uploaded
              </div>
              <div class="text-3xl font-bold text-gray-900 dark:text-white">
                {{ stats.modelsUploaded }}
              </div>
            </div>
            <div class="card p-6">
              <div class="text-sm text-gray-500 dark:text-gray-400 mb-1">
                Balance
              </div>
              <div class="text-3xl font-bold text-gray-900 dark:text-white">
                {{ stats.balance }}
              </div>
            </div>
          </div>

          <!-- Quick Actions -->
          <div class="card p-6">
            <h3
              class="text-lg font-semibold text-gray-900 dark:text-white mb-4"
            >
              Quick Actions
            </h3>
            <div class="flex flex-wrap gap-4">
              <router-link to="/upload" class="btn-primary"
                >Upload Model</router-link
              >
              <router-link to="/models" class="btn-secondary"
                >Browse Marketplace</router-link
              >
            </div>
          </div>
        </div>

        <!-- Orders Tab -->
        <div v-if="activeTab === 'orders'" class="space-y-6 animate-fade-in">
          <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
            My Orders
          </h2>

          <div
            v-if="orders.length === 0"
            class="text-center py-12 bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50"
          >
            <svg
              class="mx-auto h-16 w-16 text-gray-300 dark:text-gray-600 mb-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="1.5"
                d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"
              />
            </svg>
            <p class="text-gray-500 dark:text-gray-400 mb-2">No orders yet</p>
            <p class="text-sm text-gray-400 dark:text-gray-500 mb-4">
              Start shopping to see your orders here
            </p>
            <router-link to="/models" class="btn-primary"
              >Browse Marketplace</router-link
            >
          </div>

          <div
            v-else
            class="bg-white dark:bg-dark-surface rounded-xl shadow-sm border border-gray-100 dark:border-gray-700/50 overflow-hidden"
          >
            <table
              class="min-w-full divide-y divide-gray-200 dark:divide-gray-700"
            >
              <thead class="bg-gray-50 dark:bg-gray-800">
                <tr>
                  <th
                    class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
                  >
                    Order ID
                  </th>
                  <th
                    class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
                  >
                    Date
                  </th>
                  <th
                    class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
                  >
                    Status
                  </th>
                  <th
                    class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
                  >
                    Total
                  </th>
                  <th
                    class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
                  >
                    Action
                  </th>
                </tr>
              </thead>
              <tbody
                class="bg-white dark:bg-dark-surface divide-y divide-gray-200 dark:divide-gray-700"
              >
                <tr v-for="order in orders" :key="order.id">
                  <td
                    class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white"
                  >
                    #{{ order.id?.slice(0, 8) || order.id }}
                  </td>
                  <td
                    class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400"
                  >
                    {{ new Date(order.creation_date).toLocaleDateString() }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span
                      :class="[
                        'px-2 inline-flex text-xs leading-5 font-semibold rounded-full',
                        order.status === 'PENDING' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' :
                        order.status === 'PROCESSING' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400' :
                        order.status === 'DELIVERED' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                        order.status === 'CANCELLED' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
                        'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400'
                      ]"
                    >
                      {{ order.status }}
                    </span>
                  </td>
                  <td
                    class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400"
                  >
                    ${{ parseFloat(order.total_price).toFixed(2) }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      v-if="order.status === 'PENDING'"
                      @click="cancelOrder(order.id)"
                      class="text-red-600 hover:text-red-900 dark:hover:text-red-400 mr-3"
                    >
                      Cancel
                    </button>
                    <a
                      href="#"
                      class="text-primary-600 hover:text-primary-900 dark:hover:text-primary-400"
                      >View</a
                    >
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Models Tab -->
        <div v-if="activeTab === 'models'" class="space-y-6 animate-fade-in">
          <div class="flex justify-between items-center">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
              My Models
            </h2>
            <router-link to="/upload" class="btn-primary text-sm"
              >Upload New Model</router-link
            >
          </div>

          <div
            v-if="myModels.length === 0"
            class="text-center py-12 bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50"
          >
            <svg
              class="mx-auto h-16 w-16 text-gray-300 dark:text-gray-600 mb-4"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="1.5"
                d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
              />
            </svg>
            <p class="text-gray-500 dark:text-gray-400 mb-2">
              No models uploaded yet
            </p>
            <p class="text-sm text-gray-400 dark:text-gray-500 mb-4">
              Share your 3D creations with the community
            </p>
            <router-link to="/upload" class="btn-primary"
              >Upload Your First Model</router-link
            >
          </div>

          <div v-else class="grid grid-cols-1 gap-4">
            <div
              v-for="model in myModels"
              :key="model.id"
              class="card p-4 flex items-center justify-between"
            >
              <div class="flex items-center space-x-4">
                <div class="w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden flex-shrink-0">
                  <img
                    v-if="getModelThumbnail(model)"
                    :src="getModelThumbnail(model)"
                    :alt="model.model_name"
                    class="w-full h-full object-cover"
                  />
                  <div v-else class="w-full h-full flex items-center justify-center text-gray-400">
                    <svg class="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                </div>
                <div>
                  <h3 class="font-semibold text-gray-900 dark:text-white">
                    {{ model.model_name || model.name }}
                  </h3>
                  <div class="text-sm text-gray-500 dark:text-gray-400">
                    {{ model.view_count || 0 }} views • {{ model.download_count || 0 }} downloads
                  </div>
                </div>
              </div>
              <div class="flex items-center space-x-3">
                <span
                  :class="[
                    'px-2 py-1 text-xs font-semibold rounded-full',
                    (model.visibility_status || model.visibility) === 'PUBLIC'
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                      : (model.visibility_status || model.visibility) === 'PENDING'
                        ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                        : (model.visibility_status || model.visibility) === 'REJECTED'
                          ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400',
                  ]"
                >
                  {{ model.visibility_status || model.visibility || 'PRIVATE' }}
                </span>
                
                <!-- Rejection reason tooltip for REJECTED models -->
                <button
                  v-if="(model.visibility_status || model.visibility) === 'REJECTED'"
                  @click="showRejectionReason(model)"
                  class="text-red-500 hover:text-red-700 text-xs underline"
                  title="View rejection reason"
                >
                  Why?
                </button>
                
                <!-- Submit for Review Button (for PRIVATE or REJECTED models) -->
                <button
                  v-if="(model.visibility_status || model.visibility) === 'PRIVATE' || (model.visibility_status || model.visibility) === 'REJECTED'"
                  @click="submitForReview(model.id)"
                  :disabled="submittingForReview === model.id"
                  class="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 text-sm font-medium disabled:opacity-50"
                  title="Submit for public review"
                >
                  <span v-if="submittingForReview === model.id">Submitting...</span>
                  <span v-else>{{ (model.visibility_status || model.visibility) === 'REJECTED' ? 'Resubmit' : 'Make Public' }}</span>
                </button>
                
                <!-- View Button -->
                <router-link
                  :to="`/model/${model.id}`"
                  class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                  title="View model"
                >
                  <svg
                    class="w-5 h-5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                    />
                  </svg>
                </router-link>
                
                <!-- Delete Button -->
                <button
                  @click="deleteModel(model.id)"
                  :disabled="deletingModel === model.id"
                  class="text-red-400 hover:text-red-600 dark:hover:text-red-300 disabled:opacity-50"
                  title="Delete model"
                >
                  <svg v-if="deletingModel === model.id" class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                  </svg>
                  <svg v-else class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Settings Tab -->
        <div v-if="activeTab === 'settings'" class="space-y-6 animate-fade-in">
          <h2 class="text-2xl font-bold text-gray-900 dark:text-white">
            Settings
          </h2>

          <!-- Success Message -->
          <div
            v-if="settingsSaved"
            class="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400 px-4 py-3 rounded-lg flex items-center"
          >
            <svg
              class="w-5 h-5 mr-2"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M5 13l4 4L19 7"
              />
            </svg>
            Settings saved successfully!
          </div>

          <div class="card p-6 space-y-6">
            <!-- Avatar Section -->
            <div>
              <h3
                class="text-lg font-semibold text-gray-900 dark:text-white mb-4"
              >
                Avatar
              </h3>
              
              <!-- Avatar Preview and Actions Row -->
              <div class="flex items-center space-x-4">
                <!-- Current Avatar Display -->
                <img 
                  :src="customAvatarPreview || auth.user?.avatar" 
                  class="w-20 h-20 rounded-full border-2 border-gray-200 dark:border-gray-700 flex-shrink-0"
                  alt="Current avatar"
                />
                
                <!-- Buttons -->
                <input
                  ref="avatarFileInput"
                  type="file"
                  accept="image/*"
                  class="hidden"
                  @change="handleCustomAvatarUpload"
                />
                <button
                  @click="triggerFileInput"
                  class="btn-secondary text-sm flex items-center space-x-2"
                >
                  <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <span>Upload</span>
                </button>
                
                <button
                  @click="saveAvatar"
                  :disabled="savingAvatar"
                  class="btn-primary text-sm disabled:opacity-50 flex items-center"
                >
                  <span v-if="savingAvatar" class="flex items-center">
                    <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                    </svg>
                    Saving...
                  </span>
                  <span v-else>Save Avatar</span>
                </button>
                
                <span v-if="customAvatarFile" class="text-sm text-gray-500 dark:text-gray-400">
                  {{ customAvatarFile.name }}
                </span>
              </div>
            </div>

            <!-- Profile Section -->
            <div class="border-t border-gray-100 dark:border-gray-700 pt-6">
              <h3
                class="text-lg font-semibold text-gray-900 dark:text-white mb-4"
              >
                Profile Information
              </h3>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                    >Display Name</label
                  >
                  <input
                    type="text"
                    v-model="displayName"
                    class="input-field"
                    placeholder="Enter your display name"
                  />
                </div>
                <div>
                  <label
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                    >Email</label
                  >
                  <input
                    type="email"
                    :value="auth.user?.email"
                    class="input-field bg-gray-100 dark:bg-gray-700 cursor-not-allowed"
                    disabled
                  />
                  <p class="text-xs text-gray-500 mt-1">
                    Email cannot be changed
                  </p>
                </div>
              </div>
            </div>

            <!-- Notifications -->
            <div class="border-t border-gray-100 dark:border-gray-700 pt-6">
              <h3
                class="text-lg font-semibold text-gray-900 dark:text-white mb-4"
              >
                Notifications
              </h3>
              <div class="space-y-4">
                <label
                  class="flex items-center justify-between cursor-pointer group"
                >
                  <div>
                    <span
                      class="text-gray-700 dark:text-gray-300 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors"
                      >Email notifications for orders</span
                    >
                    <p class="text-xs text-gray-500 dark:text-gray-400">
                      Receive updates about your order status
                    </p>
                  </div>
                  <div class="relative">
                    <input
                      type="checkbox"
                      v-model="settings.emailNotifications"
                      class="sr-only peer"
                    />
                    <div
                      class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary-600"
                    ></div>
                  </div>
                </label>
                <label
                  class="flex items-center justify-between cursor-pointer group"
                >
                  <div>
                    <span
                      class="text-gray-700 dark:text-gray-300 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors"
                      >Marketing emails</span
                    >
                    <p class="text-xs text-gray-500 dark:text-gray-400">
                      Receive news about new features and promotions
                    </p>
                  </div>
                  <div class="relative">
                    <input
                      type="checkbox"
                      v-model="settings.marketingEmails"
                      class="sr-only peer"
                    />
                    <div
                      class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-primary-300 dark:peer-focus:ring-primary-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary-600"
                    ></div>
                  </div>
                </label>
              </div>
            </div>

            <!-- Preferences -->
            <div class="border-t border-gray-100 dark:border-gray-700 pt-6">
              <h3
                class="text-lg font-semibold text-gray-900 dark:text-white mb-4"
              >
                Preferences
              </h3>
              <div class="space-y-4">
                <div>
                  <label
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                    >Language</label
                  >
                  <select v-model="settings.language" class="input-field w-48">
                    <option value="en">English</option>
                    <option value="zh-TW">繁體中文</option>
                    <option value="zh-CN">简体中文</option>
                    <option value="ja">日本語</option>
                  </select>
                </div>
                <div>
                  <label
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                    >Theme</label
                  >
                  <p class="text-xs text-gray-500 dark:text-gray-400 mb-2">
                    Use the theme toggle in the navigation bar to switch between
                    light and dark mode
                  </p>
                </div>
              </div>
            </div>

            <div
              class="border-t border-gray-100 dark:border-gray-700 pt-6 flex items-center gap-4"
            >
              <button @click="saveSettings" class="btn-primary">
                Save Changes
              </button>
              <span
                v-if="settingsSaved"
                class="text-green-600 dark:text-green-400 text-sm"
                >✓ Saved</span
              >
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
