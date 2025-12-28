<template>
  <div class="min-h-[70vh] flex items-center justify-center px-4 sm:px-6 lg:px-8">
    <div class="text-center max-w-lg">
      <!-- Construction Icon -->
      <div class="mx-auto w-24 h-24 bg-gradient-to-br from-amber-100 to-orange-100 dark:from-amber-900/30 dark:to-orange-900/30 rounded-full flex items-center justify-center mb-8">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
        </svg>
      </div>

      <!-- Title -->
      <h1 class="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
        {{ $t('underDevelopment.title') }}
      </h1>

      <!-- Description -->
      <p class="text-lg text-gray-600 dark:text-gray-400 mb-8">
        {{ $t('underDevelopment.pricingMessage') }}
      </p>

      <!-- Progress Bar -->
      <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 mb-8">
        <div class="bg-gradient-to-r from-amber-400 to-orange-500 h-2.5 rounded-full w-1/3 animate-pulse"></div>
      </div>

      <!-- Back Button -->
      <RouterLink 
        to="/" 
        class="inline-flex items-center px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        {{ $t('underDevelopment.backHome') }}
      </RouterLink>
    </div>
  </div>
</template>

<script setup>
import { RouterLink } from 'vue-router';
</script>
