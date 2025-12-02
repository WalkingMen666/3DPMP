<script setup>
import { ref, onMounted, computed } from "vue";
import { RouterLink } from "vue-router";
import ModelCard from "../components/ModelCard.vue";
import { useModelsStore } from "../stores/models";

const modelsStore = useModelsStore();
const loading = ref(true);

// Fetch featured models from backend on mount
onMounted(async () => {
  loading.value = true;
  try {
    await modelsStore.fetchPublicModels({ is_featured: true });
  } catch (error) {
    // Silently fail - no fake data
  } finally {
    loading.value = false;
  }
});

// Use store data - NO FAKE DATA
const featuredModels = computed(() => {
  return modelsStore.publicModels.slice(0, 4).map(model => ({
    id: model.id,
    name: model.model_name,
    author: model.owner_name || 'Unknown',
    price: model.base_price || '0.00',
    image: model.thumbnail || `https://placehold.co/400x400/6366f1/fff?text=${encodeURIComponent(model.model_name?.slice(0, 8) || 'Model')}`
  }));
});
</script>

<template>
  <div>
    <!-- Hero Section -->
    <section class="relative bg-white dark:bg-dark-surface overflow-hidden">
      <div
        class="absolute inset-0 bg-gradient-to-br from-primary-50/50 to-transparent dark:from-primary-900/10 dark:to-transparent"
      ></div>
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24 relative">
        <div class="text-center max-w-3xl mx-auto">
          <h1
            class="text-4xl md:text-6xl font-bold text-gray-900 dark:text-white mb-6 tracking-tight"
          >
            Bring Your Ideas to
            <span
              class="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-primary-400"
              >Life</span
            >
          </h1>
          <p class="text-xl text-gray-600 dark:text-gray-300 mb-10">
            The premier platform for sharing 3D models and professional printing
            services. Upload, slice, and print in minutes.
          </p>
          <div class="flex justify-center gap-4">
            <RouterLink to="/models" class="btn-primary text-lg px-8 py-3">
              Explore Models
            </RouterLink>
            <RouterLink to="/upload" class="btn-secondary text-lg px-8 py-3">
              Start Printing
            </RouterLink>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="py-20 bg-gray-50 dark:bg-dark-bg">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div
            class="p-6 bg-white dark:bg-dark-surface rounded-xl shadow-sm border border-gray-100 dark:border-gray-700/50"
          >
            <div
              class="w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center text-primary-600 dark:text-primary-400 mb-4"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
            </div>
            <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-2">
              Instant Upload & Slicing
            </h3>
            <p class="text-gray-600 dark:text-gray-400">
              Upload your STL files and get instant slicing estimates, material
              usage, and pricing.
            </p>
          </div>
          <div
            class="p-6 bg-white dark:bg-dark-surface rounded-xl shadow-sm border border-gray-100 dark:border-gray-700/50"
          >
            <div
              class="w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center text-primary-600 dark:text-primary-400 mb-4"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
            </div>
            <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-2">
              Professional Printing
            </h3>
            <p class="text-gray-600 dark:text-gray-400">
              High-quality printing services with various materials delivered
              straight to your doorstep.
            </p>
          </div>
          <div
            class="p-6 bg-white dark:bg-dark-surface rounded-xl shadow-sm border border-gray-100 dark:border-gray-700/50"
          >
            <div
              class="w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-lg flex items-center justify-center text-primary-600 dark:text-primary-400 mb-4"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-2">
              Community Driven
            </h3>
            <p class="text-gray-600 dark:text-gray-400">
              Join a thriving community of creators. Share your designs and get
              feedback.
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Featured Models -->
    <section class="py-20 bg-white dark:bg-dark-surface">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-end mb-10">
          <div>
            <h2 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
              Featured Models
            </h2>
            <p class="text-gray-600 dark:text-gray-400">
              Discover the most popular designs this week
            </p>
          </div>
          <RouterLink
            to="/models"
            class="text-primary-600 dark:text-primary-400 font-medium hover:text-primary-700 flex items-center"
          >
            View All
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5 ml-1"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fill-rule="evenodd"
                d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                clip-rule="evenodd"
              />
            </svg>
          </RouterLink>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <ModelCard
            v-for="model in featuredModels"
            :key="model.id"
            :model="model"
          />
        </div>
      </div>
    </section>
  </div>
</template>
