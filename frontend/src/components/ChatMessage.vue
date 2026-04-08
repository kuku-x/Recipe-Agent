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
      'flex gap-3',
      isUser ? 'justify-end' : 'justify-start'
    ]"
  >
    <!-- 助手头像 -->
    <div
      v-if="!isUser"
      class="w-10 h-10 rounded-full bg-gradient-to-br from-secondary to-accent flex items-center justify-center text-2xl flex-shrink-0 shadow-lg"
    >
      🍳
    </div>

    <div
      :class="[
        'max-w-[75%] px-5 py-3 shadow-lg',
        isUser
          ? 'bg-primary text-white rounded-3xl rounded-br-md'
          : 'bg-white text-coffee rounded-3xl rounded-bl-md'
      ]"
    >
      <p class="whitespace-pre-wrap break-words leading-relaxed">
        {{ message.content }}<span v-if="message.isStreaming" class="inline-flex gap-0.5 ml-1">
          <span class="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style="animation-delay: 0ms"></span>
          <span class="w-1.5 h-1.5 bg-secondary rounded-full animate-bounce" style="animation-delay: 150ms"></span>
          <span class="w-1.5 h-1.5 bg-accent rounded-full animate-bounce" style="animation-delay: 300ms"></span>
        </span>
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

    <!-- 用户头像 -->
    <div
      v-if="isUser"
      class="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-2xl flex-shrink-0 shadow-lg"
    >
      👨
    </div>
  </div>
</template>
