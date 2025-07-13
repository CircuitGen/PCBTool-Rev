import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/stores/auth';
import { useChatStore } from '@/stores/chat';
import App from '@/App.vue'; // The main chat interface
import LoginView from '@/views/LoginView.vue';
import RegisterView from '@/views/RegisterView.vue';

const routes = [
  {
    path: '/',
    name: 'Chat',
    component: App,
    meta: { requiresAuth: true },
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginView,
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterView,
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore();
  const isAuthenticated = authStore.isAuthenticated;

  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login');
  } else if ((to.name === 'Login' || to.name === 'Register') && isAuthenticated) {
    next('/');
  } else {
    // If navigating to an authenticated route and we haven't loaded history yet
    if (to.meta.requiresAuth && isAuthenticated) {
      const chatStore = useChatStore();
      if (Object.keys(chatStore.conversations).length === 0) {
        await chatStore.fetchHistory();
      }
    }
    next();
  }
});

export default router;
