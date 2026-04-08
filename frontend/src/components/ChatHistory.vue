<script setup lang="ts">
import { useChatStore } from '../stores/chat'

const chatStore = useChatStore()

function formatTime(timestamp: number) {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - timestamp

  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`

  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}
</script>

<template>
  <div class="h-full flex flex-col bg-white/50 backdrop-blur">
    <!-- 标题 -->
    <div class="p-4 border-b border-secondary/20">
      <button
        @click="chatStore.createSession()"
        class="w-full py-3 bg-primary text-white rounded-2xl font-medium hover:bg-primary/90 transition-colors shadow-lg shadow-primary/30 flex items-center justify-center gap-2"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
        </svg>
        新对话
      </button>
    </div>

    <!-- 对话列表 -->
    <div class="flex-1 overflow-y-auto p-2 space-y-2">
      <div
        v-for="session in chatStore.sessions"
        :key="session.id"
        :class="[
          'p-3 rounded-2xl cursor-pointer transition-all duration-200 group',
          session.id === chatStore.currentSessionId
            ? 'bg-primary/20 border-2 border-primary'
            : 'bg-cream/50 hover:bg-white/70'
        ]"
        @click="chatStore.selectSession(session.id)"
      >
        <div class="flex items-start justify-between">
          <div class="flex-1 min-w-0">
            <p class="font-medium text-coffee truncate">{{ session.title }}</p>
            <p class="text-xs text-coffee/50 mt-1">
              {{ session.messages.length }} 条消息 · {{ formatTime(session.updatedAt) }}
            </p>
          </div>
          <button
            @click.stop="chatStore.deleteSession(session.id)"
            class="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded-full transition-opacity"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
