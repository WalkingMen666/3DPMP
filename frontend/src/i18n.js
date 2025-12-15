import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import zhTW from './locales/zh-TW.json'

// Get saved language from localStorage, default to 'en'
const savedLanguage = localStorage.getItem('settings_language') || 'en'

const i18n = createI18n({
  legacy: false, // Use Composition API mode
  locale: savedLanguage,
  fallbackLocale: 'en',
  messages: {
    en,
    'zh-TW': zhTW
  }
})

export default i18n
