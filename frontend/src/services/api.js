import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

function streamApiRequest(endpoint, body, onStreamEvent) {
  fetch(`http://localhost:8000/api/v1${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  .then(async response => {
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP error! status: ${response.status}, details: ${errorText}`);
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n\n').filter(line => line.trim() !== '');
      
      for (const line of lines) {
        if (line.startsWith('data:')) {
          const jsonStr = line.substring(5);
          if (jsonStr) {
            try {
              const eventData = JSON.parse(jsonStr);
              onStreamEvent(eventData);
            } catch (e) {
              console.error("Failed to parse stream event JSON:", jsonStr, e);
            }
          }
        }
      }
    }
  })
  .catch(error => {
    console.error('Streaming failed:', error);
    onStreamEvent({ event: 'error', message: `Connection to server failed: ${error.message}` });
  });
}

export default {
  startConversation(text, imageFile, onStreamEvent) {
    const formData = new FormData();
    if (text) formData.append('text_input', text);
    if (imageFile) formData.append('image', imageFile);

    fetch('http://localhost:8000/api/v1/conversations/stream', {
      method: 'POST',
      body: formData,
    })
    .then(async response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n\n');
        
        for (const line of lines) {
          if (line.startsWith('data:')) {
            const jsonStr = line.substring(5);
            if (jsonStr) {
              try {
                const eventData = JSON.parse(jsonStr);
                onStreamEvent(eventData);
              } catch (e) {
                console.error("Failed to parse stream event JSON:", jsonStr, e);
              }
            }
          }
        }
      }
    })
    .catch(error => {
      console.error('Streaming failed:', error);
      onStreamEvent({ event: 'error', message: 'Connection to server failed.' });
    });
  },

  analyzeComponents(conversationId, messageId) {
    return apiClient.post(`/conversations/${conversationId}/analyze-components`, {
      analysis_message_id: messageId,
    });
  },

  generateGuide(conversationId, messageId, onStreamEvent) {
    streamApiRequest(`/conversations/${conversationId}/generate-deployment-guide/stream`, { analysis_message_id: messageId }, onStreamEvent);
  },

  generateCode(conversationId, messageId, onStreamEvent) {
    streamApiRequest(`/conversations/${conversationId}/generate-code/stream`, { analysis_message_id: messageId }, onStreamEvent);
  },

  generateSchematic(conversationId, messageId, onStreamEvent) {
    streamApiRequest(`/conversations/${conversationId}/generate-schematic/stream`, { analysis_message_id: messageId }, onStreamEvent);
  },

  getConversationHistory() {
    return apiClient.get('/conversations');
  },

  deleteConversation(conversationId) {
    return apiClient.delete(`/conversations/${conversationId}`);
  },
};