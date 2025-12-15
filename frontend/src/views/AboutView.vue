<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-8">
      {{ $t('about.title') }}
    </h1>

    <div class="prose dark:prose-invert max-w-none">
      <div class="card p-8 mb-8">
        <h2 class="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
          {{ $t('about.mission.title') }}
        </h2>
        <p class="text-gray-600 dark:text-gray-300 mb-4">
          {{ $t('about.mission.description') }}
        </p>
      </div>

      <div class="card p-8 mb-8">
        <h2 class="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
          {{ $t('about.offer.title') }}
        </h2>
        <ul class="space-y-3 text-gray-600 dark:text-gray-300">
          <li class="flex items-start">
            <svg
              class="w-6 h-6 text-primary-500 mr-2 flex-shrink-0"
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
            <span
              ><strong>{{ $t('about.offer.marketplace') }}:</strong>
              {{ $t('about.offer.marketplaceDesc') }}</span
            >
          </li>
          <li class="flex items-start">
            <svg
              class="w-6 h-6 text-primary-500 mr-2 flex-shrink-0"
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
            <span
              ><strong>{{ $t('about.offer.slicing') }}:</strong>
              {{ $t('about.offer.slicingDesc') }}</span
            >
          </li>
          <li class="flex items-start">
            <svg
              class="w-6 h-6 text-primary-500 mr-2 flex-shrink-0"
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
            <span
              ><strong>{{ $t('about.offer.services') }}:</strong>
              {{ $t('about.offer.servicesDesc') }}</span
            >
          </li>
          <li class="flex items-start">
            <svg
              class="w-6 h-6 text-primary-500 mr-2 flex-shrink-0"
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
            <span
              ><strong>{{ $t('about.offer.tools') }}:</strong>
              {{ $t('about.offer.toolsDesc') }}</span
            >
          </li>
        </ul>
      </div>

      <div class="card p-8">
        <h2 class="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
          {{ $t('about.team.title') }}
        </h2>
        <p class="text-gray-600 dark:text-gray-300">
          {{ $t('about.team.description') }}
        </p>
      </div>
    </div>
  </div>
</template>
