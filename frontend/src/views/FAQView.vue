<script setup>
import { ref, computed } from "vue";
import { useI18n } from "vue-i18n";

const { t } = useI18n();

const faqKeys = ['formats', 'slicing', 'sell', 'materials', 'shipping', 'refunds'];
const openStates = ref(new Array(faqKeys.length).fill(false));

const faqs = computed(() => {
  return faqKeys.map((key, index) => ({
    question: t(`faq.questions.${key}.q`),
    answer: t(`faq.questions.${key}.a`),
    isOpen: openStates.value[index]
  }));
});

const toggleFaq = (index) => {
  openStates.value[index] = !openStates.value[index];
};
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <h1
      class="text-4xl font-bold text-gray-900 dark:text-white mb-4 text-center"
    >
      {{ $t('faq.title') }}
    </h1>
    <p class="text-lg text-gray-600 dark:text-gray-300 mb-12 text-center">
      {{ $t('faq.subtitle') }}
    </p>

    <div class="space-y-4">
      <div
        v-for="(faq, index) in faqs"
        :key="index"
        class="card overflow-hidden"
      >
        <button
          @click="toggleFaq(index)"
          class="w-full px-6 py-4 text-left flex justify-between items-center hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
        >
          <span class="font-semibold text-gray-900 dark:text-white">{{
            faq.question
          }}</span>
          <svg
            :class="[
              'w-5 h-5 text-gray-500 transition-transform duration-200',
              faq.isOpen ? 'rotate-180' : '',
            ]"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </button>
        <div v-show="faq.isOpen" class="px-6 pb-4">
          <p class="text-gray-600 dark:text-gray-300">{{ faq.answer }}</p>
        </div>
      </div>
    </div>

    <div class="mt-12 text-center">
      <p class="text-gray-600 dark:text-gray-300 mb-4">{{ $t('faq.stillHaveQuestions') }}</p>
      <router-link to="/contact" class="btn-primary">{{ $t('faq.contact') }}</router-link>
    </div>
  </div>
</template>
