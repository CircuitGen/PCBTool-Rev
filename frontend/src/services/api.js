import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1', // The address of our FastAPI backend
  headers: {
    'Content-Type': 'application/json',
  },
});

export default {
  startConversation(text, imageFile) {
    const formData = new FormData();
    // Append data only if it exists
    if (text) {
      formData.append('text_input', text);
    }
    if (imageFile) {
      formData.append('image', imageFile);
    }

    return apiClient.post('/conversations', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  analyzeComponents(conversationId, messageId) {
    const params = new URLSearchParams();
    params.append('analysis_message_id', messageId);
    return apiClient.post(`/conversations/${conversationId}/analyze-components`, params);
  },

  generateGuide(conversationId, messageId) {
    const params = new URLSearchParams();
    params.append('analysis_message_id', messageId);
    return apiClient.post(`/conversations/${conversationId}/generate-deployment-guide`, params);
  },

  generateCode(conversationId, messageId) {
    const params = new URLSearchParams();
    params.append('analysis_message_id', messageId);
    return apiClient.post(`/conversations/${conversationId}/generate-code`, params);
  },

  generateSchematic(conversationId, messageId) {
    const params = new URLSearchParams();
    params.append('analysis_message_id', messageId);
    return apiClient.post(`/conversations/${conversationId}/generate-schematic`, params);
  },
};
