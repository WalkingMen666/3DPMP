<script setup>
import { ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { useAuthStore } from "../stores/auth";
import { useCartStore } from "../stores/cart";
import ThemeToggle from "./ThemeToggle.vue";

const auth = useAuthStore();
const cart = useCartStore();
const router = useRouter();
const isMenuOpen = ref(false);

const handleLogout = () => {
  auth.logout();
  router.push("/login");
};
</script>

<template>
  <nav
    class="sticky top-0 z-50 bg-white/80 dark:bg-dark-bg/80 backdrop-blur-md border-b border-gray-100 dark:border-gray-800"
  >
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16">
        <!-- Logo -->
        <div class="flex items-center">
          <RouterLink to="/" class="flex items-center space-x-2">
            <img
              src="/assets/logo.png"
              alt="3DPMP Logo"
              class="h-8 w-auto object-contain"
            />
            <span
              class="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-300"
            >
              3DPMP
            </span>
          </RouterLink>

          <!-- Desktop Navigation -->
          <div class="hidden md:flex ml-10 space-x-8">
            <RouterLink
              to="/"
              class="text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 font-medium transition-colors"
            >
              Home
            </RouterLink>
            <RouterLink
              to="/models"
              class="text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 font-medium transition-colors"
            >
              Marketplace
            </RouterLink>
            <RouterLink
              v-if="auth.isAuthenticated"
              to="/dashboard"
              class="text-gray-600 dark:text-gray-300 hover:text-primary-600 dark:hover:text-primary-400 font-medium transition-colors"
            >
              Dashboard
            </RouterLink>
          </div>
        </div>

        <!-- Right Side Actions -->
        <div class="hidden md:flex items-center space-x-4">
          <ThemeToggle />

          <template v-if="auth.isAuthenticated">
            <RouterLink
              to="/cart"
              class="relative p-2 text-gray-600 dark:text-gray-300 hover:text-primary-600 transition-colors"
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
                  d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"
                />
              </svg>
              <span
                v-if="cart.itemCount > 0"
                class="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/4 -translate-y-1/4 bg-red-500 rounded-full"
                >{{ cart.itemCount }}</span
              >
            </RouterLink>

            <div class="relative group">
              <button class="flex items-center space-x-2 focus:outline-none">
                <img
                  :src="auth.user?.avatar"
                  alt="User"
                  class="w-8 h-8 rounded-full border-2 border-primary-500"
                />
                <span
                  class="text-sm font-medium text-gray-700 dark:text-gray-200"
                  >{{ auth.user?.name }}</span
                >
              </button>

              <!-- Dropdown -->
              <div
                class="absolute right-0 mt-2 w-48 bg-white dark:bg-dark-surface rounded-lg shadow-xl border border-gray-100 dark:border-gray-700 py-1 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 transform origin-top-right z-50"
              >
                <RouterLink
                  to="/dashboard"
                  class="block px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700"
                  >My Profile</RouterLink
                >
                <RouterLink
                  v-if="auth.user?.is_employee"
                  to="/admin"
                  class="block px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700"
                >
                  <span class="flex items-center">
                    <svg class="w-4 h-4 mr-2 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                    Admin Dashboard
                  </span>
                </RouterLink>
                <div
                  class="border-t border-gray-100 dark:border-gray-700 my-1"
                ></div>
                <button
                  @click="handleLogout"
                  class="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                >
                  Sign out
                </button>
              </div>
            </div>
          </template>

          <template v-else>
            <RouterLink
              to="/login"
              class="text-gray-600 dark:text-gray-300 hover:text-primary-600 font-medium transition-colors"
            >
              Log in
            </RouterLink>
            <RouterLink to="/register" class="btn-primary text-sm">
              Sign up
            </RouterLink>
          </template>
        </div>

        <!-- Mobile menu button -->
        <div class="flex items-center md:hidden space-x-4">
          <ThemeToggle />
          <button
            @click="isMenuOpen = !isMenuOpen"
            class="text-gray-600 dark:text-gray-300 hover:text-gray-900 focus:outline-none"
          >
            <svg
              class="h-6 w-6"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                v-if="!isMenuOpen"
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 6h16M4 12h16M4 18h16"
              />
              <path
                v-else
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile Menu -->
    <div
      v-show="isMenuOpen"
      class="md:hidden bg-white dark:bg-dark-surface border-t border-gray-100 dark:border-gray-800 animate-slide-up"
    >
      <div class="px-2 pt-2 pb-3 space-y-1 sm:px-3">
        <RouterLink
          to="/"
          class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 dark:text-gray-200 hover:text-primary-600 hover:bg-gray-50 dark:hover:bg-gray-800"
          >Home</RouterLink
        >
        <RouterLink
          to="/models"
          class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 dark:text-gray-200 hover:text-primary-600 hover:bg-gray-50 dark:hover:bg-gray-800"
          >Marketplace</RouterLink
        >
        <RouterLink
          v-if="auth.isAuthenticated"
          to="/dashboard"
          class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 dark:text-gray-200 hover:text-primary-600 hover:bg-gray-50 dark:hover:bg-gray-800"
          >Dashboard</RouterLink
        >

        <template v-if="!auth.isAuthenticated">
          <RouterLink
            to="/login"
            class="block px-3 py-2 rounded-md text-base font-medium text-gray-700 dark:text-gray-200 hover:text-primary-600 hover:bg-gray-50 dark:hover:bg-gray-800"
            >Log in</RouterLink
          >
          <RouterLink
            to="/register"
            class="block px-3 py-2 rounded-md text-base font-medium text-primary-600 bg-primary-50 dark:bg-primary-900/20"
            >Sign up</RouterLink
          >
        </template>
        <template v-else>
          <button
            @click="handleLogout"
            class="block w-full text-left px-3 py-2 rounded-md text-base font-medium text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
          >
            Sign out
          </button>
        </template>
      </div>
    </div>
  </nav>
</template>
