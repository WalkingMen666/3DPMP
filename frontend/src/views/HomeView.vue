<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const message = ref('Hello from Vue!')
const backendMessage = ref('Waiting for backend...')

onMounted(async () => {
  try {
    const response = await axios.get('/api/hello/')
    backendMessage.value = response.data.message
  } catch (error) {
    backendMessage.value = 'Error connecting to backend: ' + error.message
  }
})
</script>

<template>
  <div class="container">
    <h1>3DPMP - F&C Studio</h1>
    <div class="card">
      <h2>Frontend Status</h2>
      <p>{{ message }}</p>
    </div>
    <div class="card">
      <h2>Backend Status</h2>
      <p>{{ backendMessage }}</p>
    </div>
    <div class="nav-links">
      <router-link to="/login">登入</router-link>
      <router-link to="/register">註冊</router-link>
    </div>
  </div>
</template>

<style scoped>
.container {
  font-family: Arial, sans-serif;
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  text-align: center;
}
.card {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 1.5rem;
  margin: 1rem 0;
  background-color: #f9f9f9;
}
h1 {
  color: #2c3e50;
}
.nav-links {
  margin-top: 2rem;
}
.nav-links a {
  margin: 0 1rem;
  padding: 0.75rem 1.5rem;
  background-color: #4CAF50;
  color: white;
  text-decoration: none;
  border-radius: 4px;
}
.nav-links a:hover {
  background-color: #45a049;
}
</style>
