<script setup>
import { RouterLink } from "vue-router";

defineProps({
  model: {
    type: Object,
    required: true,
  },
});
</script>

<template>
  <RouterLink :to="`/models/${model.id}`" class="block">
    <div class="card group cursor-pointer">
      <div
        class="relative aspect-square overflow-hidden bg-gray-100 dark:bg-gray-800"
      >
        <img
          :src="model.image"
          :alt="model.name"
          class="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-500"
        />
        <div
          class="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-4"
        >
          <span class="w-full btn-primary text-sm py-2 text-center"
            >View Details</span
          >
        </div>
      </div>
      <div class="p-4">
        <div class="flex justify-between items-start mb-2">
          <h3 class="font-semibold text-gray-900 dark:text-white truncate pr-2">
            {{ model.name }}
          </h3>
          <span class="text-primary-600 dark:text-primary-400 font-bold text-sm"
            >${{ model.price }}</span
          >
        </div>
        <div class="flex items-center text-sm text-gray-500 dark:text-gray-400">
          <span class="truncate">by {{ model.author }}</span>
        </div>
      </div>
    </div>
  </RouterLink>
</template>
