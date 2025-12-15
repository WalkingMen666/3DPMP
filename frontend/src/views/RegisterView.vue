<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter, RouterLink } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { useI18n } from "vue-i18n";
import axios from "axios";

const router = useRouter();
const auth = useAuthStore();

const email = ref("");
const password = ref("");
const confirmPassword = ref("");
const loading = ref(false);
const error = ref("");
const success = ref(false);
const registeredEmail = ref("");
const googleClientId = ref(null);

// Fetch Google Client ID on mount
onMounted(async () => {
  try {
    const response = await axios.get('/api/auth/google/client-id/');
    googleClientId.value = response.data.client_id;
    if (googleClientId.value) {
      loadGoogleScript();
    }
  } catch (e) {
    console.log('Google OAuth not configured');
  }
});

const loadGoogleScript = () => {
  if (document.getElementById('google-signin-script')) {
    initializeGoogle();
    return;
  }
  
  const script = document.createElement('script');
  script.id = 'google-signin-script';
  script.src = 'https://accounts.google.com/gsi/client';
  script.async = true;
  script.defer = true;
  script.onload = initializeGoogle;
  document.head.appendChild(script);
};

const initializeGoogle = () => {
  if (!window.google || !googleClientId.value) return;
  
  window.google.accounts.id.initialize({
    client_id: googleClientId.value,
    callback: handleGoogleCallback,
  });
  
  // Retry rendering button until element is available
  const tryRenderButton = (attempts = 0) => {
    const btnEl = document.getElementById('google-signup-btn');
    if (btnEl) {
      window.google.accounts.id.renderButton(btnEl, { 
        theme: 'outline', 
        size: 'large',
        width: '100%',
        text: 'signup_with',
      });
    } else if (attempts < 10) {
      setTimeout(() => tryRenderButton(attempts + 1), 100);
    }
  };
  tryRenderButton();
};

const handleGoogleCallback = async (response) => {
  loading.value = true;
  error.value = "";
  
  try {
    await auth.googleLogin(response.credential);
    router.push("/dashboard");
  } catch (e) {
    error.value = e.message || "Google sign-up failed. Please try again.";
  } finally {
    loading.value = false;
  }
};

// Password strength validation
const { t } = useI18n();

const passwordChecks = computed(() => ({
  minLength: password.value.length >= 8,
  hasUppercase: /[A-Z]/.test(password.value),
  hasLowercase: /[a-z]/.test(password.value),
  hasNumber: /[0-9]/.test(password.value),
  hasSpecial: /[!@#$%^&*(),.?":{}|<>]/.test(password.value),
  notCommon: !["password", "12345678", "qwerty123"].includes(
    password.value.toLowerCase()
  ),
}));

const passwordStrength = computed(() => {
  const checks = Object.values(passwordChecks.value).filter(Boolean).length;
  if (checks <= 2) return { label: "Weak", translatedLabel: t('auth.passwordStrength.weak'), color: "bg-red-500", width: "33%" };
  if (checks <= 4)
    return { label: "Medium", translatedLabel: t('auth.passwordStrength.medium'), color: "bg-yellow-500", width: "66%" };
  return { label: "Strong", translatedLabel: t('auth.passwordStrength.strong'), color: "bg-green-500", width: "100%" };
});

const isPasswordValid = computed(
  () =>
    passwordChecks.value.minLength &&
    passwordChecks.value.hasUppercase &&
    passwordChecks.value.hasLowercase &&
    passwordChecks.value.hasNumber
);

const passwordsMatch = computed(() => password.value === confirmPassword.value);

const handleRegister = async () => {
  if (!passwordsMatch.value) {
    error.value = "Passwords do not match";
    return;
  }

  if (password.value.length < 1) {
    error.value = "Password is required";
    return;
  }

  loading.value = true;
  error.value = "";
  success.value = false;

  try {
    await auth.register(email.value, password.value, confirmPassword.value);
    // Show email verification message instead of redirecting
    registeredEmail.value = email.value;
    success.value = true;
  } catch (e) {
    error.value = e.message || "Registration failed";
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div
    class="min-h-[80vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8"
  >
    <div
      class="max-w-md w-full space-y-8 bg-white dark:bg-dark-surface p-8 rounded-2xl shadow-lg border border-gray-100 dark:border-gray-700/50"
    >
      <div>
        <h2
          class="mt-6 text-center text-3xl font-extrabold text-gray-900 dark:text-white"
        >
          {{ $t('auth.createAccountTitle') }}
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
          {{ $t('auth.alreadyHaveAccount') }}
          <RouterLink
            to="/login"
            class="font-medium text-primary-600 hover:text-primary-500"
          >
            {{ $t('auth.signIn') }}
          </RouterLink>
        </p>
      </div>

      <!-- Email Verification Success Message -->
      <div v-if="success" class="text-green-600 text-sm bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
        <p class="font-medium mb-2">Registration successful!</p>
        <p>We've sent a verification email to <strong>{{ registeredEmail }}</strong>.</p>
        <p class="mt-2">Please check your email and click the verification link to activate your account.</p>
        <p class="mt-2 text-xs text-gray-600 dark:text-gray-400">
          Note: In development mode, the email will be printed to the server console. Check the terminal window.
        </p>
        <RouterLink to="/login" class="mt-3 inline-block font-medium text-primary-600 hover:text-primary-500">
          Go to login
        </RouterLink>
      </div>

      <!-- Error Message Display -->
      <div
        v-if="error && !success"
        class="text-red-600 text-sm bg-red-50 dark:bg-red-900/20 p-4 rounded-lg border border-red-200 dark:border-red-800"
      >
        <div class="flex items-start">
          <svg class="h-5 w-5 text-red-400 mr-2 flex-shrink-0" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
          </svg>
          <div>
            <p class="font-medium">{{ error }}</p>
          </div>
        </div>
      </div>

      <form v-if="!success" class="mt-8 space-y-6" @submit.prevent="handleRegister">
        <div class="rounded-md shadow-sm -space-y-px">
          <div class="mb-4">
            <label
              for="email-address"
              class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
              >{{ $t('auth.email') }}</label
            >
            <input
              id="email-address"
              name="email"
              type="email"
              autocomplete="email"
              required
              v-model="email"
              :class="[
                'input-field',
                error && error.toLowerCase().includes('email') ? 'border-red-500 focus:border-red-500 focus:ring-red-500' : ''
              ]"
              :placeholder="$t('auth.emailPlaceholder')"
            />
            <p v-if="error && error.toLowerCase().includes('email')" class="mt-1 text-xs text-red-600">
              {{ error }}
            </p>
          </div>
          <div class="mb-4">
            <label
              for="password"
              class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
              >{{ $t('auth.password') }}</label
            >
            <input
              id="password"
              name="password"
              type="password"
              autocomplete="new-password"
              required
              v-model="password"
              class="input-field"
              :placeholder="$t('auth.passwordPlaceholder')"
            />

            <!-- Password Strength Indicator -->
            <div v-if="password" class="mt-2">
              <div class="flex justify-between items-center mb-1">
                <span class="text-xs text-gray-500 dark:text-gray-400"
                  >{{ $t('auth.passwordStrength.title') }}</span
                >
                <span
                  :class="[
                    'text-xs font-medium',
                    passwordStrength.label === 'Weak' ? 'text-red-500' : '',
                    passwordStrength.label === 'Medium'
                      ? 'text-yellow-500'
                      : '',
                    passwordStrength.label === 'Strong' ? 'text-green-500' : '',
                  ]"
                  >{{ passwordStrength.translatedLabel }}</span
                >
              </div>
              <div
                class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5"
              >
                <div
                  :class="[
                    'h-1.5 rounded-full transition-all duration-300',
                    passwordStrength.color,
                  ]"
                  :style="{ width: passwordStrength.width }"
                ></div>
              </div>

              <!-- Password Requirements -->
              <ul class="mt-2 space-y-1 text-xs">
                <li
                  :class="
                    passwordChecks.minLength
                      ? 'text-green-500'
                      : 'text-gray-400 dark:text-gray-500'
                  "
                >
                  <span class="mr-1">{{
                    passwordChecks.minLength ? "✓" : "○"
                  }}</span>
                  {{ $t('auth.passwordStrength.min') }}
                </li>
                <li
                  :class="
                    passwordChecks.hasUppercase
                      ? 'text-green-500'
                      : 'text-gray-400 dark:text-gray-500'
                  "
                >
                  <span class="mr-1">{{
                    passwordChecks.hasUppercase ? "✓" : "○"
                  }}</span>
                  {{ $t('auth.passwordStrength.upper') }}
                </li>
                <li
                  :class="
                    passwordChecks.hasLowercase
                      ? 'text-green-500'
                      : 'text-gray-400 dark:text-gray-500'
                  "
                >
                  <span class="mr-1">{{
                    passwordChecks.hasLowercase ? "✓" : "○"
                  }}</span>
                  {{ $t('auth.passwordStrength.lower') }}
                </li>
                <li
                  :class="
                    passwordChecks.hasNumber
                      ? 'text-green-500'
                      : 'text-gray-400 dark:text-gray-500'
                  "
                >
                  <span class="mr-1">{{
                    passwordChecks.hasNumber ? "✓" : "○"
                  }}</span>
                  {{ $t('auth.passwordStrength.number') }}
                </li>
                <li
                  :class="
                    passwordChecks.hasSpecial
                      ? 'text-green-500'
                      : 'text-gray-400 dark:text-gray-500'
                  "
                >
                  <span class="mr-1">{{
                    passwordChecks.hasSpecial ? "✓" : "○"
                  }}</span>
                  {{ $t('auth.passwordStrength.special') }}
                </li>
              </ul>
            </div>
          </div>
          <div class="mb-4">
            <label
              for="confirm-password"
              class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1 mt-4"
              >{{ $t('auth.confirmPassword') }}</label
            >
            <input
              id="confirm-password"
              name="confirm-password"
              type="password"
              autocomplete="new-password"
              required
              v-model="confirmPassword"
              class="input-field"
              :placeholder="$t('auth.passwordPlaceholder')"
            />
            <p
              v-if="confirmPassword && !passwordsMatch"
              class="mt-1 text-xs text-red-500"
            >
              {{ $t('auth.passwordsDoNotMatch') }}
            </p>
            <p
              v-if="confirmPassword && passwordsMatch"
              class="mt-1 text-xs text-green-500"
            >
              {{ $t('auth.passwordsMatch') }}
            </p>
          </div>
        </div>

        <div>
          <button
            type="submit"
            :disabled="loading || !passwordsMatch"
            class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-70 disabled:cursor-not-allowed transition-colors"
          >
            <span
              v-if="loading"
              class="absolute left-0 inset-y-0 flex items-center pl-3"
            >
              <svg
                class="animate-spin h-5 w-5 text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  class="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  stroke-width="4"
                ></circle>
                <path
                  class="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
            </span>
            {{ loading ? $t('auth.creatingAccount') : $t('auth.signUp') }}
          </button>
        </div>

        <!-- Or divider -->
        <div class="relative">
          <div class="absolute inset-0 flex items-center">
            <div class="w-full border-t border-gray-300 dark:border-gray-600"></div>
          </div>
          <div class="relative flex justify-center text-sm">
            <span class="px-2 bg-white dark:bg-dark-surface text-gray-500">{{ $t('auth.signUpWith') }}</span>
          </div>
        </div>

        <!-- Google Sign-Up Button -->
        <div class="mt-4">
          <div v-if="googleClientId" id="google-signup-btn" class="flex justify-center"></div>
          <div v-else class="text-center text-sm text-gray-500">
            <RouterLink to="/login" class="text-primary-600 hover:text-primary-500">
              {{ $t('auth.signInWithGoogle') }}
            </RouterLink>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>
