<script setup>
import { RouterLink } from "vue-router";
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
            {{ $t('home.hero.titlePrefix') }}
            <span
              class="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-primary-400"
              >{{ $t('home.hero.titleSuffix') }}</span
            >
          </h1>
          <p class="text-xl text-gray-600 dark:text-gray-300 mb-10">
            {{ $t('home.hero.subtitle') }}
          </p>
          <div class="flex justify-center gap-4">
            <RouterLink to="/models" class="btn-primary text-lg px-8 py-3">
              {{ $t('home.hero.explore') }}
            </RouterLink>
            <RouterLink to="/upload" class="btn-secondary text-lg px-8 py-3">
              {{ $t('home.hero.start') }}
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
              {{ $t('home.features.upload') }}
            </h3>
            <p class="text-gray-600 dark:text-gray-400">
              {{ $t('home.features.uploadDesc') }}
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
              {{ $t('home.features.printing') }}
            </h3>
            <p class="text-gray-600 dark:text-gray-400">
              {{ $t('home.features.printingDesc') }}
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
              {{ $t('home.features.community') }}
            </h3>
            <p class="text-gray-600 dark:text-gray-400">
              {{ $t('home.features.communityDesc') }}
            </p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>
