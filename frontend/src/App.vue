<template>
  <div id="chat-container">
    <div class="sidebar">
      <h2>Conversations</h2>
      <div class="conversation-list">
        <div
          v-for="convo in chatStore.conversations"
          :key="convo.id"
          class="conversation-item"
          :class="{ active: convo.id === chatStore.currentConversationId }"
          @click="chatStore.currentConversationId = convo.id"
        >
          {{ convo.title }}
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
              @analyze-components="handleAnalyzeComponents(message.id)"
              @generate-guide="handleGenerateGuide(message.id)"
              @generate-code="handleGenerateCode(message.id)"
              @generate-schematic="handleGenerateSchematic(message.id)"
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
import { ref } from 'vue';
import { useChatStore } from '@/stores/chat';
import MessageRenderer from '@/components/MessageRenderer.vue';

const chatStore = useChatStore();
const textInput = ref('');
const selectedFile = ref(null);

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
}

.conversation-list {
  overflow-y: auto;
}

.conversation-item {
  padding: 0.75rem;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 0.5rem;
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
