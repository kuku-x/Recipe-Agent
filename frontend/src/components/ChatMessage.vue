<script setup lang="ts">
import { computed } from 'vue'
import type { Message } from '../stores/chat'

const props = defineProps<{
  message: Message
}>()

const isUser = computed(() => props.message.role === 'user')
</script>

<template>
  <div
    :class="[
      'flex animate-bounce-in',
      isUser ? 'justify-end' : 'justify-start'
    ]"
  >
    <div
      :class="[
        'max-w-[75%] px-5 py-3 shadow-lg',
        isUser
          ? 'bg-primary text-white rounded-3xl rounded-br-md'
          : 'bg-white text-coffee rounded-3xl rounded-bl-md'
      ]"
    >
      <p class="whitespace-pre-wrap break-words leading-relaxed">
        {{ message.content }}
        <span v-if="message.isStreaming" class="typing-cursor">|</span>
      </p>
      <p
        v-if="!message.isStreaming"
        :class="[
          'text-xs mt-1 opacity-70',
          isUser ? 'text-white/80' : 'text-coffee/50'
        ]"
      >
        {{ new Date(message.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }}
      </p>
    </div>
  </div>
</template>
