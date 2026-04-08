<script setup lang="ts">
defineEmits<{
  (e: 'select', question: string): void
}>()

const quickQuestions = [
  { icon: '🍖', text: '红烧肉怎么做' },
  { icon: '🥬', text: '推荐几道素菜' },
  { icon: '🍜', text: '面条做法大全' },
  { icon: '🥣', text: '汤类食谱' },
  { icon: '🍰', text: '甜点做法' },
  { icon: '🍳', text: '早餐吃什么' },
]
</script>

<template>
  <div class="flex flex-wrap gap-2 justify-center">
    <button
      v-for="q in quickQuestions"
      :key="q.text"
      @click="$emit('select', q.text)"
      class="flex items-center gap-2 px-4 py-2 bg-white/70 backdrop-blur rounded-full text-coffee text-sm hover:bg-primary hover:text-white transition-all duration-200 hover:scale-105 active:scale-95 shadow-md hover:shadow-lg"
    >
      <span>{{ q.icon }}</span>
      <span>{{ q.text }}</span>
    </button>
  </div>
</template>
