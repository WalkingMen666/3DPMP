<script setup>
import { ref, onMounted } from "vue";
import { useRouter, RouterLink } from "vue-router";
import { useAuthStore } from "../stores/auth";
import axios from "axios";

const router = useRouter();
const auth = useAuthStore();

const email = ref("");
const password = ref("");
const loading = ref(false);
const googleLoading = ref(false);
const error = ref("");
const googleClientId = ref(null);

// Fetch Google Client ID
onMounted(async () => {
  try {
    const response = await axios.get('/api/auth/google/client-id/');
    googleClientId.value = response.data.client_id;
    
    // Load Google Sign-In script
    if (googleClientId.value) {
      loadGoogleScript();
    }
  } catch (e) {
    console.log('Google OAuth not configured');
  }
});

const loadGoogleScript = () => {
  // If script already loaded, just initialize
  if (window.google) {
    initializeGoogle();
    return;
  }
  
  if (document.getElementById('google-signin-script')) {
    // Script exists but not loaded yet, wait for it
    const checkGoogle = setInterval(() => {
      if (window.google) {
        clearInterval(checkGoogle);
        initializeGoogle();
      }
    }, 100);
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
    const btnEl = document.getElementById('google-signin-btn');
    if (btnEl) {
      window.google.accounts.id.renderButton(btnEl, { 
        theme: 'outline', 
        size: 'large',
        width: '100%',
        text: 'signin_with',
      });
    } else if (attempts < 10) {
      setTimeout(() => tryRenderButton(attempts + 1), 100);
    }
  };
  tryRenderButton();
};

const handleGoogleCallback = async (response) => {
  googleLoading.value = true;
  error.value = "";
  
  try {
    await auth.googleLogin(response.credential);
    router.push("/dashboard");
  } catch (e) {
    error.value = e.message || "Google sign-in failed. Please try again.";
  } finally {
    googleLoading.value = false;
  }
};

const handleLogin = async () => {
  loading.value = true;
  error.value = "";
  try {
    await auth.login(email.value, password.value);
    router.push("/dashboard");
  } catch (e) {
    error.value =
      e.message || "Invalid email or password. Please check your credentials.";
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
          Welcome back
        </h2>
        <p class="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
          Or
          <RouterLink
            to="/register"
            class="font-medium text-primary-600 hover:text-primary-500"
          >
            create a new account
          </RouterLink>
        </p>
      </div>
      <form class="mt-8 space-y-6" @submit.prevent="handleLogin">
        <div class="rounded-md shadow-sm -space-y-px">
          <div class="mb-4">
            <label
              for="email-address"
              class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
              >Email address</label
            >
            <input
              id="email-address"
              name="email"
              type="email"
              autocomplete="email"
              required
              v-model="email"
              class="input-field"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label
              for="password"
              class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
              >Password</label
            >
            <input
              id="password"
              name="password"
              type="password"
              autocomplete="current-password"
              required
              v-model="password"
              class="input-field"
              placeholder="••••••••"
            />
          </div>
        </div>

        <div
          v-if="error"
          class="text-red-500 text-sm text-center bg-red-50 dark:bg-red-900/20 p-3 rounded-lg"
        >
          {{ error }}
        </div>

        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <input
              id="remember-me"
              name="remember-me"
              type="checkbox"
              class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            />
            <label
              for="remember-me"
              class="ml-2 block text-sm text-gray-900 dark:text-gray-300"
            >
              Remember me
            </label>
          </div>

          <div class="text-sm">
            <a
              href="#"
              class="font-medium text-primary-600 hover:text-primary-500"
            >
              Forgot your password?
            </a>
          </div>
        </div>

        <div>
          <button
            type="submit"
            :disabled="loading"
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
            {{ loading ? "Signing in..." : "Sign in" }}
          </button>
        </div>

        <div class="relative">
          <div class="absolute inset-0 flex items-center">
            <div
              class="w-full border-t border-gray-300 dark:border-gray-600"
            ></div>
          </div>
          <div class="relative flex justify-center text-sm">
            <span class="px-2 bg-white dark:bg-dark-surface text-gray-500"
              >Or continue with</span
            >
          </div>
        </div>

        <!-- Google Sign-In Button -->
        <div class="grid grid-cols-1 gap-3">
          <div v-if="googleClientId" id="google-signin-btn" class="flex justify-center"></div>
          <button
            v-else
            type="button"
            disabled
            class="w-full inline-flex justify-center py-2 px-4 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm bg-gray-100 dark:bg-gray-800 text-sm font-medium text-gray-400 dark:text-gray-500 cursor-not-allowed"
          >
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M12.545,10.239v3.821h5.445c-0.712,2.315-2.647,3.972-5.445,3.972c-3.332,0-6.033-2.701-6.033-6.032s2.701-6.032,6.033-6.032c1.498,0,2.866,0.549,3.921,1.453l2.814-2.814C17.503,2.988,15.139,2,12.545,2C7.021,2,2.543,6.477,2.543,12s4.478,10,10.002,10c8.396,0,10.249-7.85,9.426-11.748L12.545,10.239z"
              />
            </svg>
            <span class="ml-2">Google (Not configured)</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
