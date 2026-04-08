<script setup lang="ts">
const props = defineProps<{
  disabled?: boolean
}>()

const emit = defineEmits<{
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
      @click="!props.disabled && $emit('select', q.text)"
      :disabled="props.disabled"
      :class="[
        'flex items-center gap-2 px-4 py-2 rounded-full text-sm transition-all duration-200 shadow-md',
        props.disabled
          ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
          : 'bg-white/70 backdrop-blur text-coffee hover:bg-primary hover:text-white hover:scale-105 hover:shadow-lg active:scale-95'
      ]"
    >
      <span>{{ q.icon }}</span>
      <span>{{ q.text }}</span>
    </button>
  </div>
</template>
