<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-8">
      {{ $t('terms.title') }}
    </h1>

    <div class="prose dark:prose-invert max-w-none">
      <p class="text-gray-600 dark:text-gray-300 mb-6">
        {{ $t('terms.lastUpdated') }}
      </p>

      <div class="card p-8 mb-6">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          {{ $t('terms.sections.acceptance.title') }}
        </h2>
        <p class="text-gray-600 dark:text-gray-300">
          {{ $t('terms.sections.acceptance.description') }}
        </p>
      </div>

      <div class="card p-8 mb-6">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          {{ $t('terms.sections.accounts.title') }}
        </h2>
        <p class="text-gray-600 dark:text-gray-300 mb-4">
          {{ $t('terms.sections.accounts.description') }}
        </p>
        <ul
          class="list-disc list-inside text-gray-600 dark:text-gray-300 space-y-2"
        >
          <li v-for="(item, index) in $tm('terms.sections.accounts.items')" :key="index">
            {{ $rt(item) }}
          </li>
        </ul>
      </div>

      <div class="card p-8 mb-6">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          {{ $t('terms.sections.intellectual.title') }}
        </h2>
        <p class="text-gray-600 dark:text-gray-300">
          {{ $t('terms.sections.intellectual.description') }}
        </p>
      </div>

      <div class="card p-8 mb-6">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          {{ $t('terms.sections.prohibited.title') }}
        </h2>
        <p class="text-gray-600 dark:text-gray-300 mb-4">
          {{ $t('terms.sections.prohibited.description') }}
        </p>
        <ul
          class="list-disc list-inside text-gray-600 dark:text-gray-300 space-y-2"
        >
          <li v-for="(item, index) in $tm('terms.sections.prohibited.items')" :key="index">
            {{ $rt(item) }}
          </li>
        </ul>
      </div>

      <div class="card p-8 mb-6">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          {{ $t('terms.sections.payment.title') }}
        </h2>
        <p class="text-gray-600 dark:text-gray-300">
          {{ $t('terms.sections.payment.description') }}
        </p>
      </div>

      <div class="card p-8">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          {{ $t('terms.sections.liability.title') }}
        </h2>
        <p class="text-gray-600 dark:text-gray-300">
          {{ $t('terms.sections.liability.description') }}
        </p>
      </div>
    </div>
  </div>
</template>
