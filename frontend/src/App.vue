<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useChatStore } from './stores/chat'
import ChatMessage from './components/ChatMessage.vue'
import ChatInput from './components/ChatInput.vue'
import QuickActions from './components/QuickActions.vue'
import ChatHistory from './components/ChatHistory.vue'

const chatStore = useChatStore()
const showHistory = ref(false)
const messagesContainer = ref<HTMLElement | null>(null)

onMounted(async () => {
  chatStore.init()

  // 检查后端连接状态
  try {
    const res = await fetch('/api/status')
    if (res.ok) {
      const data = await res.json()
      chatStore.isConnected = data.ready
    }
  } catch {
    chatStore.isConnected = false
  }

  // 定期检查连接状态
  setInterval(async () => {
    try {
      const res = await fetch('/api/status')
      if (res.ok) {
        const data = await res.json()
        chatStore.isConnected = data.ready
      }
    } catch {
      chatStore.isConnected = false
    }
  }, 30000) // 每30秒检查一次
})

function handleSend(message: string) {
  chatStore.sendMessage(message)
}

function handleQuickAction(question: string) {
  chatStore.sendMessage(question)
}

// 滚动到底部
function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

async function checkConnection() {
  try {
    const res = await fetch('/api/status')
    if (res.ok) {
      const data = await res.json()
      chatStore.isConnected = data.ready
    }
  } catch {
    chatStore.isConnected = false
  }
}
</script>

<template>
  <div class="h-screen flex">
    <!-- 历史记录侧边栏 (移动端) -->
    <div
      :class="[
        'fixed inset-0 z-50 bg-black/50 transition-opacity lg:hidden',
        showHistory ? 'opacity-100' : 'opacity-0 pointer-events-none'
      ]"
      @click="showHistory = false"
    >
      <div
        :class="[
          'w-72 h-full bg-cream transition-transform',
          showHistory ? 'translate-x-0' : '-translate-x-full'
        ]"
        @click.stop
      >
        <ChatHistory />
      </div>
    </div>

    <!-- 历史记录侧边栏 (桌面端) -->
    <div class="hidden lg:block w-72 border-r border-secondary/20">
      <ChatHistory />
    </div>

    <!-- 主聊天区域 -->
    <div class="flex-1 flex flex-col">
      <!-- 顶部导航 -->
      <header class="bg-white/80 backdrop-blur shadow-sm px-4 py-3 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <button
            @click="showHistory = true"
            class="lg:hidden p-2 hover:bg-secondary/10 rounded-xl transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-coffee" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <div class="flex items-center gap-2">
            <span class="text-2xl">🍳</span>
            <h1 class="font-bold text-coffee text-lg">尝尝咸淡</h1>
          </div>
        </div>

        <!-- 状态指示 -->
        <div class="flex items-center gap-2">
          <div :class="['w-2 h-2 rounded-full', chatStore.isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400']"></div>
          <span class="text-sm text-coffee/60">{{ chatStore.isConnected ? '已连接' : '未连接' }}</span>
          <button
            v-if="!chatStore.isConnected"
            @click="checkConnection"
            class="text-xs px-2 py-1 bg-secondary/20 text-secondary rounded-full hover:bg-secondary/30"
          >
            重试
          </button>
        </div>
      </header>

      <!-- 消息区域 -->
      <div ref="messagesContainer" class="flex-1 overflow-y-auto p-4 space-y-4">
        <!-- 欢迎信息 -->
        <div v-if="chatStore.currentMessages.length === 0" class="flex flex-col items-center justify-center h-full text-center">
          <div class="text-6xl mb-4 animate-bounce">👨‍🍳</div>
          <h2 class="text-2xl font-bold text-coffee mb-2">你好，我是烹饪助手</h2>
          <p class="text-coffee/60 mb-2 max-w-md">可以问我任何关于烹饪的问题，比如菜谱、食材搭配、烹饪技巧等</p>

          <!-- 初始化提示 -->
          <p v-if="!chatStore.isConnected" class="text-sm text-secondary mb-4">
            🔄 RAG 系统初始化中，首次加载可能需要 1-2 分钟...
          </p>

          <QuickActions @select="handleQuickAction" :disabled="!chatStore.isConnected" />
        </div>

        <!-- 消息列表 -->
        <template v-else>
          <ChatMessage
            v-for="msg in chatStore.currentMessages"
            :key="msg.id"
            :message="msg"
          />
        </template>
      </div>

      <!-- 快捷问题 -->
      <div v-if="chatStore.currentMessages.length > 0 && !chatStore.isLoading" class="px-4 pb-2">
        <QuickActions @select="handleQuickAction" />
      </div>

      <!-- 输入框 -->
      <div class="p-4">
        <ChatInput @send="handleSend" />
      </div>
    </div>
  </div>
</template>
