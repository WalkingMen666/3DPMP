<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <h1 class="text-4xl font-bold text-gray-900 dark:text-white mb-8">
      {{ $t('pricing.title') }}
    </h1>

    <p class="text-lg text-gray-600 dark:text-gray-300 mb-12">
      {{ $t('pricing.subtitle') }}
    </p>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <!-- Free Plan -->
      <div class="card p-8 text-center">
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          {{ $t('pricing.free.title') }}
        </h3>
        <div class="text-4xl font-bold text-gray-900 dark:text-white mb-4">
          $0<span class="text-lg font-normal text-gray-500">{{ $t('pricing.month') }}</span>
        </div>
        <ul class="space-y-3 text-gray-600 dark:text-gray-300 mb-8 text-left">
          <li class="flex items-center">
            <svg
              class="w-5 h-5 text-green-500 mr-2"
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
            {{ $t('pricing.free.feat1') }}
          </li>
          <li class="flex items-center">
            <svg
              class="w-5 h-5 text-green-500 mr-2"
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
            {{ $t('pricing.free.feat2') }}
          </li>
          <li class="flex items-center">
            <svg
              class="w-5 h-5 text-green-500 mr-2"
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
            {{ $t('pricing.free.feat3') }}
          </li>
        </ul>
        <button class="w-full btn-secondary">{{ $t('pricing.free.cta') }}</button>
      </div>

      <!-- Pro Plan -->
      <div class="card p-8 text-center border-2 border-primary-500 relative">
        <div
          class="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-primary-500 text-white px-4 py-1 rounded-full text-sm font-semibold"
        >
          {{ $t('pricing.pro.popular') }}
        </div>
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          {{ $t('pricing.pro.title') }}
        </h3>
        <div class="text-4xl font-bold text-gray-900 dark:text-white mb-4">
          $19<span class="text-lg font-normal text-gray-500">{{ $t('pricing.month') }}</span>
        </div>
        <ul class="space-y-3 text-gray-600 dark:text-gray-300 mb-8 text-left">
          <li class="flex items-center">
            <svg
              class="w-5 h-5 text-green-500 mr-2"
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
            {{ $t('pricing.pro.feat1') }}
          </li>
          <li class="flex items-center">
            <svg
              class="w-5 h-5 text-green-500 mr-2"
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
            {{ $t('pricing.pro.feat2') }}
          </li>
          <li class="flex items-center">
            <svg
              class="w-5 h-5 text-green-500 mr-2"
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
            {{ $t('pricing.pro.feat3') }}
          </li>
          <li class="flex items-center">
            <svg
              class="w-5 h-5 text-green-500 mr-2"
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
            {{ $t('pricing.pro.feat4') }}
          </li>
        </ul>
        <button class="w-full btn-primary">{{ $t('pricing.pro.cta') }}</button>
      </div>

      <!-- Enterprise Plan -->
      <div class="card p-8 text-center">
        <h3 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">
          {{ $t('pricing.enterprise.title') }}
        </h3>
        <div class="text-4xl font-bold text-gray-900 dark:text-white mb-4">
          {{ $t('pricing.enterprise.price') }}
        </div>
        <ul class="space-y-3 text-gray-600 dark:text-gray-300 mb-8 text-left">
          <li class="flex items-center">
            <svg
              class="w-5 h-5 text-green-500 mr-2"
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
            {{ $t('pricing.enterprise.feat1') }}
          </li>
          <li class="flex items-center">
            <svg
              class="w-5 h-5 text-green-500 mr-2"
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
            {{ $t('pricing.enterprise.feat2') }}
          </li>
          <li class="flex items-center">
            <svg
              class="w-5 h-5 text-green-500 mr-2"
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
            {{ $t('pricing.enterprise.feat3') }}
          </li>
          <li class="flex items-center">
            <svg
              class="w-5 h-5 text-green-500 mr-2"
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
            {{ $t('pricing.enterprise.feat4') }}
          </li>
        </ul>
        <button class="w-full btn-secondary">{{ $t('pricing.enterprise.cta') }}</button>
      </div>
    </div>
  </div>
</template>
