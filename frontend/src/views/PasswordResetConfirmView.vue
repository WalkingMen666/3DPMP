<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import axios from 'axios'
import { useI18n } from 'vue-i18n'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const newPassword1 = ref('')
const newPassword2 = ref('')
const loading = ref(false)
const error = ref('')
const success = ref(false)

// Extract uid and token from URL params
const uid = ref(route.params.uid || '')
const token = ref(route.params.token || '')

onMounted(() => {
  if (!uid.value || !token.value) {
    error.value = t('auth.resetPasswordPage.invalidLink')
  }
})

const handleSubmit = async () => {
  if (newPassword1.value !== newPassword2.value) {
    error.value = t('auth.resetPasswordPage.mismatch')
    return
  }

  loading.value = true
  error.value = ''
  success.value = false

  try {
    await axios.post('/api/auth/password/reset/confirm/', {
      uid: uid.value,
      token: token.value,
      new_password1: newPassword1.value,
      new_password2: newPassword2.value
    })
    success.value = true

    // Redirect to login after 3 seconds
    setTimeout(() => {
      router.push('/login')
    }, 3000)
  } catch (e) {
    if (e.response?.data) {
      const errors = e.response.data
      if (errors.new_password2) {
        error.value = errors.new_password2[0]
      } else if (errors.token) {
        error.value = t('auth.resetPasswordPage.invalidLink')
      } else if (errors.detail) {
        error.value = errors.detail
      } else {
        error.value = JSON.stringify(errors)
      }
    } else {
      error.value = t('auth.resetPasswordPage.error') || t('auth.forgotPasswordPage.error')
    }
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
          {{ $t('auth.resetPasswordPage.title') }}
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
          {{ $t('auth.resetPasswordPage.subtitle') }}
        </p>
      </div>

      <div v-if="success" class="text-green-600 text-sm bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
        <p class="font-medium mb-2">{{ $t('auth.resetPasswordPage.successTitle') }}</p>
        <p>{{ $t('auth.resetPasswordPage.successMessage') }}</p>
        <RouterLink to="/login" class="font-medium text-primary-600 hover:text-primary-500 mt-2 inline-block">
          {{ $t('auth.resetPasswordPage.goToLogin') }}
        </RouterLink>
      </div>

      <form v-else class="mt-8 space-y-6" @submit.prevent="handleSubmit">
        <div>
          <label for="password1" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {{ $t('auth.resetPasswordPage.newPassword') }}
          </label>
          <input
            id="password1"
            name="password1"
            type="password"
            autocomplete="new-password"
            required
            v-model="newPassword1"
            class="input-field"
            :placeholder="$t('auth.passwordPlaceholder')"
            :disabled="!uid || !token"
          />
        </div>

        <div>
          <label for="password2" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            {{ $t('auth.resetPasswordPage.confirmNewPassword') }}
          </label>
          <input
            id="password2"
            name="password2"
            type="password"
            autocomplete="new-password"
            required
            v-model="newPassword2"
            class="input-field"
            :placeholder="$t('auth.passwordPlaceholder')"
            :disabled="!uid || !token"
          />
        </div>

        <div v-if="error" class="text-red-500 text-sm bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
          {{ error }}
        </div>

        <div>
          <button
            type="submit"
            :disabled="loading || !uid || !token"
            class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-70 disabled:cursor-not-allowed transition-colors"
          >
            <span v-if="loading" class="absolute left-0 inset-y-0 flex items-center pl-3">
              <svg class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </span>
            {{ loading ? $t('auth.resetPasswordPage.resetting') : $t('auth.resetPasswordPage.resetBtn') }}
          </button>
        </div>

        <div class="text-center">
          <RouterLink to="/forgot-password" class="text-sm font-medium text-primary-600 hover:text-primary-500">
            {{ $t('auth.resetPasswordPage.requestNew') }}
          </RouterLink>
        </div>
      </form>
    </div>
  </div>
</template>
