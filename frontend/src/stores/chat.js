import { defineStore } from 'pinia';
import api from '@/services/api';

export const useChatStore = defineStore('chat', {
  state: () => ({
    conversations: {}, // Store conversations by ID
    currentConversationId: null,
    isLoading: false,
    error: null,
  }),

  getters: {
    currentMessages: (state) => {
      if (!state.currentConversationId || !state.conversations[state.currentConversationId]) {
        return [];
      }
      return state.conversations[state.currentConversationId].messages;
    },
  },

  actions: {
    async startConversation(text, imageFile) {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await api.startConversation(text, imageFile);
        const { conversation_id, message } = response.data;

        this.conversations[conversation_id] = {
          id: conversation_id,
          title: text.substring(0, 30),
          messages: [message],
        };
        this.currentConversationId = conversation_id;
        
      } catch (err) {
        this.error = err.response?.data?.detail || 'An unknown error occurred.';
        console.error(err);
      } finally {
        this.isLoading = false;
      }
    },

    async analyzeComponents(messageId) {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await api.analyzeComponents(this.currentConversationId, messageId);
        const newMessage = response.data;
        
        // Add the new message to the current conversation
        this.conversations[this.currentConversationId].messages.push(newMessage);

      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to analyze components.';
        console.error(err);
      } finally {
        this.isLoading = false;
      }
    },

    async generateGuide(messageId) {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await api.generateGuide(this.currentConversationId, messageId);
        this.conversations[this.currentConversationId].messages.push(response.data.message);
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to generate guide.';
      } finally {
        this.isLoading = false;
      }
    },

    async generateCode(messageId) {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await api.generateCode(this.currentConversationId, messageId);
        this.conversations[this.currentConversationId].messages.push(response.data.message);
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to generate code.';
      } finally {
        this.isLoading = false;
      }
    },

    async generateSchematic(messageId) {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await api.generateSchematic(this.currentConversationId, messageId);
        this.conversations[this.currentConversationId].messages.push(response.data.message);
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to generate schematic.';
      } finally {
        this.isLoading = false;
      }
    },
  },
});
