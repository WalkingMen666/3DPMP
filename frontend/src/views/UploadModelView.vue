```vue
<script setup>
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { useModelsStore } from "@/stores/models";
import { useAuthStore } from "@/stores/auth";
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const router = useRouter();
const modelsStore = useModelsStore();
const authStore = useAuthStore();

// Form data
const modelName = ref("");
const description = ref("");
const category = ref("Other");
const tags = ref("");
const stlFile = ref(null);
const thumbnailFile = ref(null);
const imageFiles = ref([]);

// UI state
const dragging = ref(false);
const uploading = ref(false);
const progress = ref(0);
const error = ref("");
const step = ref(1); // 1: Upload STL, 2: Add Details, 3: Add Images

// Validation state
const showValidation = ref(false);

// Preview URLs
const thumbnailPreview = ref(null);
const imagePreviews = ref([]);

// Category options
const categories = computed(() => [
  { value: "Toys", label: t('marketplace.categoriesList.Toys') },
  { value: "Home", label: t('marketplace.categoriesList.Home') },
  { value: "Gadgets", label: t('marketplace.categoriesList.Gadgets') },
  { value: "Art", label: t('marketplace.categoriesList.Art') },
  { value: "Fashion", label: t('marketplace.categoriesList.Fashion') },
  { value: "Tools", label: t('marketplace.categoriesList.Tools') },
  { value: "Education", label: t('marketplace.categoriesList.Education') },
  { value: "Other", label: t('marketplace.categoriesList.Other') },
]);

// Check auth
if (!authStore.isAuthenticated) {
  router.push("/login");
}

const canProceed = computed(() => {
  if (step.value === 1) return stlFile.value !== null;
  if (step.value === 2) return modelName.value.trim() !== "";
  return true;
});

const handleDrop = (e) => {
  dragging.value = false;
  showValidation.value = false;
  const file = e.dataTransfer.files[0];
  if (file && file.name.toLowerCase().endsWith(".stl")) {
    stlFile.value = file;
    error.value = "";
  } else {
    error.value = t('upload.validation.uploadStl');
  }
};

const handleFileSelect = (e) => {
  showValidation.value = false;
  const file = e.target.files[0];
  if (file) {
    stlFile.value = file;
    error.value = "";
  } else {
    error.value = t('upload.validation.uploadStl');
  }
};

const handleThumbnailSelect = (e) => {
  const file = e.target.files[0];
  if (file && file.type.startsWith("image/")) {
    thumbnailFile.value = file;
    thumbnailPreview.value = URL.createObjectURL(file);
  }
};

const handleImagesSelect = (e) => {
  const files = Array.from(e.target.files);
  const validImages = files.filter((f) => f.type.startsWith("image/"));

  validImages.forEach((file) => {
    imageFiles.value.push(file);
    imagePreviews.value.push(URL.createObjectURL(file));
  });
};

const removeImage = (index) => {
  imageFiles.value.splice(index, 1);
  URL.revokeObjectURL(imagePreviews.value[index]);
  imagePreviews.value.splice(index, 1);
};

const removeThumbnail = () => {
  if (thumbnailPreview.value) {
    URL.revokeObjectURL(thumbnailPreview.value);
  }
  thumbnailFile.value = null;
  thumbnailPreview.value = null;
};

const nextStep = () => {
  if (!canProceed.value) {
    showValidation.value = true;
    if (step.value === 1) {
      error.value = t('upload.validation.stlRequired');
    } else if (step.value === 2) {
      error.value = t('upload.validation.nameRequired');
    }
    return;
  }
  showValidation.value = false;
  error.value = ""; // Clear general error if validation passes
  if (step.value < 3) {
    step.value++;
  }
};

const prevStep = () => {
  showValidation.value = false;
  error.value = ""; // Clear general error
  if (step.value > 1) {
    step.value--;
  }
};

const uploadModel = async () => {
  if (!stlFile.value || !modelName.value.trim()) {
    error.value = t('upload.validation.modelNameAndStlRequired');
    showValidation.value = true;
    return;
  }

  uploading.value = true;
  error.value = "";
  progress.value = 0;

  try {
    // Prepare form data
    const formData = new FormData();
    formData.append("model_name", modelName.value.trim());
    formData.append("description", description.value);
    formData.append("category", category.value);
    formData.append("stl_file", stlFile.value);
    formData.append("stl_file_path", stlFile.value.name);

    if (tags.value) {
      const tagList = tags.value
        .split(",")
        .map((t) => t.trim())
        .filter((t) => t);
      formData.append("tags", JSON.stringify(tagList));
    }

    // Price is NOT set by user - it will be calculated after slicing

    if (thumbnailFile.value) {
      formData.append("thumbnail", thumbnailFile.value);
    }

    // Upload model
    progress.value = 20;
    const model = await modelsStore.uploadModel(formData);
    progress.value = 60;

    // Upload additional images if any
    if (imageFiles.value.length > 0 && model?.id) {
      const imageFormData = new FormData();
      imageFiles.value.forEach((file) => {
        imageFormData.append("images", file);
      });
      await modelsStore.uploadModelImages(model.id, imageFormData);
    }

    progress.value = 100;

    // Redirect to dashboard after upload complete
    setTimeout(() => {
      router.push("/dashboard");
    }, 500);
  } catch (err) {
    error.value = err.message || t('upload.errors.failedToUpload');
    uploading.value = false;
  }
};

const resetForm = () => {
  stlFile.value = null;
  modelName.value = "";
  description.value = "";
  category.value = "Other";
  tags.value = "";
  removeThumbnail();
  imagePreviews.value.forEach((url) => URL.revokeObjectURL(url));
  imageFiles.value = [];
  imagePreviews.value = [];
  step.value = 1;
  error.value = "";
  showValidation.value = false;
};
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <h1
      class="text-3xl font-bold text-gray-900 dark:text-white mb-2 text-center"
    >
      {{ t('upload.title') }}
    </h1>
    <p class="text-gray-500 dark:text-gray-400 text-center mb-8">
      {{ t('upload.subtitle') }}
    </p>

    <!-- Progress Steps -->
    <div class="flex items-center justify-center mb-8">
      <div class="flex items-center space-x-4">
        <div
          v-for="s in 3"
          :key="s"
          class="flex items-center"
          :class="s < 3 ? 'flex-1' : ''"
        >
          <div
            class="w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-colors"
            :class="
              step >= s
                ? 'bg-primary-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-500'
            "
          >
            {{ s }}
          </div>
          <div
            v-if="s < 3"
            class="w-16 h-1 mx-2"
            :class="
              step > s
                ? 'bg-primary-600'
                : 'bg-gray-200 dark:bg-gray-700'
            "
          ></div>
        </div>
      </div>
    </div>

    <!-- Error Message -->
    <div
      v-if="error"
      class="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400"
    >
      {{ error }}
    </div>

    <!-- Step 1: Upload STL -->
    <div v-if="step === 1">
      <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
        {{ t('upload.steps.1') }}
      </h2>
      
      <!-- Validation Error Alert -->
      <div v-if="showValidation && !stlFile" class="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-300 dark:border-red-700 rounded-lg flex items-center space-x-3">
        <svg class="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <span class="text-red-700 dark:text-red-400 font-medium">{{ t('upload.validation.stlRequired') }}</span>
      </div>

      <div
        class="border-2 border-dashed rounded-2xl p-12 text-center transition-colors duration-300"
        :class="[
          showValidation && !stlFile
            ? 'border-red-500 bg-red-50 dark:bg-red-900/10'
            : dragging
              ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/10'
              : 'border-gray-300 dark:border-gray-700 hover:border-primary-400',
        ]"
        @dragover.prevent="dragging = true"
        @dragleave.prevent="dragging = false"
        @drop.prevent="handleDrop"
      >
        <div v-if="!stlFile">
          <svg
            class="mx-auto h-16 w-16"
            :class="showValidation ? 'text-red-400' : 'text-gray-400'"
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
          >
            <path
              d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
              stroke-width="2"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
          <p class="mt-4 text-lg" :class="showValidation ? 'text-red-600 dark:text-red-400' : 'text-gray-600 dark:text-gray-300'">
            <span v-if="showValidation">{{ t('upload.validation.uploadStl') }}</span>
            <span v-else>
              {{ t('upload.dragDrop') }}
              <label
                class="text-primary-600 hover:text-primary-500 cursor-pointer font-medium"
              >
                {{ t('upload.browse') }}
                <input
                  type="file"
                  class="hidden"
                  accept=".stl"
                  @change="handleFileSelect"
                />
              </label>
            </span>
          </p>
          <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
            {{ t('upload.maxSize') }}
          </p>
        </div>

        <div v-else class="space-y-4">
          <div
            class="flex items-center justify-center space-x-2 text-gray-900 dark:text-white font-medium"
          >
            <svg
              class="h-8 w-8 text-primary-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <span class="text-lg">{{ stlFile.name }}</span>
          </div>
          <p class="text-sm text-gray-500">
            {{ (stlFile.size / 1024 / 1024).toFixed(2) }} MB
          </p>
          <button
            @click="stlFile = null"
            class="text-red-600 hover:text-red-500 text-sm font-medium"
          >
            {{ t('upload.removeFile') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Step 2: Model Details -->
    <div v-if="step === 2">
      <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
        {{ t('upload.steps.2') }}
      </h2>
      
      <!-- Validation Error Alert -->
      <div v-if="showValidation && !modelName.trim()" class="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-300 dark:border-red-700 rounded-lg flex items-center space-x-3">
        <svg class="w-6 h-6 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <span class="text-red-700 dark:text-red-400 font-medium">{{ t('upload.validation.nameRequired') }}</span>
      </div>

      <div class="space-y-6">
        <!-- Model Name -->
        <div>
          <label
            class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            {{ t('upload.form.name') }} *
          </label>
          <input
            v-model="modelName"
            type="text"
            class="input-field"
            :class="showValidation && !modelName.trim() ? 'border-red-500 ring-1 ring-red-500' : ''"
            :placeholder="t('upload.form.namePlaceholder')"
            required
          />
          <p v-if="showValidation && !modelName.trim()" class="mt-1 text-sm text-red-600 dark:text-red-400">
            {{ t('upload.validation.nameRequired') }}
          </p>
        </div>

        <!-- Description -->
        <div>
          <label
            class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            {{ t('upload.form.description') }}
          </label>
          <textarea
            v-model="description"
            rows="4"
            class="input-field"
            :placeholder="t('upload.form.descriptionPlaceholder')"
          ></textarea>
        </div>

        <!-- Category -->
        <div>
          <label
            class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            {{ t('upload.form.category') }}
          </label>
          <select v-model="category" class="input-field">
            <option v-for="cat in categories" :key="cat.value" :value="cat.value">
              {{ cat.label }}
            </option>
          </select>
        </div>

        <!-- Tags -->
        <div>
          <label
            class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            {{ t('upload.form.tags') }}
          </label>
          <input
            v-model="tags"
            type="text"
            class="input-field"
            :placeholder="t('upload.form.tagsPlaceholder')"
          />
          <p class="mt-1 text-sm text-gray-500">
            {{ t('upload.form.tagsHelp') }}
          </p>
        </div>
      </div>
    </div>

    <!-- Step 3: Images -->
    <div v-if="step === 3">
      <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">
        {{ t('upload.steps.3') }}
      </h2>

      <!-- Thumbnail -->
      <div class="mb-8">
        <label
          class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
        >
          {{ t('upload.form.thumbnail') }}
        </label>
        <div class="flex items-start space-x-4">
          <div
            v-if="thumbnailPreview"
            class="relative w-32 h-32 rounded-lg overflow-hidden"
          >
            <img
              :src="thumbnailPreview"
              class="w-full h-full object-cover"
              :alt="t('upload.form.thumbnail')"
            />
            <button
              @click="removeThumbnail"
              class="absolute top-1 right-1 bg-red-500 text-white rounded-full p-1 hover:bg-red-600"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <label
            v-else
            class="w-32 h-32 border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg flex flex-col items-center justify-center cursor-pointer hover:border-primary-500"
          >
            <svg class="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            <span class="text-xs text-gray-500 mt-1">{{ t('upload.form.addThumbnail') }}</span>
            <input
              type="file"
              class="hidden"
              accept="image/*"
              @change="handleThumbnailSelect"
            />
          </label>
        </div>
      </div>

      <!-- Additional Images -->
      <div>
        <label
          class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
        >
          {{ t('upload.form.additionalImages') }}
        </label>
        <div class="grid grid-cols-4 gap-4">
          <div
            v-for="(preview, index) in imagePreviews"
            :key="index"
            class="relative aspect-square rounded-lg overflow-hidden"
          >
            <img
              :src="preview"
              class="w-full h-full object-cover"
              :alt="t('upload.form.additionalImages')"
            />
            <button
              @click="removeImage(index)"
              class="absolute top-1 right-1 bg-red-500 text-white rounded-full p-1 hover:bg-red-600"
            >
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <label
            v-if="imagePreviews.length < 8"
            class="aspect-square border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-lg flex flex-col items-center justify-center cursor-pointer hover:border-primary-500"
          >
            <svg class="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            <span class="text-xs text-gray-500 mt-1">{{ t('upload.form.addImage') }}</span>
            <input
              type="file"
              class="hidden"
              accept="image/*"
              multiple
              @change="handleImagesSelect"
            />
          </label>
        </div>
        <p class="mt-2 text-sm text-gray-500">
          You can add up to 8 images. Recommended: 1920x1080 or higher.
        </p>
      </div>
    </div>

    <!-- Upload Progress -->
    <div
      v-if="uploading"
      class="mt-8 p-6 bg-gray-50 dark:bg-gray-800 rounded-xl"
    >
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm font-medium text-gray-700 dark:text-gray-300">
          Uploading...
        </span>
        <span class="text-sm text-gray-500">{{ progress }}%</span>
      </div>
      <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5">
        <div
          class="bg-primary-600 h-2.5 rounded-full transition-all duration-300"
          :style="{ width: progress + '%' }"
        ></div>
      </div>
    </div>

    <!-- Navigation Buttons -->
    <div class="flex justify-between mt-8">
      <button
        v-if="step > 1"
        @click="prevStep"
        class="btn-secondary"
        :disabled="uploading"
      >
        ← Previous
      </button>
      <div v-else></div>

      <div class="flex space-x-4">
        <button
          @click="resetForm"
          class="btn-secondary"
          :disabled="uploading"
        >
          Reset
        </button>
        <button
          v-if="step < 3"
          @click="nextStep"
          class="btn-primary"
        >
          Next →
        </button>
        <button
          v-else
          @click="uploadModel"
          class="btn-primary"
          :disabled="uploading"
        >
          {{ uploading ? "Uploading..." : "Upload Model" }}
        </button>
      </div>
    </div>
  </div>
</template>
