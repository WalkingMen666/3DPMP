<script setup>
import { ref } from "vue";

const form = ref({
  name: "",
  email: "",
  subject: "",
  message: "",
});

const submitted = ref(false);
const loading = ref(false);

const submitForm = () => {
  loading.value = true;
  // Simulate API call
  setTimeout(() => {
    loading.value = false;
    submitted.value = true;
  }, 1000);
};
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <h1
      class="text-4xl font-bold text-gray-900 dark:text-white mb-4 text-center"
    >
      {{ $t('contact.title') }}
    </h1>
    <p class="text-lg text-gray-600 dark:text-gray-300 mb-12 text-center">
      {{ $t('contact.subtitle') }}
    </p>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-12">
      <!-- Contact Form -->
      <div class="card p-8">
        <div v-if="submitted" class="text-center py-8">
          <svg
            class="mx-auto h-16 w-16 text-green-500 mb-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M5 13l4 4L19 7"
            />
          </svg>
          <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            {{ $t('contact.success.title') }}
          </h3>
          <p class="text-gray-600 dark:text-gray-300">
            {{ $t('contact.success.message') }}
          </p>
        </div>

        <form v-else @submit.prevent="submitForm" class="space-y-6">
          <div>
            <label
              class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
              >{{ $t('contact.form.name') }}</label
            >
            <input
              type="text"
              v-model="form.name"
              required
              class="input-field"
              :placeholder="$t('contact.form.namePlaceholder')"
            />
          </div>
          <div>
            <label
              class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
              >{{ $t('contact.form.email') }}</label
            >
            <input
              type="email"
              v-model="form.email"
              required
              class="input-field"
              :placeholder="$t('contact.form.emailPlaceholder')"
            />
          </div>
          <div>
            <label
              class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
              >{{ $t('contact.form.subject') }}</label
            >
            <select v-model="form.subject" required class="input-field">
              <option value="">{{ $t('contact.form.selectTopic') }}</option>
              <option value="general">{{ $t('contact.form.topics.general') }}</option>
              <option value="support">{{ $t('contact.form.topics.support') }}</option>
              <option value="billing">{{ $t('contact.form.topics.billing') }}</option>
              <option value="partnership">{{ $t('contact.form.topics.partnership') }}</option>
            </select>
          </div>
          <div>
            <label
              class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
              >{{ $t('contact.form.message') }}</label
            >
            <textarea
              v-model="form.message"
              required
              rows="5"
              class="input-field"
              :placeholder="$t('contact.form.messagePlaceholder')"
            ></textarea>
          </div>
          <button
            type="submit"
            :disabled="loading"
            class="w-full btn-primary py-3"
          >
            {{ loading ? $t('contact.form.sending') : $t('contact.form.send') }}
          </button>
        </form>
      </div>

      <!-- Contact Info -->
      <div class="space-y-8">
        <div class="card p-6">
          <div class="flex items-start space-x-4">
            <svg
              class="w-6 h-6 text-primary-500 flex-shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
            <div>
              <h3 class="font-semibold text-gray-900 dark:text-white">{{ $t('contact.info.email') }}</h3>
              <p class="text-gray-600 dark:text-gray-300">support@3dpmp.com</p>
            </div>
          </div>
        </div>

        <div class="card p-6">
          <div class="flex items-start space-x-4">
            <svg
              class="w-6 h-6 text-primary-500 flex-shrink-0"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
              />
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            <div>
              <h3 class="font-semibold text-gray-900 dark:text-white">
                {{ $t('contact.info.address') }}
              </h3>
              <p class="text-gray-600 dark:text-gray-300 whitespace-pre-line">{{ $t('contact.info.addressValue') }}</p>
            </div>
          </div>
        </div>

        <div class="card p-6">
          <div class="flex items-start space-x-4">
            <svg
              class="w-6 h-6 text-primary-500 flex-shrink-0"
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
            <div>
              <h3 class="font-semibold text-gray-900 dark:text-white">
                {{ $t('contact.info.hours') }}
              </h3>
              <p class="text-gray-600 dark:text-gray-300 whitespace-pre-line">{{ $t('contact.info.hoursValue') }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
