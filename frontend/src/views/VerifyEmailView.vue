<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import axios from 'axios'
import { useI18n } from 'vue-i18n'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const loading = ref(true)
const error = ref('')
const success = ref(false)

// Extract key from URL params
const key = ref(route.params.key || '')

onMounted(async () => {
  if (!key.value) {
    error.value = t('auth.verifyEmailPage.invalidLink')
    loading.value = false
    return
  }

  try {
    await axios.post('/api/auth/registration/verify-email/', {
      key: key.value
    })
    success.value = true
  } catch (e) {
    if (e.response?.data?.detail) {
      error.value = e.response.data.detail
    } else {
      error.value = t('auth.verifyEmailPage.expiredLink')
    }
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="min-h-[80vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 bg-white dark:bg-dark-surface p-8 rounded-2xl shadow-lg border border-gray-100 dark:border-gray-700/50">
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900 dark:text-white">
          {{ $t('auth.verifyEmailPage.title') }}
        </h2>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="text-center py-8">
        <svg class="animate-spin h-10 w-10 text-primary-600 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <p class="mt-4 text-gray-600 dark:text-gray-400">{{ $t('auth.verifyEmailPage.verifying') }}</p>
      </div>

      <!-- Success State -->
      <div v-if="success && !loading" class="text-green-600 text-sm bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
        <div class="flex items-center mb-3">
          <svg class="h-6 w-6 text-green-500 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p class="font-medium text-lg">{{ $t('auth.verifyEmailPage.successTitle') }}</p>
        </div>
        <p>{{ $t('auth.verifyEmailPage.successMessage') }}</p>
        <RouterLink to="/login" class="mt-4 inline-block w-full text-center px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors">
          {{ $t('auth.verifyEmailPage.goToLogin') }}
        </RouterLink>
      </div>

      <!-- Error State -->
      <div v-if="error && !loading" class="text-red-600 text-sm bg-red-50 dark:bg-red-900/20 p-4 rounded-lg border border-red-200 dark:border-red-800">
        <div class="flex items-start">
          <svg class="h-5 w-5 text-red-400 mr-2 flex-shrink-0" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
          <div>
            <p class="font-medium mb-2">{{ $t('auth.verifyEmailPage.failedTitle') }}</p>
            <p>{{ error }}</p>
            <RouterLink to="/register" class="mt-3 inline-block font-medium text-primary-600 hover:text-primary-500">
              {{ $t('auth.verifyEmailPage.registerAgain') }}
            </RouterLink>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
