import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  isStreaming?: boolean
}

export interface ChatSession {
  id: string
  title: string
  messages: Message[]
  createdAt: number
  updatedAt: number
}

export const useChatStore = defineStore('chat', () => {
  // State
  const sessions = ref<ChatSession[]>([])
  const currentSessionId = ref<string | null>(null)
  const isLoading = ref(false)
  const isConnected = ref(false)

  // Getters
  const currentSession = computed(() => {
    return sessions.value.find(s => s.id === currentSessionId.value) || null
  })

  const currentMessages = computed(() => {
    return currentSession.value?.messages || []
  })

  // Actions
  function createSession(): ChatSession {
    const session: ChatSession = {
      id: Date.now().toString(),
      title: '新对话',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now()
    }
    sessions.value.unshift(session)
    currentSessionId.value = session.id
    saveToLocalStorage()
    return session
  }

  function selectSession(id: string) {
    currentSessionId.value = id
  }

  function deleteSession(id: string) {
    const index = sessions.value.findIndex(s => s.id === id)
    if (index !== -1) {
      sessions.value.splice(index, 1)
      if (currentSessionId.value === id) {
        currentSessionId.value = sessions.value[0]?.id || null
      }
      saveToLocalStorage()
    }
  }

  function addMessage(role: 'user' | 'assistant', content: string): Message {
    if (!currentSession.value) {
      createSession()
    }

    const message: Message = {
      id: Date.now().toString() + Math.random().toString(36).slice(2),
      role,
      content,
      timestamp: Date.now()
    }

    currentSession.value!.messages.push(message)
    currentSession.value!.updatedAt = Date.now()

    // 更新对话标题（如果第一条是用户消息）
    if (role === 'user' && currentSession.value!.messages.length === 1) {
      currentSession.value!.title = content.slice(0, 20) + (content.length > 20 ? '...' : '')
    }

    saveToLocalStorage()
    return message
  }

  function updateMessage(messageId: string, content: string, isStreaming = false) {
    const message = currentSession.value?.messages.find(m => m.id === messageId)
    if (message) {
      message.content = content
      message.isStreaming = isStreaming
      saveToLocalStorage()
    }
  }

  function finishStreaming(messageId: string) {
    const message = currentSession.value?.messages.find(m => m.id === messageId)
    if (message) {
      message.isStreaming = false
      saveToLocalStorage()
    }
  }

  async function sendMessage(content: string) {
    if (!content.trim() || isLoading.value) return

    isLoading.value = true

    // 添加用户消息
    addMessage('user', content)

    // 添加一个空的助手消息用于流式更新
    const assistantMessage = addMessage('assistant', '')
    assistantMessage.isStreaming = true

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: content,
          history: currentMessages.value.slice(-6).map(m => ({
            role: m.role,
            content: m.content
          }))
        })
      })

      if (!response.ok) {
        throw new Error('请求失败')
      }

      // 处理流式响应
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (reader) {
        let buffer = ''
        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line.trim()) {
              try {
                const data = JSON.parse(line)
                if (data.error) {
                  updateMessage(assistantMessage.id, `错误: ${data.error}`, false)
                } else {
                  updateMessage(
                    assistantMessage.id,
                    (currentSession.value?.messages.find(m => m.id === assistantMessage.id)?.content || '') + data.content,
                    !data.done
                  )
                  if (data.done) {
                    finishStreaming(assistantMessage.id)
                  }
                }
              } catch (e) {
                // 忽略解析错误
              }
            }
          }
        }
      }
    } catch (error) {
      updateMessage(assistantMessage.id, `抱歉，发生了错误: ${error}`, false)
    } finally {
      isLoading.value = false
    }
  }

  // 本地存储
  function saveToLocalStorage() {
    try {
      localStorage.setItem('recipe-chat-sessions', JSON.stringify(sessions.value))
      localStorage.setItem('recipe-chat-current', currentSessionId.value || '')
    } catch (e) {
      console.error('保存到本地存储失败:', e)
    }
  }

  function loadFromLocalStorage() {
    try {
      const savedSessions = localStorage.getItem('recipe-chat-sessions')
      const savedCurrent = localStorage.getItem('recipe-chat-current')

      if (savedSessions) {
        sessions.value = JSON.parse(savedSessions)
      }
      if (savedCurrent) {
        currentSessionId.value = savedCurrent
      }
    } catch (e) {
      console.error('从本地存储加载失败:', e)
    }
  }

  // 初始化
  function init() {
    loadFromLocalStorage()
    if (sessions.value.length === 0) {
      createSession()
    }
  }

  return {
    sessions,
    currentSessionId,
    currentSession,
    currentMessages,
    isLoading,
    isConnected,
    createSession,
    selectSession,
    deleteSession,
    sendMessage,
    init
  }
})
