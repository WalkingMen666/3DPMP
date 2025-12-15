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
            {{ $t('footer.description') }}
          </p>
        </div>

        <div>
          <h3
            class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4"
          >
            {{ $t('footer.platform') }}
          </h3>
          <ul class="space-y-3">
            <li>
              <RouterLink
                to="/models"
                class="text-base text-gray-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400"
                >{{ $t('nav.models') }}</RouterLink
              >
            </li>
            <li>
              <RouterLink
                to="/about"
                class="text-base text-gray-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400"
                >{{ $t('footer.about') }}</RouterLink
              >
            </li>
            <li>
              <RouterLink
                to="/pricing"
                class="text-base text-gray-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400"
                >{{ $t('footer.pricing') }}</RouterLink
              >
            </li>
          </ul>
        </div>

        <div>
          <h3
            class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4"
          >
            {{ $t('footer.support') }}
          </h3>
          <ul class="space-y-3">
            <li>
              <RouterLink
                to="/faq"
                class="text-base text-gray-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400"
                >{{ $t('footer.faq') }}</RouterLink
              >
            </li>
            <li>
              <RouterLink
                to="/contact"
                class="text-base text-gray-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400"
                >{{ $t('footer.contact') }}</RouterLink
              >
            </li>
          </ul>
        </div>

        <div>
          <h3
            class="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-4"
          >
            {{ $t('footer.legal') }}
          </h3>
          <ul class="space-y-3">
            <li>
              <RouterLink
                to="/privacy"
                class="text-base text-gray-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400"
                >{{ $t('footer.privacy') }}</RouterLink
              >
            </li>
            <li>
              <RouterLink
                to="/terms"
                class="text-base text-gray-500 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400"
                >{{ $t('footer.terms') }}</RouterLink
              >
            </li>
          </ul>
        </div>
      </div>
      <div class="mt-8 border-t border-gray-100 dark:border-gray-800 pt-8">
        <p class="text-base text-gray-400 text-center">
          {{ $t('footer.copyright', { year: new Date().getFullYear() }) }}
        </p>
      </div>
    </div>
  </footer>
</template>
