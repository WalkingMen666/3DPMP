<script setup>
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import axios from 'axios'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const email = ref('')
const loading = ref(false)
const error = ref('')
const success = ref(false)

const handleSubmit = async () => {
  loading.value = true
  error.value = ''
  success.value = false

  try {
    await axios.post('/api/auth/password/reset/', {
      email: email.value
    })
    success.value = true
  } catch (e) {
    error.value = e.response?.data?.email?.[0] || e.response?.data?.detail || t('auth.forgotPasswordPage.error')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-[80vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 bg-white dark:bg-dark-surface p-8 rounded-2xl shadow-lg border border-gray-100 dark:border-gray-700/50">
      <div>
        <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900 dark:text-white">
          {{ $t('auth.forgotPasswordPage.title') }}
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
          {{ $t('auth.forgotPasswordPage.subtitle') }}
          <RouterLink to="/login" class="font-medium text-primary-600 hover:text-primary-500">
            {{ $t('auth.forgotPasswordPage.signIn') }}
          </RouterLink>
        </p>
      </div>

      <div v-if="success" class="text-green-600 text-sm bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
        <p class="font-medium mb-2">{{ $t('auth.forgotPasswordPage.successTitle') }}</p>
        <p>{{ $t('auth.forgotPasswordPage.successMessage', { email }) }}</p>
        <p class="mt-2">{{ $t('auth.forgotPasswordPage.checkEmail') }}</p>
        <p class="mt-2 text-xs text-gray-600 dark:text-gray-400">
          {{ $t('auth.forgotPasswordPage.devNote') }}
        </p>
      </div>

      <form v-else class="mt-8 space-y-6" @submit.prevent="handleSubmit">
        <div>
          <label for="email" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {{ $t('auth.email') }}
          </label>
          <input
            id="email"
            name="email"
            type="email"
            autocomplete="email"
            required
            v-model="email"
            class="input-field"
            :placeholder="$t('auth.emailPlaceholder')"
          />
          <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
            {{ $t('auth.forgotPasswordPage.description') }}
          </p>
        </div>

        <div v-if="error" class="text-red-500 text-sm text-center bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
          {{ error }}
        </div>

        <div>
          <button
            type="submit"
            :disabled="loading"
            class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-70 disabled:cursor-not-allowed transition-colors"
          >
            <span v-if="loading" class="absolute left-0 inset-y-0 flex items-center pl-3">
              <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </span>
            {{ loading ? $t('auth.forgotPasswordPage.sending') : $t('auth.forgotPasswordPage.sendLink') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
