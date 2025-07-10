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
    startConversation(text, imageFile) {
      this.isLoading = true;
      this.error = null;
      
      // Create a temporary message to show progress
      const tempMessageId = `temp-${Date.now()}`;
      const tempMessage = {
        id: tempMessageId,
        role: 'assistant',
        content: {
          type: 'loading',
          data: { status: 'Initializing...' }
        },
        created_at: new Date().toISOString(),
      };

      // Add the temporary message to a new temporary conversation
      const tempConvoId = `temp-convo-${Date.now()}`;
      this.conversations[tempConvoId] = {
        id: tempConvoId,
        title: text ? text.substring(0, 30) : "Image Analysis",
        messages: [tempMessage],
      };
      this.currentConversationId = tempConvoId;

      const onStreamEvent = (eventData) => {
        const { event } = eventData;

        if (event === 'node_started' || event === 'node_finished') {
          // Update the loading message status
          tempMessage.content.data.status = eventData.data?.title || event;
        }

        if (event === 'workflow_finished') {
          // The workflow is done, but we wait for our custom 'conversation_created' event
          tempMessage.content.data.status = 'Finalizing and saving results...';
        }
        
        if (event === 'conversation_created') {
          // This is our final, custom event from the backend
          const { conversation_id, message_content } = eventData;
          
          // Replace the temporary conversation with the real one
          delete this.conversations[tempConvoId];
          
          this.conversations[conversation_id] = {
            id: conversation_id,
            title: text ? text.substring(0, 30) : "Image Analysis",
            messages: [{
              id: Date.now(), // A proper ID would be better, but this works
              role: 'assistant',
              content: message_content,
              created_at: new Date().toISOString(),
            }],
          };
          this.currentConversationId = conversation_id;
          this.isLoading = false;
        }

        if (event === 'error') {
          this.error = eventData.message || 'An unknown streaming error occurred.';
          this.isLoading = false;
        }
      };

      api.startConversation(text, imageFile, onStreamEvent);
    },

    async analyzeComponents(messageId) {
      this.isLoading = true;
      this.error = null;
      try {
        const response = await api.analyzeComponents(this.currentConversationId, messageId);
        const newMessage = response.data;
        this.conversations[this.currentConversationId].messages.push({
          ...newMessage,
          content: newMessage.content,
        });
      } catch (err) {
        this.error = err.response?.data?.detail || 'Failed to analyze components.';
        console.error(err);
      } finally {
        this.isLoading = false;
      }
    },

    _handleStreamedGeneration(apiMethod, messageId, finalContentType) {
      this.isLoading = true;
      this.error = null;

      const tempMessage = {
        id: `temp-${Date.now()}`,
        role: 'assistant',
        content: { 
          type: 'loading', 
          data: { 
            status: 'Initializing...',
            streamedContent: '' // Initialize a place for the text stream
          } 
        },
        created_at: new Date().toISOString(),
      };
      this.conversations[this.currentConversationId].messages.push(tempMessage);

      const onStreamEvent = (eventData) => {
        const { event } = eventData;

        // Update status for node events
        if (event === 'node_started' || event === 'node_finished') {
          tempMessage.content.data.status = eventData.data?.title || event;
        }

        // Handle incoming text chunks for agent messages
        if (event === 'agent_message') {
          tempMessage.content.type = finalContentType; // Evolve the message type
          tempMessage.content.data.streamedContent += eventData.answer;
          // Keep the 'code' property updated for live rendering
          tempMessage.content.data.code = tempMessage.content.data.streamedContent;
        }

        // Handle the final message from the backend
        if (event === 'final_message') {
          const index = this.conversations[this.currentConversationId].messages.findIndex(m => m.id === tempMessage.id);
          if (index !== -1) {
            // Replace the temporary message with the final, complete one
            this.conversations[this.currentConversationId].messages.splice(index, 1, {
              ...tempMessage,
              id: Date.now(), // Use a more permanent ID
              content: eventData.content,
            });
          }
          this.isLoading = false;
        }
        
        if (event === 'error') {
          this.error = eventData.message || 'An unknown streaming error occurred.';
          this.isLoading = false;
          tempMessage.content.type = 'error'; // Mark the temp message as an error
          tempMessage.content.data.status = this.error;
        }
      };

      apiMethod(this.currentConversationId, messageId, onStreamEvent);
    },

    startNewConversation() {
      this.currentConversationId = null;
    },

    async deleteConversation(conversationId) {
      try {
        await api.deleteConversation(conversationId);
        
        // Remove from local state
        delete this.conversations[conversationId];

        // If the deleted one was the current one, reset the view
        if (this.currentConversationId === conversationId) {
          this.currentConversationId = null;
        }

      } catch (err) {
        this.error = 'Failed to delete conversation.';
        console.error(err);
      }
    },

    generateGuide(messageId) {
      this._handleStreamedGeneration(api.generateGuide, messageId, 'deployment_guide');
    },

    generateCode(messageId) {
      this._handleStreamedGeneration(api.generateCode, messageId, 'generated_code');
    },

    generateSchematic(messageId) {
      this._handleStreamedGeneration(api.generateSchematic, messageId, 'schematic_code');
    },

    async fetchHistory() {
      this.isLoading = true;
      try {
        const response = await api.getConversationHistory();
        const history = response.data;
        // Normalize the history data into the store's structure
        const conversations = {};
        for (const convo of history) {
          conversations[convo.id] = {
            id: convo.id,
            title: convo.title,
            messages: convo.messages.map(msg => ({
              ...msg,
              content: JSON.parse(msg.content) // Pre-parse content
            })),
          };
        }
        this.conversations = conversations;
        // Optionally, set the current conversation to the most recent one
        if (history.length > 0) {
          this.currentConversationId = history[0].id;
        }
      } catch (err) {
        this.error = 'Failed to load conversation history.';
        console.error(err);
      } finally {
        this.isLoading = false;
      }
    },
  },
});
