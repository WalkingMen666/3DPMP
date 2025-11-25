<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const message = ref('Hello from Vue!')
const backendMessage = ref('Waiting for backend...')

onMounted(async () => {
  try {
    // Note: In docker-compose, frontend (browser) accesses backend via localhost:8000 if exposed,
    // OR via the nginx proxy at /api/.
    // Since we set up nginx to proxy /api/ to backend:8000, we should use /api/hello/
    const response = await axios.get('/api/hello/')
    backendMessage.value = response.data.message
  } catch (error) {
    backendMessage.value = 'Error connecting to backend: ' + error.message
  }
})
</script>

<template>
  <div class="container">
    <h1>3DPMP Hello World</h1>
    <div class="card">
      <h2>Frontend Status</h2>
      <p>{{ message }}</p>
    </div>
    <div class="card">
      <h2>Backend Status</h2>
      <p>{{ backendMessage }}</p>
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
</style>
