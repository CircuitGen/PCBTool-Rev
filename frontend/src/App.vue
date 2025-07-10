<template>
  <div id="chat-container">
    <div class="sidebar">
      <div class="logo-container">
        <img src="@/assets/logo.png" alt="Logo" class="logo" />
      </div>
      <div class="sidebar-header">
        <h2>Conversations</h2>
        <button @click="handleNewConversation" class="new-convo-btn" title="New Conversation">+</button>
      </div>
      <div class="conversation-list">
        <div
          v-for="convo in chatStore.conversations"
          :key="convo.id"
          class="conversation-item"
          :class="{ active: convo.id === chatStore.currentConversationId }"
          @click="chatStore.currentConversationId = convo.id"
        >
          <span class="convo-title">{{ convo.title }}</span>
          <button @click.stop="handleDeleteConversation(convo.id)" class="delete-btn" title="Delete">×</button>
        </div>
      </div>
      <div class="sidebar-footer">
        <span>{{ authStore.username }}</span>
        <button @click="authStore.logout()" class="logout-btn" title="Logout">Logout</button>
      </div>
    </div>
    <div class="main-content">
      <div class="banner-container">
        <img src="@/assets/background.jpg" alt="Banner" class="banner-image" />
      </div>
      <div class="message-window">
        <div v-if="!chatStore.currentConversationId" class="welcome-message">
          <h1>PCBTool Assistant</h1>
          <p>Upload an image and enter a prompt to start.</p>
        </div>
        <div v-else class="message-list">
          <div v-for="message in chatStore.currentMessages" :key="message.id" class="message" :class="message.role">
            <MessageRenderer 
              :content="message.content"
              :message-id="message.id"
              @analyze-components="handleAnalyzeComponents($event)"
              @generate-guide="handleGenerateGuide($event)"
              @generate-code="handleGenerateCode($event)"
              @generate-schematic="handleGenerateSchematic($event)"
            />
          </div>
        </div>
      </div>
      <div v-if="chatStore.error" class="error-bar">
        {{ chatStore.error }}
      </div>
      <div class="input-area">
        <input
          type="text"
          v-model="textInput"
          placeholder="Enter your prompt..."
          @keyup.enter="handleStartConversation"
          :disabled="chatStore.isLoading"
        />
        <input type="file" @change="handleFileChange" ref="fileInput" :disabled="chatStore.isLoading" />
        <button @click="handleStartConversation" :disabled="chatStore.isLoading">
          {{ chatStore.isLoading ? 'Processing...' : 'Send' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useChatStore } from '@/stores/chat';
import { useAuthStore } from '@/stores/auth';
import MessageRenderer from '@/components/MessageRenderer.vue';

const chatStore = useChatStore();
const authStore = useAuthStore();
const textInput = ref('');
const selectedFile = ref(null);

onMounted(() => {
  chatStore.fetchHistory();
});

const handleNewConversation = () => {
  chatStore.startNewConversation();
};

const handleDeleteConversation = (conversationId) => {
  if (confirm('Are you sure you want to delete this conversation?')) {
    chatStore.deleteConversation(conversationId);
  }
};

const handleFileChange = (event) => {
  selectedFile.value = event.target.files[0];
};

const handleStartConversation = () => {
  chatStore.startConversation(textInput.value, selectedFile.value);
  textInput.value = '';
  const fileInput = document.querySelector('input[type="file"]');
  if(fileInput) fileInput.value = '';
  selectedFile.value = null;
};

const handleAnalyzeComponents = (messageId) => {
  chatStore.analyzeComponents(messageId);
};

const handleGenerateGuide = (messageId) => {
  chatStore.generateGuide(messageId);
};

const handleGenerateCode = (messageId) => {
  chatStore.generateCode(messageId);
};

const handleGenerateSchematic = (messageId) => {
  chatStore.generateSchematic(messageId);
};
</script>

<style>
/* This is now the single source of truth for App.vue styles */
.logo-container {
  text-align: center;
  padding: 1rem 0;
  margin-bottom: 1rem;
}

.logo {
  max-width: 80%;
  height: auto;
}

.sidebar-footer {
  margin-top: auto;
  padding-top: 1rem;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logout-btn {
  background: none;
  border: 1px solid var(--border-color);
  padding: 0.4rem 0.8rem;
  border-radius: 8px;
  cursor: pointer;
}

.logout-btn:hover {
  background-color: var(--dark-secondary-bg);
}
</style>
