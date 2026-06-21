<template>
  <div class="p-6 max-w-xl mx-auto">
    <h1 class="text-2xl font-bold mb-6">Настройки</h1>

    <div class="card mb-4">
      <h2 class="font-semibold mb-3">API-токен</h2>
      <p class="text-sm text-gray-600 mb-3">Сохраняется в localStorage браузера.</p>
      <div class="flex gap-2">
        <input v-model="token" type="password" placeholder="Введите токен"
          class="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand" />
        <button class="btn-primary" @click="save">Сохранить</button>
      </div>
      <p v-if="saved" class="text-green-600 text-sm mt-2">Сохранено ✓</p>
    </div>

    <div class="card">
      <h2 class="font-semibold mb-3 text-sm">API эндпоинты</h2>
      <dl class="text-sm space-y-2.5">
        <div v-for="ep in endpoints" :key="ep.path" class="flex gap-2 items-start">
          <span class="badge shrink-0 mt-0.5 w-14 justify-center"
            :class="ep.method === 'GET' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'">
            {{ ep.method }}
          </span>
          <div>
            <div class="font-mono text-xs">{{ ep.path }}</div>
            <div class="text-gray-500 text-xs">{{ ep.desc }}</div>
          </div>
        </div>
      </dl>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const token = ref(localStorage.getItem('asoc_token') || '')
const saved = ref(false)

function save() {
  localStorage.setItem('asoc_token', token.value)
  saved.value = true
  setTimeout(() => { saved.value = false }, 2000)
}

const endpoints = [
  { method: 'POST', path: '/api/v1/scan-classes/{id}/ingest', desc: 'Загрузить результат (SARIF/CycloneDX) в Scan Class' },
  { method: 'POST', path: '/api/v1/scan-classes/{id}/sbom',   desc: 'Загрузить SBOM (multipart) в Scan Class' },
  { method: 'POST', path: '/api/v1/import',                   desc: 'Ручной импорт файла' },
  { method: 'GET',  path: '/api/v1/projects',                 desc: 'Список проектов' },
  { method: 'POST', path: '/api/v1/projects',                 desc: 'Создать проект' },
  { method: 'GET',  path: '/api/v1/projects/{id}/scan-classes', desc: 'Scan Classes проекта' },
  { method: 'POST', path: '/api/v1/projects/{id}/scan-classes', desc: 'Создать Scan Class' },
  { method: 'GET',  path: '/api/v1/findings',                 desc: 'Находки (фильтры: scan_class_id, severity, status, component)' },
  { method: 'PUT',  path: '/api/v1/findings/{id}/status',     desc: 'Обновить статус находки' },
  { method: 'GET',  path: '/api/v1/stats',                    desc: 'Сводная статистика' },
  { method: 'POST', path: '/api/v1/check/{id}/external',      desc: 'TRON-алиас → /scan-classes/{id}/ingest' },
  { method: 'POST', path: '/api/v1/layer/{id}/sbom',          desc: 'TRON-алиас → /scan-classes/{id}/sbom' },
]
</script>
