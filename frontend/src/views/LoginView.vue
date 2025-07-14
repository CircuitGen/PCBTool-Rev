<template>
  <div class="auth-container">
    <div class="auth-form">
      <h2>Login</h2>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="username">Username</label>
          <input type="text" v-model="username" id="username" autocomplete="username" required />
        </div>
        <div class="form-group">
          <label for="password">Password</label>
          <input type="password" v-model="password" id="password" autocomplete="current-password" required />
        </div>
        <div v-if="authStore.error" class="error-message">{{ authStore.error }}</div>
        <button type="submit">Login</button>
      </form>
      <p>
        Don't have an account? <router-link to="/register">Register here</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useAuthStore } from '@/stores/auth';

const username = ref('');
const password = ref('');
const authStore = useAuthStore();

const handleLogin = () => {
  authStore.login(username.value, password.value);
};
</script>

<style scoped>
/* Styles will be shared, so we can add them to main.css */
</style>
