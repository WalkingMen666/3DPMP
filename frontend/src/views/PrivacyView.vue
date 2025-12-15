<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-8">
      {{ $t('privacy.title') }}
    </h1>

    <div class="prose dark:prose-invert max-w-none">
      <p class="text-gray-600 dark:text-gray-300 mb-6">
        {{ $t('privacy.lastUpdated') }}
      </p>

      <div class="card p-8 mb-6">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          {{ $t('privacy.sections.collection.title') }}
        </h2>
        <p class="text-gray-600 dark:text-gray-300 mb-4">
          {{ $t('privacy.sections.collection.description') }}
        </p>
        <ul
          class="list-disc list-inside text-gray-600 dark:text-gray-300 space-y-2"
        >
          <li v-for="(item, index) in $tm('privacy.sections.collection.items')" :key="index">
            {{ $rt(item) }}
          </li>
        </ul>
      </div>

      <div class="card p-8 mb-6">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          {{ $t('privacy.sections.usage.title') }}
        </h2>
        <p class="text-gray-600 dark:text-gray-300">
          {{ $t('privacy.sections.usage.description') }}
        </p>
      </div>

      <div class="card p-8 mb-6">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          {{ $t('privacy.sections.security.title') }}
        </h2>
        <p class="text-gray-600 dark:text-gray-300">
          {{ $t('privacy.sections.security.description') }}
        </p>
      </div>

      <div class="card p-8 mb-6">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          {{ $t('privacy.sections.rights.title') }}
        </h2>
        <p class="text-gray-600 dark:text-gray-300">
          {{ $t('privacy.sections.rights.description') }}
        </p>
      </div>

      <div class="card p-8">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          {{ $t('privacy.sections.contact.title') }}
        </h2>
        <p class="text-gray-600 dark:text-gray-300">
          {{ $t('privacy.sections.contact.description') }}
          <a
            href="mailto:privacy@3dpmp.com"
            class="text-primary-600 hover:text-primary-500"
            >privacy@3dpmp.com</a
          >.
        </p>
      </div>
    </div>
  </div>
</template>
