<script setup>
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useCartStore } from "../stores/cart";
import { useAuthStore } from "../stores/auth";
import { useModelsStore } from "../stores/models";
import { useMaterialsStore } from "../stores/materials";

const route = useRoute();
const router = useRouter();
const cart = useCartStore();
const auth = useAuthStore();
const modelsStore = useModelsStore();
const materialsStore = useMaterialsStore();

const model = ref(null);
const loading = ref(true);
const loadingSlicing = ref(true);
const selectedMaterial = ref(null);
const quantity = ref(1);
const addedToCart = ref(false);
const selectedImageIndex = ref(0);
const notFound = ref(false);
const isOwner = ref(false);

// Available materials from backend
const materials = computed(() => materialsStore.activeMaterials);

// Helper to get image URL
const getImageUrl = (img) => {
  if (!img) return null;
  if (typeof img === 'string') return img;
  return img.url || img.image_url || img.image || null;
};

onMounted(async () => {
  const modelId = route.params.id;
  
  // Fetch materials
  await materialsStore.fetchMaterials();
  if (materials.value.length > 0) {
    selectedMaterial.value = materials.value[0].id;
  }
  
  // Fetch from backend only - NO FAKE DATA
  try {
    const fetchedModel = await modelsStore.fetchModelById(modelId);
    console.log('=== DEBUG: Fetched model ===', fetchedModel);
    console.log('=== DEBUG: Model images from API ===', fetchedModel?.images);
    console.log('=== DEBUG: Thumbnail URL ===', fetchedModel?.thumbnail_url);
    
    if (fetchedModel) {
      // Check if current user is the owner
      isOwner.value = auth.user && (fetchedModel.owner === auth.user.id || fetchedModel.owner_email === auth.user.email);
      
      // Build images array - ALWAYS include thumbnail first, then additional images
      let images = [];
      
      // 1. Add thumbnail as the first image (if exists)
      if (fetchedModel.thumbnail_url) {
        images.push(fetchedModel.thumbnail_url);
      } else if (fetchedModel.thumbnail) {
        images.push(fetchedModel.thumbnail);
      }
      
      // 2. Add all additional images from the API (sorted by order)
      if (fetchedModel.images && fetchedModel.images.length > 0) {
        const sortedImages = [...fetchedModel.images].sort((a, b) => {
          // Primary images come first
          if (a.is_primary && !b.is_primary) return -1;
          if (!a.is_primary && b.is_primary) return 1;
          // Then sort by order
          return (a.order || 0) - (b.order || 0);
        });
        const additionalImageUrls = sortedImages.map(img => getImageUrl(img)).filter(Boolean);
        images = images.concat(additionalImageUrls);
        console.log('Added additional images:', additionalImageUrls); // Debug log
      }
      
      // 3. If still no images, use placeholder
      if (images.length === 0) {
        images.push(`https://placehold.co/600x400/6366f1/fff?text=${encodeURIComponent(fetchedModel.model_name?.slice(0, 10) || 'Model')}`);
      }
      
      console.log('=== DEBUG: Final images array ===', images);
      console.log('=== DEBUG: Number of images ===', images.length);
      
      model.value = {
        id: fetchedModel.id,
        name: fetchedModel.model_name,
        author: fetchedModel.owner_name || fetchedModel.owner_email?.split('@')[0] || 'Unknown',
        price: fetchedModel.price || '0.00',
        description: fetchedModel.description || 'No description available.',
        category: fetchedModel.category_display || fetchedModel.category || 'Other',
        visibility: fetchedModel.visibility_status || fetchedModel.visibility,
        images: images,
        slicingInfo: fetchedModel.slicing_info
      };
      
      if (model.value.slicingInfo) {
        loadingSlicing.value = false;
      } else {
        // No slicing info available - show pending message
        // Real slicing will be done by Celery worker after upload
        loadingSlicing.value = false;
      }
    } else {
      notFound.value = true;
    }
  } catch (error) {
    console.error('Error loading model:', error);
    notFound.value = true;
  }
  
  loading.value = false;
});

const currentImage = computed(() => {
  if (!model.value || !model.value.images) return "";
  return model.value.images[selectedImageIndex.value] || model.value.images[0];
});

// Calculate price based on material, volume (filament_used_cm3), and quantity
const calculatedPrice = computed(() => {
  if (!model.value?.slicingInfo || !selectedMaterial.value) {
    return null;
  }

  const material = materials.value.find(m => m.id === selectedMaterial.value);
  if (!material) return null;

  // Calculate weight from volume × material density (not hardcoded)
  let weightGrams = 0;
  if (model.value.slicingInfo.weight_grams) {
    // Legacy: use pre-calculated weight if available
    weightGrams = parseFloat(model.value.slicingInfo.weight_grams) || 0;
  } else if (model.value.slicingInfo.filament_used_cm3 && material.density_g_cm3) {
    // Calculate weight from volume × selected material's density
    const volumeCm3 = parseFloat(model.value.slicingInfo.filament_used_cm3) || 0;
    const density = parseFloat(material.density_g_cm3);
    if (density > 0) {
      weightGrams = volumeCm3 * density;
    }
  }

  if (weightGrams <= 0) return null;

  const pricePerGram = parseFloat(material.price_twd_g) || 0;
  if (pricePerGram <= 0) return null;

  const qty = parseInt(quantity.value) || 1;

  const total = weightGrams * pricePerGram * qty;
  return total.toFixed(2);
});

const addToCart = async () => {
  if (!auth.isAuthenticated) {
    router.push("/login");
    return;
  }

  try {
    await cart.addItem(model.value, quantity.value, selectedMaterial.value);
    addedToCart.value = true;

    setTimeout(() => {
      addedToCart.value = false;
    }, 2000);
  } catch (error) {
    alert(error.message);
  }
};
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center py-24">
      <svg
        class="animate-spin h-12 w-12 text-primary-600"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          class="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="4"
        ></circle>
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        ></path>
      </svg>
    </div>

    <!-- Content -->
    <div v-else-if="model" class="grid grid-cols-1 lg:grid-cols-2 gap-12">
      <!-- Image Gallery -->
      <div class="space-y-4">
        <div
          class="aspect-video bg-gray-100 dark:bg-gray-800 rounded-xl overflow-hidden"
        >
          <img
            :src="currentImage"
            :alt="model.name"
            class="w-full h-full object-cover"
          />
        </div>
        <div class="grid grid-cols-4 gap-4">
          <div
            v-for="(img, index) in model.images"
            :key="index"
            @click="selectedImageIndex = index"
            :class="[
              'aspect-square bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden cursor-pointer transition-all',
              selectedImageIndex === index
                ? 'ring-2 ring-primary-500'
                : 'hover:ring-2 ring-primary-300',
            ]"
          >
            <img
              :src="img"
              class="w-full h-full object-cover"
              :class="
                selectedImageIndex === index
                  ? 'opacity-100'
                  : 'opacity-70 hover:opacity-100'
              "
            />
          </div>
        </div>
      </div>

      <!-- Product Details -->
      <div class="space-y-8">
        <div>
          <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
            {{ model.name }}
          </h1>
          <p class="text-lg text-gray-500 dark:text-gray-400">
            {{ $t('modelDetail.by') }}
            <span class="text-primary-600 dark:text-primary-400 font-medium">{{
              model.author
            }}</span>
          </p>
          <span
            class="inline-block mt-2 px-3 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-sm rounded-full"
            >{{ model.category }}</span
          >
        </div>

        <div class="prose dark:prose-invert">
          <p class="text-gray-600 dark:text-gray-300">
            {{ model.description }}
          </p>
        </div>

        <!-- Slicing Info Card -->
        <div
          class="bg-gray-50 dark:bg-gray-800/50 rounded-xl p-6 border border-gray-100 dark:border-gray-700"
        >
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            {{ $t('modelDetail.slicing.title') }}
          </h3>
          <div
            v-if="loadingSlicing"
            class="flex items-center space-x-2 text-gray-500"
          >
            <svg
              class="animate-spin h-5 w-5"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                class="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                stroke-width="4"
              ></circle>
              <path
                class="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            <span>{{ $t('modelDetail.slicing.calculating') }}</span>
          </div>
          <div v-else-if="model.slicingInfo" class="grid grid-cols-2 gap-4">
            <div class="text-center">
              <div class="text-sm text-gray-500 dark:text-gray-400">{{ $t('modelDetail.slicing.filament') }}</div>
              <div class="font-semibold text-gray-900 dark:text-white">
                {{ model.slicingInfo.filamentLength || (model.slicingInfo.filament_used_mm ? `${(model.slicingInfo.filament_used_mm / 1000).toFixed(2)}m` : '--') }}
              </div>
            </div>
            <div
              class="text-center border-l border-gray-200 dark:border-gray-700"
            >
              <div class="text-sm text-gray-500 dark:text-gray-400">
                {{ $t('modelDetail.slicing.volume') || '體積' }}
              </div>
              <div class="font-semibold text-gray-900 dark:text-white">
                {{ model.slicingInfo.filament_used_cm3 ? `${model.slicingInfo.filament_used_cm3.toFixed(2)} cm³` : '--' }}
              </div>
            </div>
          </div>
          <div v-else class="text-center py-4">
            <div class="text-gray-500 dark:text-gray-400 text-sm">
              <svg class="w-8 h-8 mx-auto mb-2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{{ $t('modelDetail.slicing.pending') }}</span>
            </div>
          </div>
        </div>

        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <span class="text-2xl font-bold text-gray-900 dark:text-white">
              <template v-if="calculatedPrice !== null">
                NT$ {{ calculatedPrice }}
              </template>
              <template v-else-if="model.slicingInfo">
                NT$ --
              </template>
              <template v-else>
                <span class="text-base text-gray-500">{{ $t('modelDetail.slicing.pending') }}</span>
              </template>
            </span>
            <div class="flex items-center space-x-4">
              <select v-model="selectedMaterial" class="input-field w-32">
                <option v-for="mat in materials" :key="mat.id" :value="mat.id">
                  {{ mat.name }}
                </option>
                <!-- Fallback if no materials from backend -->
                <option v-if="materials.length === 0" value="">PLA</option>
              </select>
              <input
                type="number"
                v-model="quantity"
                min="1"
                class="input-field w-20"
              />
            </div>
          </div>

          <button
            @click="addToCart"
            :class="[
              'w-full py-4 text-lg font-semibold rounded-lg transition-all duration-300',
              addedToCart ? 'bg-green-500 text-white' : 'btn-primary',
            ]"
          >
            <span v-if="addedToCart" class="flex items-center justify-center">
              <svg
                class="w-6 h-6 mr-2"
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
              {{ $t('modelDetail.addedToCart') }}
            </span>
            <span v-else>{{ $t('modelDetail.addToCart') }}</span>
          </button>

          <router-link
            to="/models"
            class="block text-center text-primary-600 hover:text-primary-500 text-sm"
          >
            {{ $t('modelDetail.backToMarketplace') }}
          </router-link>
        </div>
      </div>
    </div>

    <!-- Model Not Found -->
    <div v-else class="flex flex-col items-center justify-center py-24 text-center">
      <svg class="w-24 h-24 text-gray-300 dark:text-gray-600 mb-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">{{ $t('modelDetail.notFound.title') }}</h2>
      <p class="text-gray-500 dark:text-gray-400 mb-6">
        {{ $t('modelDetail.notFound.description') }}
      </p>
      <router-link to="/models" class="btn-primary">
        {{ $t('modelDetail.backToMarketplace') }}
      </router-link>
    </div>
  </div>
</template>
