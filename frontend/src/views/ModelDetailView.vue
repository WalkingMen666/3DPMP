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
    console.log('Fetched model:', fetchedModel); // Debug log
    console.log('Model images from API:', fetchedModel?.images); // Debug log
    
    if (fetchedModel) {
      // Check if current user is the owner
      isOwner.value = auth.user && (fetchedModel.owner === auth.user.id || fetchedModel.owner_email === auth.user.email);
      
      // Build images array - images from API already have 'url' field from serializer
      let images = [];
      if (fetchedModel.images && fetchedModel.images.length > 0) {
        images = fetchedModel.images.map(img => getImageUrl(img)).filter(Boolean);
        console.log('Processed images:', images); // Debug log
      }
      if (images.length === 0 && fetchedModel.thumbnail_url) {
        images.push(fetchedModel.thumbnail_url);
      }
      if (images.length === 0 && fetchedModel.thumbnail) {
        images.push(fetchedModel.thumbnail);
      }
      if (images.length === 0) {
        images.push(`https://placehold.co/600x400/6366f1/fff?text=${encodeURIComponent(fetchedModel.model_name?.slice(0, 10) || 'Model')}`);
      }
      
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
            by
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
            Slicing Estimates
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
            <span>Calculating print parameters...</span>
          </div>
          <div v-else-if="model.slicingInfo" class="grid grid-cols-3 gap-4">
            <div class="text-center">
              <div class="text-sm text-gray-500 dark:text-gray-400">Weight</div>
              <div class="font-semibold text-gray-900 dark:text-white">
                {{ model.slicingInfo.weight }}
              </div>
            </div>
            <div
              class="text-center border-l border-gray-200 dark:border-gray-700"
            >
              <div class="text-sm text-gray-500 dark:text-gray-400">Time</div>
              <div class="font-semibold text-gray-900 dark:text-white">
                {{ model.slicingInfo.printTime }}
              </div>
            </div>
            <div
              class="text-center border-l border-gray-200 dark:border-gray-700"
            >
              <div class="text-sm text-gray-500 dark:text-gray-400">
                Filament
              </div>
              <div class="font-semibold text-gray-900 dark:text-white">
                {{ model.slicingInfo.filamentLength }}
              </div>
            </div>
          </div>
          <div v-else class="text-center py-4">
            <div class="text-gray-500 dark:text-gray-400 text-sm">
              <svg class="w-8 h-8 mx-auto mb-2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Slicing pending - estimates will be available once processing is complete</span>
            </div>
          </div>
        </div>

        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <span class="text-2xl font-bold text-gray-900 dark:text-white"
              >${{ model.price }}</span
            >
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
              Added to Cart!
            </span>
            <span v-else>Add to Cart</span>
          </button>

          <router-link
            to="/models"
            class="block text-center text-primary-600 hover:text-primary-500 text-sm"
          >
            ← Back to Marketplace
          </router-link>
        </div>
      </div>
    </div>

    <!-- Model Not Found -->
    <div v-else class="flex flex-col items-center justify-center py-24 text-center">
      <svg class="w-24 h-24 text-gray-300 dark:text-gray-600 mb-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">Model Not Found</h2>
      <p class="text-gray-500 dark:text-gray-400 mb-6">
        The model you're looking for doesn't exist or has been removed.
      </p>
      <router-link to="/models" class="btn-primary">
        ← Back to Marketplace
      </router-link>
    </div>
  </div>
</template>
