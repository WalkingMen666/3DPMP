<script setup>
import { ref, computed, onMounted } from "vue";
import ModelCard from "../components/ModelCard.vue";
import { useModelsStore } from "../stores/models";

const modelsStore = useModelsStore();

const searchQuery = ref("");
const selectedCategory = ref("All");
const priceRange = ref(100);
const sortBy = ref("name-asc");
const loading = ref(true);

const categories = ["All", "Art", "Engineering", "Fashion", "Gadgets", "Toys"];

const sortOptions = [
  { value: "name-asc", label: "Name (A-Z)" },
  { value: "name-desc", label: "Name (Z-A)" },
  { value: "price-asc", label: "Price (Low to High)" },
  { value: "price-desc", label: "Price (High to Low)" },
  { value: "author-asc", label: "Author (A-Z)" },
];

// Fetch models from backend on mount
onMounted(async () => {
  loading.value = true;
  try {
    await modelsStore.fetchPublicModels();
  } catch (error) {
    // Silently fail - no models will be shown
  } finally {
    loading.value = false;
  }
});

// Convert backend models to display format - NO FAKE DATA - NO FAKE DATA
const allModels = computed(() => {
  return modelsStore.publicModels.map(model => ({
    id: model.id,
    name: model.model_name || model.name,
    author: model.owner_name || 'Unknown',
    price: model.base_price || model.price || '0.00',
    category: model.category || 'Art',
    image: model.thumbnail_url || model.thumbnail || `https://placehold.co/400x400/6366f1/fff?text=${encodeURIComponent((model.model_name || model.name)?.slice(0, 8) || 'Model')}`
  }));
});

const filteredModels = computed(() => {
  let result = allModels.value.filter((model) => {
    // Search filter
    const matchesSearch =
      searchQuery.value === "" ||
      model.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      model.author.toLowerCase().includes(searchQuery.value.toLowerCase());

    // Category filter
    const matchesCategory =
      selectedCategory.value === "All" ||
      model.category === selectedCategory.value;

    // Price filter
    const matchesPrice = parseFloat(model.price) <= priceRange.value;

    return matchesSearch && matchesCategory && matchesPrice;
  });

  // Sorting
  const [sortField, sortOrder] = sortBy.value.split("-");
  result.sort((a, b) => {
    let comparison = 0;
    if (sortField === "name") {
      comparison = a.name.localeCompare(b.name);
    } else if (sortField === "price") {
      comparison = parseFloat(a.price) - parseFloat(b.price);
    } else if (sortField === "author") {
      comparison = a.author.localeCompare(b.author);
    }
    return sortOrder === "desc" ? -comparison : comparison;
  });

  return result;
});
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <div class="flex flex-col md:flex-row gap-8">
      <!-- Sidebar Filters -->
      <div class="w-full md:w-64 flex-shrink-0 space-y-8">
        <div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Search
          </h3>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search models..."
            class="input-field"
          />
        </div>

        <div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Categories
          </h3>
          <div class="space-y-2">
            <label
              v-for="category in categories"
              :key="category"
              class="flex items-center space-x-2 cursor-pointer"
            >
              <input
                type="radio"
                :value="category"
                v-model="selectedCategory"
                class="text-primary-600 focus:ring-primary-500"
              />
              <span class="text-gray-600 dark:text-gray-300">{{
                category
              }}</span>
            </label>
          </div>
        </div>

        <div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Max Price: ${{ priceRange }}
          </h3>
          <input
            type="range"
            v-model="priceRange"
            min="0"
            max="100"
            class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
          />
        </div>

        <div>
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Sort By
          </h3>
          <select v-model="sortBy" class="input-field">
            <option
              v-for="option in sortOptions"
              :key="option.value"
              :value="option.value"
            >
              {{ option.label }}
            </option>
          </select>
        </div>
      </div>

      <!-- Main Content -->
      <div class="flex-1">
        <div class="flex justify-between items-center mb-6">
          <h1 class="text-2xl font-bold text-gray-900 dark:text-white">
            Marketplace
          </h1>
          <div class="text-gray-500 dark:text-gray-400">
            Showing {{ filteredModels.length }} results
          </div>
        </div>

        <div
          v-if="filteredModels.length === 0"
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
              d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <p class="text-gray-500 dark:text-gray-400 mb-2">No models found</p>
          <p class="text-sm text-gray-400 dark:text-gray-500">
            Try adjusting your search or filter criteria
          </p>
        </div>

        <div
          v-else
          class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          <ModelCard
            v-for="model in filteredModels"
            :key="model.id"
            :model="model"
          />
        </div>
      </div>
    </div>
  </div>
</template>
