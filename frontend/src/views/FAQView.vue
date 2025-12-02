<script setup>
import { ref } from "vue";

const faqs = ref([
  {
    question: "What file formats do you support?",
    answer:
      "We primarily support STL files, which is the most common format for 3D printing. We also accept OBJ and 3MF files.",
    isOpen: false,
  },
  {
    question: "How does the automatic slicing work?",
    answer:
      "When you upload or view a model, our system automatically calculates print parameters including estimated print time, material usage, and weight. This uses industry-standard slicer algorithms.",
    isOpen: false,
  },
  {
    question: "Can I sell my own 3D models?",
    answer:
      "Yes! You can upload your own 3D models to our marketplace and set your own prices. We take a small commission on each sale to cover platform costs.",
    isOpen: false,
  },
  {
    question: "What materials are available for printing?",
    answer:
      "We offer PLA, PETG, ABS, and various specialty materials. Each material has different properties suitable for different applications.",
    isOpen: false,
  },
  {
    question: "How long does shipping take?",
    answer:
      "Print times vary based on model complexity. After printing, standard shipping typically takes 3-7 business days. Express shipping options are also available.",
    isOpen: false,
  },
  {
    question: "Do you offer refunds?",
    answer:
      "Yes, we offer full refunds for defective prints. For digital model purchases, refunds are handled case-by-case. Please contact support for assistance.",
    isOpen: false,
  },
]);

const toggleFaq = (index) => {
  faqs.value[index].isOpen = !faqs.value[index].isOpen;
};
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <h1
      class="text-4xl font-bold text-gray-900 dark:text-white mb-4 text-center"
    >
      Frequently Asked Questions
    </h1>
    <p class="text-lg text-gray-600 dark:text-gray-300 mb-12 text-center">
      Find answers to common questions about our platform.
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
      <p class="text-gray-600 dark:text-gray-300 mb-4">Still have questions?</p>
      <router-link to="/contact" class="btn-primary">Contact Us</router-link>
    </div>
  </div>
</template>
