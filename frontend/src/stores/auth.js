import { defineStore } from 'pinia';
import api from '@/services/api';
import { useChatStore } from '@/stores/chat';
import router from '@/router';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || null,
    username: localStorage.getItem('username') || null,
    error: null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
  },
  actions: {
    async login(username, password) {
      this.error = null;
      try {
        const response = await api.login(username, password);
        // Note: api.login uses fetch, so response is already the JSON data
        const { access_token } = response;
        this.token = access_token;
        this.username = username;
        localStorage.setItem('token', access_token);
        localStorage.setItem('username', username);
        
        // After successful login, fetch the chat history
        const chatStore = useChatStore();
        await chatStore.fetchHistory();

        // Redirect to the main chat interface
        router.push('/');
      } catch (err) {
        console.error('Login error:', err);
        this.error = err.detail || 'Login failed.';
      }
    },
    async register(username, password) {
        this.error = null;
        try {
            const response = await api.register(username, password);
            // After successful registration, automatically log the user in
            await this.login(username, password);
        } catch (err) {
            console.error('Registration error:', err);
            this.error = err.response?.data?.detail || 'Registration failed.';
            throw err; // Don't continue to login if registration failed
        }
    },
    logout() {
      const chatStore = useChatStore();
      chatStore.clearConversations(); // Clear chat history from state

      this.token = null;
      this.username = null;
      localStorage.removeItem('token');
      localStorage.removeItem('username');
      router.push('/login');
    },
  },
});
