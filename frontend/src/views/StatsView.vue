<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { useAuthStore } from '../stores/auth';

const auth = useAuthStore();
const stats = ref(null);
const loading = ref(true);
const error = ref(null);

onMounted(async () => {
    // Auth Token Fix: Use token from store if available
    if (!auth.isAuthenticated) {
        error.value = "Unauthorized"; // Handle not logged in case if needed, though router guards should prevent this
        loading.value = false;
        return;
    }

    try {
        const response = await axios.get('/api/stats/', {
            headers: {
                // Manually attach header since we don't have a global interceptor
                Authorization: `Token ${auth.token}`
            }
        });
        stats.value = response.data;
    } catch (err) {
        error.value = err.response && err.response.status === 401 
            ? "Unauthorized access" 
            : (err.message || "Failed to load statistics.");
        console.error(err);
    } finally {
        loading.value = false;
    }
});

const formatCurrency = (value) => {
    return new Intl.NumberFormat('zh-TW', { style: 'currency', currency: 'TWD' }).format(value);
};
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-dark-bg py-12">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      
      <!-- Header -->
      <div class="mb-10 text-center">
        <h1 class="text-3xl font-extrabold text-gray-900 dark:text-white sm:text-4xl">
          {{ $t('stats.title') }}
        </h1>
        <p class="mt-2 text-lg text-gray-600 dark:text-gray-400">
          {{ $t('stats.subtitle') }}
        </p>
      </div>

      <div v-if="loading" class="text-center py-20">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
        <p class="mt-4 text-gray-500">{{ $t('stats.loading') }}</p>
      </div>

      <div v-else-if="error" class="text-center py-20 text-red-600">
        {{ $t('stats.error') }}
      </div>

      <div v-else class="space-y-12">
        
        <!-- SECTION 1: TOP MODELS (Public - Popularity Based) -->
        <section>
          <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6 flex items-center">
            <svg class="w-6 h-6 mr-2 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"></path></svg>
            {{ $t('stats.topModels') }}
          </h2>
          <div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <div v-for="(model, index) in stats.top_models" :key="index" 
                 class="bg-white dark:bg-dark-surface rounded-xl shadow-sm p-6 border border-gray-100 dark:border-gray-700 hover:shadow-md transition-shadow">
              <div class="flex items-center justify-between mb-4">
                <span class="text-3xl font-bold text-gray-200 dark:text-gray-700">#{{ index + 1 }}</span>
                <div class="flex flex-col items-end">
                    <span class="px-3 py-1 text-sm font-medium text-purple-800 bg-purple-100 rounded-full dark:bg-purple-900 dark:text-purple-200 mb-1">
                      {{ model.units_sold }} {{ $t('stats.sold') }}
                    </span>
                    <span class="text-xs text-gray-500" :title="$t('stats.popularityScore')">
                        🔥 {{ model.popularity_score }} pts
                    </span>
                </div>
              </div>
              <h3 class="text-xl font-bold text-gray-900 dark:text-white truncate" :title="model.model_name">
                {{ model.model_name }}
              </h3>
              <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{{ $t('stats.by') }} {{ model.creator }}</p>
            </div>
          </div>
        </section>

        <!-- SECTION 2: TRENDING MATERIALS (Public) -->
        <section class="max-w-4xl mx-auto">
             <!-- Trending Materials -->
             <div>
                 <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-6 flex items-center">
                    <svg class="w-6 h-6 mr-2 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"></path></svg>
                    {{ $t('stats.trendingMaterials') }}
                 </h2>
                 <div class="bg-white dark:bg-dark-surface rounded-xl shadow-sm overflow-hidden border border-gray-100 dark:border-gray-700 h-full">
                    <div class="p-6">
                      <ul class="space-y-4">
                        <li v-for="(mat, index) in stats.trending_materials" :key="index" class="relative">
                          <div class="flex items-center justify-between mb-1 relative z-10">
                            <span class="font-medium text-gray-700 dark:text-gray-200">{{ mat.name }}</span>
                            <span class="text-sm font-bold text-gray-500">{{ mat.usage_count }} {{ $t('stats.orders') }}</span>
                          </div>
                          <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
                            <div class="bg-blue-600 h-2.5 rounded-full transition-all duration-1000" 
                                 :style="{ width: `${(mat.usage_count / Math.max(...stats.trending_materials.map(m => m.usage_count))) * 100}%` }"></div>
                          </div>
                        </li>
                      </ul>
                    </div>
                 </div>
             </div>
        </section>

        <!-- ADMIN ONLY SECTION -->
        <div v-if="stats.is_admin" class="pt-8 border-t-2 border-dashed border-gray-200 dark:border-gray-700">
            <div class="bg-red-50 dark:bg-red-900/10 border border-red-100 dark:border-red-900/30 rounded-xl p-6 mb-8 flex justify-between items-center">
                 <div>
                    <h2 class="text-xl font-bold text-red-800 dark:text-red-400 flex items-center">
                        <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>
                        {{ $t('stats.adminReport') }}
                    </h2>
                    <p class="text-sm text-red-600 dark:text-red-300 mt-1">{{ $t('stats.adminReportDesc') }}</p>
                 </div>
            </div>

            <!-- 1. Monthly Trends (Full Width) -->
            <div class="bg-white dark:bg-dark-surface rounded-xl shadow-sm overflow-hidden border border-gray-100 dark:border-gray-700 mb-8">
                <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
                    <h3 class="font-bold text-gray-900 dark:text-white">{{ $t('stats.monthlyTrends') }}</h3>
                </div>
                <div class="overflow-x-auto">
                    <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                        <thead class="bg-gray-50 dark:bg-gray-800">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{{ $t('stats.month') }}</th>
                                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">{{ $t('stats.totalOrders') }}</th>
                                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">{{ $t('stats.uniqueCustomers') }}</th>
                                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">{{ $t('stats.avgOrderValue') }}</th>
                                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">{{ $t('stats.cancellationRate') }}</th>
                                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">{{ $t('stats.totalRevenue') }}</th>
                            </tr>
                        </thead>
                        <tbody class="bg-white dark:bg-dark-surface divide-y divide-gray-200 dark:divide-gray-700">
                            <tr v-for="row in stats.monthly_trends" :key="row.month">
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white font-medium">{{ row.month }}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400 text-right">{{ row.total_orders }}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400 text-right">{{ row.unique_customers }}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400 text-right">{{ formatCurrency(row.avg_order_value) }}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-right" :class="row.cancellation_rate > 10 ? 'text-red-600' : 'text-green-600'">
                                    {{ row.cancellation_rate }}%
                                </td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-green-600 font-bold">{{ formatCurrency(row.total_revenue) }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Grid for Other Admin Stats -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                
                <!-- 2. VIP Customers -->
                 <div class="bg-white dark:bg-dark-surface rounded-xl shadow-sm overflow-hidden border border-gray-100 dark:border-gray-700">
                    <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
                        <h3 class="font-bold text-gray-900 dark:text-white">{{ $t('stats.vipCustomers') }}</h3>
                    </div>
                     <ul class="divide-y divide-gray-200 dark:divide-gray-700">
                        <li v-for="(user, i) in stats.vip_customers" :key="i" class="px-6 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-800 hover:bg-opacity-50">
                            <div class="flex items-center">
                                <span class="h-8 w-8 rounded-full bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-300 flex items-center justify-center font-bold text-xs mr-3">
                                    {{ i + 1 }}
                                </span>
                                <div>
                                    <p class="text-sm font-medium text-gray-900 dark:text-white">{{ user.display_name || user.email.split('@')[0] }}</p>
                                    <p class="text-xs text-gray-500">{{ user.email }}</p>
                                </div>
                            </div>
                            <div class="text-right">
                                <p class="text-sm font-bold text-gray-900 dark:text-white">{{ formatCurrency(user.total_spent) }}</p>
                                <p class="text-xs text-gray-500">{{ user.total_orders }} {{ $t('stats.orders') }}</p>
                            </div>
                        </li>
                     </ul>
                </div>

                <!-- 3. Material Revenue -->
                <div class="bg-white dark:bg-dark-surface rounded-xl shadow-sm overflow-hidden border border-gray-100 dark:border-gray-700">
                    <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-700">
                        <h3 class="font-bold text-gray-900 dark:text-white">{{ $t('stats.materialRevenue') }}</h3>
                    </div>
                    <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                        <thead class="bg-gray-50 dark:bg-gray-800">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">{{ $t('stats.trendingMaterials') }}</th>
                                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">{{ $t('stats.revenuePercentage') }}</th>
                                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">{{ $t('stats.totalRevenue') }}</th>
                            </tr>
                        </thead>
                         <tbody class="bg-white dark:bg-dark-surface divide-y divide-gray-200 dark:divide-gray-700">
                            <tr v-for="mat in stats.material_revenue" :key="mat.material_name">
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white font-medium">{{ mat.material_name }}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-500 dark:text-gray-400">{{ mat.revenue_percentage }}%</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-green-600 font-bold">{{ formatCurrency(mat.revenue) }}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- 4. Hesitant Buyers -->
                 <div class="bg-white dark:bg-dark-surface rounded-xl shadow-sm overflow-hidden border border-gray-100 dark:border-gray-700">
                    <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-700 border-l-4 border-l-yellow-400">
                        <h3 class="font-bold text-gray-900 dark:text-white">{{ $t('stats.hesitantBuyers') }}</h3>
                    </div>
                     <ul class="divide-y divide-gray-200 dark:divide-gray-700">
                        <li v-for="(buyer, i) in stats.hesitant_buyers" :key="i" class="px-6 py-4 flex items-center justify-between">
                            <div>
                                <p class="text-sm font-medium text-gray-900 dark:text-white">{{ buyer.email }}</p>
                                <p class="text-xs text-gray-500">{{ $t('stats.lastCartActivity') }}: {{ new Date(buyer.last_cart_activity).toLocaleDateString() }}</p>
                            </div>
                            <span class="px-3 py-1 text-xs font-bold text-yellow-800 bg-yellow-100 rounded-full dark:bg-yellow-900 dark:text-yellow-200">
                                {{ buyer.cart_items_count }} {{ $t('stats.itemsInCart') }}
                            </span>
                        </li>
                     </ul>
                </div>

                <!-- 5. Employee Stats -->
                 <div class="bg-white dark:bg-dark-surface rounded-xl shadow-sm overflow-hidden border border-gray-100 dark:border-gray-700">
                    <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-700 border-l-4 border-l-blue-400">
                        <h3 class="font-bold text-gray-900 dark:text-white">{{ $t('stats.employeeStats') }}</h3>
                    </div>
                    <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                        <thead class="bg-gray-50 dark:bg-gray-800">
                            <tr>
                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">{{ $t('stats.reviews') }}</th>
                                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">{{ $t('stats.approvalRate') }}</th>
                            </tr>
                        </thead>
                         <tbody class="bg-white dark:bg-dark-surface divide-y divide-gray-200 dark:divide-gray-700">
                            <tr v-for="emp in stats.employee_stats" :key="emp.employee_name">
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white font-medium">{{ emp.employee_name }}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-right text-gray-500 dark:text-gray-400">{{ emp.total_reviews }}</td>
                                <td class="px-6 py-4 whitespace-nowrap text-sm text-right font-bold text-blue-600">{{ emp.approval_rate }}%</td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <!-- 6. Order Status Distribution (Admin) -->
                <div class="bg-white dark:bg-dark-surface rounded-xl shadow-sm overflow-hidden border border-gray-100 dark:border-gray-700">
                   <div class="px-6 py-4 border-b border-gray-100 dark:border-gray-700 border-l-4 border-l-green-400">
                       <h3 class="font-bold text-gray-900 dark:text-white">{{ $t('stats.orderStatusDist') }}</h3>
                   </div>
                   <div class="p-6">
                       <div class="grid grid-cols-2 gap-4">
                           <div v-for="stat in stats.order_status_distribution" :key="stat.status" 
                                class="text-center p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
                               <div class="text-2xl font-bold text-primary-600 dark:text-primary-400">{{ stat.count }}</div>
                               <div class="text-xs text-gray-500 uppercase mt-1">{{ stat.status }}</div>
                           </div>
                       </div>
                   </div>
               </div>

            </div>
        </div>

      </div>
    </div>
  </div>
</template>
