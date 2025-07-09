<template>
  <div class="message-content">
    <div v-if="type === 'initial_analysis'">
      <h3>需求文档</h3>
      <div v-html="renderMarkdown(data.需求文档)"></div>
      <hr />
      <h3>BOM 文件</h3>
      <div v-html="renderMarkdown(data.BOM文件)"></div>
      <div class="actions">
        <button @click="onAnalyzeComponents">Analyze Components</button>
      </div>
    </div>
    <div v-else-if="type === 'component_analysis'">
      <p>{{ data.status }}</p>
      <table class="component-table">
        <thead>
          <tr>
            <th>器件名称</th>
            <th>单价</th>
            <th>数量</th>
            <th>总价</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, index) in data.components" :key="index">
            <td>{{ item.器件名称 }}</td>
            <td>{{ item.单价 }}</td>
            <td>{{ item.数量 }}</td>
            <td>{{ item.总价 }}</td>
          </tr>
        </tbody>
      </table>
      <div class="actions">
        <button @click="$emit('generate-guide')">Generate Guide</button>
        <button @click="$emit('generate-code')">Generate Code</button>
        <button @click="$emit('generate-schematic')">Generate Schematic</button>
      </div>
    </div>
    <div v-else-if="type === 'deployment_guide'">
      <h3>Deployment Guide</h3>
      <div v-html="renderMarkdown(data.text)"></div>
      <audio v-if="data.audio_url" :src="'http://localhost:8000' + data.audio_url" controls>
        Your browser does not support the audio element.
      </audio>
    </div>
    <div v-else-if="type === 'generated_code' || type === 'schematic_code'">
      <h3>{{ type === 'generated_code' ? 'Generated Code' : 'Schematic Code' }}</h3>
      <pre class="code-block"><code>{{ data.code }}</code></pre>
    </div>
    <div v-else>
      <!-- Fallback for other message types -->
      <pre>{{ content }}</pre>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue';
import { marked } from 'marked';

const props = defineProps({
  content: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(['analyze-components']);

const type = computed(() => props.content.type);
const data = computed(() => props.content.data);

const renderMarkdown = (md) => {
  if (!md) return '';
  // This is a basic implementation. For production, you'd want to sanitize the HTML.
  return marked.parse(md);
};

const onAnalyzeComponents = () => {
  emit('analyze-components');
};
</script>

<style scoped>
.message-content {
  width: 100%;
}
h3 {
  margin-top: 1rem;
  margin-bottom: 0.5rem;
}
hr {
  border: none;
  border-top: 1px solid var(--border-color);
  margin: 1rem 0;
}
.actions {
  margin-top: 1rem;
  text-align: right;
}
button {
  background-color: var(--accent-color);
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.6rem 1rem;
  cursor: pointer;
  font-size: 0.9rem;
  transition: background-color 0.2s;
}
button:hover {
  background-color: var(--accent-color-hover);
}

.component-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

.component-table th, .component-table td {
  border: 1px solid var(--border-color);
  padding: 0.5rem;
  text-align: left;
}

.component-table th {
  background-color: var(--background-light);
}

.code-block {
  background-color: #2d2d2d;
  color: #f8f8f2;
  padding: 1rem;
  border-radius: 8px;
  overflow-x: auto;
  white-space: pre;
}

audio {
  margin-top: 1rem;
  width: 100%;
}
</style>
