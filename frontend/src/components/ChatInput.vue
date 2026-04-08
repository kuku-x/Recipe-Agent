<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  (e: 'send', message: string): void
}>()

const message = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)

function handleSend() {
  if (message.value.trim()) {
    emit('send', message.value)
    message.value = ''
    if (textareaRef.value) {
      textareaRef.value.style.height = 'auto'
    }
  }
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

function autoResize() {
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
    textareaRef.value.style.height = Math.min(textareaRef.value.scrollHeight, 150) + 'px'
  }
}
</script>

<template>
  <div class="bg-white rounded-3xl shadow-xl p-4 border-2 border-secondary/20">
    <div class="flex gap-3">
      <textarea
        ref="textareaRef"
        v-model="message"
        @keydown="handleKeydown"
        @input="autoResize"
        placeholder="问问菜谱..."
        rows="1"
        class="flex-1 resize-none bg-cream/50 rounded-2xl px-4 py-3 text-coffee placeholder-coffee/40 focus:outline-none focus:ring-0"
      />
      <button
        @click="handleSend"
        :disabled="!message.trim()"
        :class="[
          'px-6 py-3 rounded-2xl font-medium transition-all duration-200',
          message.trim()
            ? 'bg-primary text-white hover:bg-primary/90 hover:scale-105 active:scale-95 shadow-lg shadow-primary/30'
            : 'bg-gray-200 text-gray-400 cursor-not-allowed'
        ]"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path d="M10.894 2.553a1 1 0 00-1.788 0l-7 14a1 1 0 001.169 1.409l5-1.429A1 1 0 009 15.571V11a1 1 0 112 0v4.571a1 1 0 00.725.962l5 1.428a1 1 0 001.17-1.408l-7-14z" />
        </svg>
      </button>
    </div>
  </div>
</template>
