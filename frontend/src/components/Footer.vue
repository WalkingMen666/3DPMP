<script setup>
import { RouterLink } from "vue-router";
</script>

<template>
  <footer
    class="bg-white dark:bg-dark-surface border-t border-gray-100 dark:border-gray-800 mt-auto"
  >
    <div class="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
        <div class="col-span-1 md:col-span-1">
          <div class="flex items-center space-x-2 mb-4">
            <img
              src="/assets/logo.png"
              alt="3DPMP Logo"
              class="w-8 h-8 rounded-lg"
            />
            <span class="text-xl font-bold text-gray-900 dark:text-white"
              >3DPMP</span
            >
          </div>
          <p class="text-gray-500 dark:text-gray-400 text-sm">
            The premier platform for 3D model sharing and professional printing
            services.
          </p>
        </div>

        <div>
          <h3
            class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4"
          >
            Platform
          </h3>
          <ul class="space-y-3">
            <li>
              <RouterLink
                to="/models"
                class="text-base text-gray-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400"
                >Marketplace</RouterLink
              >
            </li>
            <li>
              <RouterLink
                to="/about"
                class="text-base text-gray-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400"
                >About Us</RouterLink
              >
            </li>
            <li>
              <RouterLink
                to="/pricing"
                class="text-base text-gray-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400"
                >Pricing</RouterLink
              >
            </li>
          </ul>
        </div>

        <div>
          <h3
            class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4"
          >
            Support
          </h3>
          <ul class="space-y-3">
            <li>
              <RouterLink
                to="/faq"
                class="text-base text-gray-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400"
                >FAQ</RouterLink
              >
            </li>
            <li>
              <RouterLink
                to="/contact"
                class="text-base text-gray-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400"
                >Contact Us</RouterLink
              >
            </li>
          </ul>
        </div>

        <div>
          <h3
            class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4"
          >
            Legal
          </h3>
          <ul class="space-y-3">
            <li>
              <RouterLink
                to="/privacy"
                class="text-base text-gray-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400"
                >Privacy Policy</RouterLink
              >
            </li>
            <li>
              <RouterLink
                to="/terms"
                class="text-base text-gray-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400"
                >Terms of Service</RouterLink
              >
            </li>
          </ul>
        </div>
      </div>
      <div class="mt-8 border-t border-gray-100 dark:border-gray-800 pt-8">
        <p class="text-base text-gray-400 text-center">
          &copy; 2025 3DPMP. All rights reserved.
        </p>
      </div>
    </div>
  </footer>
</template>
