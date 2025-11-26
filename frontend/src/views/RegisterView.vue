<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()
const email = ref('')
const password1 = ref('')
const password2 = ref('')
const error = ref('')
const loading = ref(false)

const handleRegister = async () => {
  loading.value = true
  error.value = ''

  if (password1.value !== password2.value) {
    error.value = '密碼不一致'
    loading.value = false
    return
  }

  try {
    await axios.post('/api/auth/registration/', {
      email: email.value,
      password1: password1.value,
      password2: password2.value
    })
    
    alert('註冊成功！請登入')
    router.push('/login')
  } catch (err) {
    console.error(err)
    const data = err.response?.data
    if (data) {
      // 處理各種錯誤格式
      if (data.email) error.value = data.email[0]
      else if (data.password1) error.value = data.password1[0]
      else if (data.password2) error.value = data.password2[0]
      else if (data.non_field_errors) error.value = data.non_field_errors[0]
      else error.value = '註冊失敗'
    } else {
      error.value = '註冊失敗'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="register-container">
    <div class="register-card">
      <h2>註冊帳號</h2>
      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label for="email">Email</label>
          <input 
            id="email" 
            v-model="email" 
            type="email" 
            required 
            autocomplete="email"
            placeholder="輸入您的 Email"
          />
        </div>
        
        <div class="form-group">
          <label for="password1">密碼</label>
          <input 
            id="password1" 
            v-model="password1" 
            type="password" 
            required 
            autocomplete="new-password"
            placeholder="輸入密碼"
          />
        </div>

        <div class="form-group">
          <label for="password2">確認密碼</label>
          <input 
            id="password2" 
            v-model="password2" 
            type="password" 
            required 
            autocomplete="new-password"
            placeholder="再次輸入密碼"
          />
        </div>

        <div v-if="error" class="error-message">
          {{ error }}
        </div>

        <button type="submit" :disabled="loading">
          {{ loading ? '註冊中...' : '註冊' }}
        </button>
      </form>

      <div class="login-link">
        已有帳號？<router-link to="/login">登入</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f0f2f5;
}

.register-card {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
  width: 100%;
  max-width: 400px;
}

h2 {
  text-align: center;
  margin-bottom: 1.5rem;
  color: #333;
}

.form-group {
  margin-bottom: 1rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  color: #666;
}

input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 1rem;
  box-sizing: border-box;
}

button {
  width: 100%;
  padding: 0.75rem;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  margin-top: 1rem;
}

button:disabled {
  background-color: #ccc;
}

button:hover:not(:disabled) {
  background-color: #45a049;
}

.error-message {
  color: red;
  margin-top: 0.5rem;
  font-size: 0.9rem;
  text-align: center;
}

.login-link {
  text-align: center;
  margin-top: 1rem;
  color: #666;
}

.login-link a {
  color: #4CAF50;
  text-decoration: none;
}

.login-link a:hover {
  text-decoration: underline;
}
</style>
