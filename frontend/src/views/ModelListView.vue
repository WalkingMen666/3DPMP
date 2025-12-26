<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { useI18n } from 'vue-i18n';
import ModelCard from "../components/ModelCard.vue";
import Navbar from '../components/Navbar.vue';
import Footer from '../components/Footer.vue';
import { useModelsStore } from "../stores/models";
import { useMaterialsStore } from "../stores/materials";

const { t } = useI18n();

const modelsStore = useModelsStore();
const materialsStore = useMaterialsStore();

const searchQuery = ref("");
const selectedCategory = ref("All");
const selectedMaterial = ref("all");
const minPrice = ref("");
const maxPrice = ref("");
const sortBy = ref("nameAsc");
const loading = ref(true);

// Price validation: auto-swap if min > max or max < min
const validatePriceRange = () => {
  const min = parseFloat(minPrice.value);
  const max = parseFloat(maxPrice.value);
  if (!isNaN(min) && !isNaN(max) && min > max) {
    [minPrice.value, maxPrice.value] = [maxPrice.value, minPrice.value];
  }
};

watch([minPrice, maxPrice], validatePriceRange);

const categoryIds = ['All', 'Art', 'Engineering', 'Fashion', 'Gadgets', 'Toys', 'Home', 'Tools', 'Education', 'Other'];

// Compute category counts from actual model data
const categoryCounts = computed(() => {
  const counts = {};
  categoryIds.forEach(id => {
    counts[id] = id === 'All' 
      ? allModels.value.length 
      : allModels.value.filter(m => m.category === id).length;
  });
  return counts;
});

const categories = computed(() => categoryIds.map(id => ({
  id,
  label: t(`marketplace.categoriesList.${id}`),
  count: categoryCounts.value[id]
})));

const sortOptions = computed(() => [
  { value: 'nameAsc', label: t('marketplace.sortOptions.nameAsc') },
  { value: 'nameDesc', label: t('marketplace.sortOptions.nameDesc') },
  { value: 'priceAsc', label: t('marketplace.sortOptions.priceAsc') },
  { value: 'priceDesc', label: t('marketplace.sortOptions.priceDesc') },
  { value: 'authorAsc', label: t('marketplace.sortOptions.authorAsc') },
]);

// Fetch models and materials from backend on mount
onMounted(async () => {
  loading.value = true;
  try {
    await Promise.all([
      modelsStore.fetchPublicModels(),
      materialsStore.fetchMaterials()
    ]);
  } catch (error) {
    // Silently fail - no models will be shown
  } finally {
    loading.value = false;
  }
});

// Get sorted materials by effective price (density × price per gram)
const sortedMaterialsByPrice = computed(() => {
  return [...materialsStore.activeMaterials].sort((a, b) => {
    const priceA = (parseFloat(a.density_g_cm3) || 1.24) * (parseFloat(a.price_twd_g) || 0);
    const priceB = (parseFloat(b.density_g_cm3) || 1.24) * (parseFloat(b.price_twd_g) || 0);
    return priceA - priceB;
  });
});

// Calculate model price based on material (using material's density)
const calculatePrice = (slicingInfo, material) => {
  if (!slicingInfo?.filament_used_cm3 || !material) return null;
  // Price = volume (cm³) × density (g/cm³) × price per gram
  const density = parseFloat(material.density_g_cm3) || 1.24;
  const pricePerG = parseFloat(material.price_twd_g) || 0;
  const weightG = slicingInfo.filament_used_cm3 * density;
  return weightG * pricePerG;
};

// Convert backend models to display format with calculated prices
const allModels = computed(() => {
  const materials = sortedMaterialsByPrice.value;
  const cheapest = materials[0];
  const expensive = materials[materials.length - 1];
  const selectedMat = materialsStore.activeMaterials.find(m => m.id === selectedMaterial.value);
  
  return modelsStore.publicModels.map(model => {
    const slicingInfo = model.slicing_info;
    let priceDisplay = null;
    let calculatedPrice = null;
    
    if (slicingInfo?.filament_used_cm3 && materials.length > 0) {
      if (selectedMaterial.value === 'all') {
        // Show price range - use cheapest and most expensive materials
        const minP = calculatePrice(slicingInfo, cheapest);
        const maxP = calculatePrice(slicingInfo, expensive);
        if (minP !== null && maxP !== null) {
          priceDisplay = `$${minP.toFixed(0)} ~ $${maxP.toFixed(0)}`;
          calculatedPrice = minP; // Use min price for filtering
        }
      } else if (selectedMat) {
        // Show specific price for selected material
        const price = calculatePrice(slicingInfo, selectedMat);
        if (price !== null) {
          priceDisplay = `$${price.toFixed(0)}`;
          calculatedPrice = price;
        }
      }
    }
    
    return {
      id: model.id,
      name: model.model_name || model.name,
      author: model.owner_name || 'Unknown',
      category: model.category || 'Art',
      image: model.thumbnail_url || model.thumbnail || `https://placehold.co/400x400/6366f1/fff?text=${encodeURIComponent((model.model_name || model.name)?.slice(0, 8) || 'Model')}`,
      priceDisplay,
      calculatedPrice,
      hasSlicingInfo: !!slicingInfo?.filament_used_cm3
    };
  });
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

    // Price filter - only apply if values are set
    let matchesPrice = true;
    if (model.calculatedPrice !== null) {
      const min = parseFloat(minPrice.value);
      const max = parseFloat(maxPrice.value);
      if (!isNaN(min) && model.calculatedPrice < min) matchesPrice = false;
      if (!isNaN(max) && model.calculatedPrice > max) matchesPrice = false;
    }

    return matchesSearch && matchesCategory && matchesPrice;
  });

  // Sorting
  const [sortField, sortOrder] = sortBy.value.replace('Asc', '-asc').replace('Desc', '-desc').split("-");
  result.sort((a, b) => {
    let comparison = 0;
    if (sortField === "name") {
      comparison = a.name.localeCompare(b.name);
    } else if (sortField === "price") {
      comparison = (a.calculatedPrice || 0) - (b.calculatedPrice || 0);
    } else if (sortField === "author") {
      comparison = a.author.localeCompare(b.author);
    }
    return sortOrder === "desc" ? -comparison : comparison;
  });

  return result;
});
</script>

<template>
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="flex flex-col md:flex-row justify-between items-center mb-8 bg-white dark:bg-dark-surface p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700/50">
        <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-4 md:mb-0 bg-clip-text text-transparent bg-gradient-to-r from-primary-600 to-secondary-600">
          {{ $t('marketplace.title') }}
        </h1>
        
        <div class="w-full md:w-96 relative">
          <input 
            v-model="searchQuery"
            type="text" 
            :placeholder="$t('marketplace.searchPlaceholder')" 
            class="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
          />
          <svg class="w-5 h-5 text-gray-400 absolute left-3 top-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
      </div>

      <div class="flex flex-col lg:flex-row gap-8">
        <!-- Sidebar Filters -->
        <aside class="w-full lg:w-64 space-y-8">
          <!-- Categories -->
          <div class="bg-white dark:bg-dark-surface p-6 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700/50">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center">
              <svg class="w-5 h-5 mr-2 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h7" />
              </svg>
              {{ $t('marketplace.categories') }}
            </h3>
            <div class="space-y-2">
              <button 
                v-for="category in categories" 
                :key="category.id"
                @click="selectedCategory = category.id"
                :class="[
                  'w-full text-left px-3 py-2 rounded-lg text-sm transition-colors flex justify-between items-center group',
                  selectedCategory === category.id 
                    ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 font-medium' 
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'
                ]"
              >
                <span>{{ category.label }}</span>
                <span :class="[
                  'text-xs px-2 py-0.5 rounded-full transition-colors',
                  selectedCategory === category.id
                    ? 'bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-300'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 group-hover:bg-gray-200 dark:group-hover:bg-gray-600'
                ]">{{ category.count }}</span>
              </button>
            </div>
          </div>

          <!-- Material Selector -->
          <div class="bg-white dark:bg-dark-surface p-6 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700/50">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center">
              <svg class="w-5 h-5 mr-2 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.415-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
              </svg>
              {{ $t('marketplace.material.title') }}
            </h3>
            <select 
              v-model="selectedMaterial"
              class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="all">{{ $t('marketplace.material.all') }}</option>
              <option v-for="material in materialsStore.activeMaterials" :key="material.id" :value="material.id">
                {{ material.name }}
              </option>
            </select>
          </div>

          <!-- Price Filter -->
          <div class="bg-white dark:bg-dark-surface p-6 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700/50">
            <h3 class="font-bold text-gray-900 dark:text-white mb-4 flex items-center">
              <svg class="w-5 h-5 mr-2 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {{ $t('marketplace.priceFilter.title') }}
            </h3>
            <div class="space-y-3">
              <div>
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">{{ $t('marketplace.priceFilter.minPrice') }}</label>
                <input 
                  v-model="minPrice"
                  type="number"
                  min="0"
                  :placeholder="$t('marketplace.priceFilter.minPlaceholder')"
                  class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
              <div>
                <label class="block text-xs text-gray-500 dark:text-gray-400 mb-1">{{ $t('marketplace.priceFilter.maxPrice') }}</label>
                <input 
                  v-model="maxPrice"
                  type="number"
                  min="0"
                  :placeholder="$t('marketplace.priceFilter.maxPlaceholder')"
                  class="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>
        </aside>

        <!-- Product Grid -->
        <div class="flex-1">
          <!-- Sort Controls -->
          <div class="flex justify-between items-center mb-6 bg-white dark:bg-dark-surface p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700/50">
            <p class="text-sm text-gray-500 dark:text-gray-400">
              {{ $t('marketplace.showingResults', { count: filteredModels.length }) }}
            </p>
            <div class="flex items-center space-x-2">
              <label class="text-sm text-gray-600 dark:text-gray-400 hidden sm:inline">{{ $t('marketplace.sortBy') }}:</label>
              <select 
                v-model="sortBy"
                class="text-sm border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-primary-500 focus:border-primary-500"
              >
                <option v-for="option in sortOptions" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </div>
          </div>

          <!-- Grid -->
          <div v-if="filteredModels.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            <ModelCard 
              v-for="model in filteredModels" 
              :key="model.id" 
              :model="model" 
            />
          </div>

          <!-- Empty State -->
          <div v-else class="text-center py-20 bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50">
            <svg class="mx-auto h-16 w-16 text-gray-300 dark:text-gray-600 mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-1">{{ $t('marketplace.noModelsFound') }}</h3>
            <p class="text-gray-500 dark:text-gray-400">{{ $t('marketplace.tryAdjusting') }}</p>
          </div>
        </div>
      </div>
    </main>
</template>
