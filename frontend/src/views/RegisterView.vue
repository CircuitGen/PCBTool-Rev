<template>
  <div class="auth-container">
    <div class="auth-form">
      <h2>Register</h2>
      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label for="username">Username</label>
          <input type="text" v-model="username" id="username" autocomplete="username" required />
        </div>
        <div class="form-group">
          <label for="password">Password</label>
          <input type="password" v-model="password" id="password" autocomplete="new-password" required />
        </div>
        <div v-if="authStore.error" class="error-message">{{ authStore.error }}</div>
        <button type="submit">Register</button>
      </form>
      <p>
        Already have an account? <router-link to="/login">Login here</router-link>
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

const handleRegister = () => {
  authStore.register(username.value, password.value);
};
</script>
