<script setup>
import { computed, onMounted } from "vue";
import { useCartStore } from "../stores/cart";
import { useAuthStore } from "../stores/auth";

const cart = useCartStore();
const auth = useAuthStore();

// Fetch cart from backend on mount if authenticated
onMounted(async () => {
  if (auth.isAuthenticated) {
    await cart.fetchCart();
  } else {
    cart.loadFromLocalStorage();
  }
});

const shipping = computed(() => (cart.items.length > 0 ? 10.0 : 0));
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-8">
      Shopping Cart
    </h1>

    <div class="flex flex-col lg:flex-row gap-12">
      <!-- Cart Items -->
      <div class="flex-1 space-y-6">
        <div
          v-if="cart.items.length === 0"
          class="text-center py-12 bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50"
        >
          <svg
            class="mx-auto h-16 w-16 text-gray-300 dark:text-gray-600 mb-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"
            />
          </svg>
          <p class="text-gray-500 dark:text-gray-400 mb-4">
            Your cart is empty
          </p>
          <router-link to="/models" class="btn-primary"
            >Browse Models</router-link
          >
        </div>

        <div
          v-else
          v-for="item in cart.items"
          :key="item.id"
          class="flex items-center gap-4 p-4 bg-white dark:bg-dark-surface rounded-xl border border-gray-100 dark:border-gray-700/50"
        >
          <img
            :src="item.image"
            :alt="item.name"
            class="w-24 h-24 object-cover rounded-lg bg-gray-100 dark:bg-gray-800"
          />

          <div class="flex-1">
            <h3 class="font-semibold text-gray-900 dark:text-white">
              {{ item.name }}
            </h3>
            <p class="text-sm text-gray-500 dark:text-gray-400">
              Material: {{ item.material }}
            </p>
          </div>

          <div class="flex items-center gap-4">
            <div
              class="flex items-center border border-gray-200 dark:border-gray-700 rounded-lg"
            >
              <button
                @click="cart.updateQuantity(item.id, item.quantity - 1)"
                class="px-3 py-1 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                -
              </button>
              <span
                class="px-3 py-1 text-gray-900 dark:text-white font-medium"
                >{{ item.quantity }}</span
              >
              <button
                @click="cart.updateQuantity(item.id, item.quantity + 1)"
                class="px-3 py-1 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                +
              </button>
            </div>
            <div
              class="font-bold text-gray-900 dark:text-white w-20 text-right"
            >
              ${{ (item.price * item.quantity).toFixed(2) }}
            </div>
            <button
              @click="cart.removeItem(item.id)"
              class="text-red-500 hover:text-red-700 p-2"
            >
              <svg
                class="w-5 h-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Order Summary -->
      <div class="w-full lg:w-96">
        <div
          class="bg-white dark:bg-dark-surface rounded-xl p-6 border border-gray-100 dark:border-gray-700/50 sticky top-24"
        >
          <h2 class="text-xl font-bold text-gray-900 dark:text-white mb-6">
            Order Summary
          </h2>

          <div class="space-y-4 mb-6">
            <div class="flex justify-between text-gray-600 dark:text-gray-400">
              <span>Subtotal</span>
              <span>${{ cart.subtotal.toFixed(2) }}</span>
            </div>
            <div class="flex justify-between text-gray-600 dark:text-gray-400">
              <span>Shipping</span>
              <span>${{ shipping.toFixed(2) }}</span>
            </div>
            <div
              class="border-t border-gray-100 dark:border-gray-700 pt-4 flex justify-between font-bold text-lg text-gray-900 dark:text-white"
            >
              <span>Total</span>
              <span>${{ cart.total.toFixed(2) }}</span>
            </div>
          </div>

          <button
            :disabled="cart.items.length === 0"
            class="w-full btn-primary py-3 text-lg font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Proceed to Checkout
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
