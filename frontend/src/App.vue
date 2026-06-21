<template>
  <div class="min-h-screen flex">
    <!-- Sidebar -->
    <aside class="w-56 bg-gray-900 text-gray-100 flex flex-col shrink-0">
      <div class="px-5 py-5 border-b border-gray-700">
        <div class="flex items-center gap-2">
          <svg class="w-6 h-6 text-brand" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
          </svg>
          <span class="font-bold text-lg tracking-tight">ASOC</span>
        </div>
        <p class="text-xs text-gray-400 mt-1">Nexign Security Hub</p>
      </div>

      <nav class="flex-1 px-3 py-4 space-y-1">
        <router-link v-for="item in nav" :key="item.to" :to="item.to"
          class="flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors"
          :class="isActive(item.to)
            ? 'bg-brand text-white'
            : 'text-gray-300 hover:bg-gray-800 hover:text-white'">
          <span class="w-4 h-4 shrink-0 text-base leading-none">{{ item.emoji }}</span>
          {{ item.label }}
        </router-link>
      </nav>

      <div class="px-4 py-4 border-t border-gray-700 text-xs text-gray-500">v1.0.0</div>
    </aside>

    <!-- Main -->
    <main class="flex-1 overflow-auto">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()

const nav = [
  { to: '/dashboard',    label: 'Дашборд',      emoji: '🏠' },
  { to: '/projects',     label: 'Проекты',      emoji: '📁' },
  { to: '/findings',     label: 'Находки',      emoji: '🐛' },
  { to: '/dependencies', label: 'Зависимости',  emoji: '📦' },
  { to: '/import',       label: 'Импорт',       emoji: '📥' },
  { to: '/settings',     label: 'Настройки',    emoji: '⚙️' },
]

function isActive(to) {
  if (to === '/dashboard') return route.path === to
  return route.path.startsWith(to)
}
</script>
