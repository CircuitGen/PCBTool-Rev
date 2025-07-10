<template>
  <div id="chat-container">
    <div class="sidebar">
      <div class="sidebar-header">
        <h2>Conversations</h2>
        <button @click="handleNewConversation" class="new-convo-btn">+</button>
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
          <button @click.stop="handleDeleteConversation(convo.id)" class="delete-btn">×</button>
        </div>
      </div>
    </div>
    <div class="main-content">
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
import MessageRenderer from '@/components/MessageRenderer.vue';

const chatStore = useChatStore();
const textInput = ref('');
const selectedFile = ref(null);

// Fetch history when the component is mounted
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

const handleStartConversation = async () => {
  if (!selectedFile.value && !textInput.value.trim()) {
    alert('Please provide either an image or a text prompt.');
    return;
  }
  await chatStore.startConversation(textInput.value, selectedFile.value);
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
/* Using one global style file for simplicity */
:root {
  --border-color: #e0e0e0;
  --background-light: #f7f9fc;
  --background-white: #ffffff;
  --text-primary: #202124;
  --text-secondary: #5f6368;
  --accent-color: #1a73e8;
  --accent-color-hover: #185abc;
  --assistant-bg: #f1f3f4;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  background-color: var(--background-light);
  color: var(--text-primary);
}

#app {
  display: flex;
  height: 100vh;
}

#chat-container {
  display: flex;
  width: 100%;
}

.sidebar {
  width: 250px;
  background-color: var(--background-white);
  border-right: 1px solid var(--border-color);
  padding: 1rem;
  display: flex;
  flex-direction: column;
}

.sidebar h2 {
  margin-top: 0;
  color: var(--text-secondary);
  font-size: 1.2rem;
  margin-bottom: 0;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 1rem;
}

.new-convo-btn {
  background: none;
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  font-size: 1.5rem;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  padding-bottom: 4px;
}

.new-convo-btn:hover {
  background-color: var(--background-light);
  border-color: var(--accent-color);
}


.conversation-list {
  overflow-y: auto;
}

.conversation-item {
  padding: 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 0.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.convo-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.delete-btn {
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 1.2rem;
  cursor: pointer;
  visibility: hidden; /* Hidden by default */
  opacity: 0.6;
  padding: 0 0.5rem;
}

.conversation-item:hover .delete-btn {
  visibility: visible; /* Show on hover */
}

.delete-btn:hover {
  opacity: 1;
  color: #d93025; /* Red for delete */
}


.conversation-item:hover {
  background-color: var(--background-light);
}

.conversation-item.active {
  background-color: var(--accent-color);
  color: white;
}

.main-content {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.message-window {
  flex-grow: 1;
  overflow-y: auto;
  padding: 2rem;
}

.welcome-message {
  text-align: center;
  margin-top: 20vh;
  color: var(--text-secondary);
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.message {
  padding: 1rem;
  border-radius: 12px;
  max-width: 80%;
}

.message.assistant {
  background-color: var(--assistant-bg);
  align-self: flex-start;
}

.message.user {
  background-color: var(--accent-color);
  color: white;
  align-self: flex-end;
}

.message-content pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  font-size: 1rem;
  margin: 0;
}

.error-bar {
  padding: 1rem;
  background-color: #f8d7da;
  color: #721c24;
  text-align: center;
}

.input-area {
  display: flex;
  padding: 1rem;
  border-top: 1px solid var(--border-color);
  background-color: var(--background-white);
}

.input-area input[type='text'] {
  flex-grow: 1;
  border: 1px solid var(--border-color);
  border-radius: 18px;
  padding: 0.5rem 1rem;
  font-size: 1rem;
}

.input-area input[type='file'] {
  width: 120px;
}

.input-area button {
  background-color: var(--accent-color);
  color: white;
  border: none;
  border-radius: 18px;
  padding: 0.5rem 1.5rem;
  margin-left: 1rem;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.2s;
}

.input-area button:hover {
  background-color: var(--accent-color-hover);
}

.input-area button:disabled {
  background-color: #cccccc;
  cursor: not-allowed;
}
</style>