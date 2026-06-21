<template>
  <div class="p-6 max-w-7xl mx-auto">
    <h1 class="text-2xl font-bold mb-6">Зависимости (SBOM)</h1>

    <!-- Filters -->
    <div class="card mb-4 flex flex-wrap gap-3 items-end">
      <div class="flex flex-col gap-1 flex-1 min-w-[200px]">
        <label class="text-xs text-gray-500">Поиск по названию</label>
        <input v-model="search" placeholder="requests, lodash..."
          class="border border-gray-300 rounded px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand"
          @keydown.enter="load" />
      </div>
      <div class="flex flex-col gap-1">
        <label class="text-xs text-gray-500">Проект</label>
        <select v-model="selectedProject" @change="load"
          class="border border-gray-300 rounded px-2 py-1.5 text-sm">
          <option value="">Все</option>
          <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </div>
      <button class="btn-primary" @click="load">Найти</button>
      <button class="btn-secondary" @click="reset">Сброс</button>
      <span class="text-sm text-gray-400 ml-auto">{{ total }} пакетов</span>
    </div>

    <!-- Table -->
    <div class="card overflow-x-auto p-0">
      <div v-if="loading" class="p-6 text-gray-400">Загрузка...</div>
      <div v-else-if="!items.length" class="p-8 text-center text-gray-400">Нет зависимостей</div>
      <table v-else class="w-full text-left">
        <thead class="bg-gray-50">
          <tr>
            <th class="table-th">Пакет</th>
            <th class="table-th">Версия</th>
            <th class="table-th">Лицензии</th>
            <th class="table-th">Уязвимости</th>
            <th class="table-th">PURL</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in items" :key="d.id"
            class="border-t border-gray-100 hover:bg-gray-50 cursor-pointer"
            @click="selected = d">
            <td class="table-td font-medium font-mono text-sm">{{ d.name }}</td>
            <td class="table-td text-gray-500 text-sm">{{ d.version || '—' }}</td>
            <td class="table-td">
              <div class="flex flex-wrap gap-1">
                <span v-for="lic in (d.licenses || [])" :key="lic"
                  class="badge bg-blue-50 text-blue-700 text-xs">{{ lic }}</span>
                <span v-if="!d.licenses?.length" class="text-gray-400 text-xs">—</span>
              </div>
            </td>
            <td class="table-td">
              <span v-if="d.vulnerabilities?.length"
                class="badge bg-red-100 text-red-700 font-semibold">
                {{ d.vulnerabilities.length }}
              </span>
              <span v-else class="text-gray-400 text-xs">—</span>
            </td>
            <td class="table-td font-mono text-xs text-gray-400 max-w-[200px] truncate">
              {{ d.purl || '—' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Pagination -->
    <div v-if="total > pageSize" class="flex items-center justify-between mt-4">
      <button class="btn-secondary" :disabled="offset === 0" @click="prevPage">← Назад</button>
      <span class="text-sm text-gray-500">
        {{ offset + 1 }}–{{ Math.min(offset + pageSize, total) }} из {{ total }}
      </span>
      <button class="btn-secondary" :disabled="offset + pageSize >= total" @click="nextPage">Вперёд →</button>
    </div>

    <!-- Detail drawer -->
    <div v-if="selected" class="fixed inset-0 bg-black/30 z-30 flex justify-end"
      @click.self="selected = null">
      <div class="w-full max-w-lg bg-white h-full overflow-y-auto shadow-xl flex flex-col">
        <div class="flex items-center justify-between px-5 py-4 border-b border-gray-200">
          <h2 class="font-semibold text-sm">{{ selected.name }} {{ selected.version }}</h2>
          <button class="text-gray-400 hover:text-gray-700 text-xl" @click="selected = null">✕</button>
        </div>
        <div class="px-5 py-4 space-y-4 text-sm flex-1">
          <div v-if="selected.purl">
            <div class="label">PURL</div>
            <div class="font-mono text-xs break-all bg-gray-50 px-2 py-1 rounded">{{ selected.purl }}</div>
          </div>
          <div>
            <div class="label">Лицензии</div>
            <div v-if="selected.licenses?.length" class="flex flex-wrap gap-1 mt-1">
              <span v-for="lic in selected.licenses" :key="lic"
                class="badge bg-blue-50 text-blue-700">{{ lic }}</span>
            </div>
            <div v-else class="text-gray-400">—</div>
          </div>
          <div v-if="selected.vulnerabilities?.length">
            <div class="label">Уязвимости ({{ selected.vulnerabilities.length }})</div>
            <div class="space-y-2 mt-1">
              <div v-for="v in selected.vulnerabilities" :key="v.id || v.cve"
                class="rounded border border-gray-100 px-3 py-2 bg-gray-50">
                <div class="font-mono text-xs text-blue-600 font-semibold">{{ v.id || v.cve }}</div>
                <div v-if="v.description" class="text-xs text-gray-600 mt-0.5">{{ v.description }}</div>
                <div v-if="v.severity" class="text-xs text-gray-400 mt-0.5">{{ v.severity }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getDependencies, getDependenciesCount, getProjects } from '../api'

const items = ref([])
const total = ref(0)
const loading = ref(true)
const selected = ref(null)
const projects = ref([])
const selectedProject = ref('')
const search = ref('')
const pageSize = 100
const offset = ref(0)

function buildParams() {
  const p = { limit: pageSize, offset: offset.value }
  if (selectedProject.value) p.project_id = selectedProject.value
  if (search.value) p.search = search.value
  return p
}

async function load() {
  loading.value = true
  const params = buildParams()
  const [dr, cr] = await Promise.all([getDependencies(params), getDependenciesCount(params)])
  items.value = dr.data
  total.value = cr.data.total
  loading.value = false
}

function reset() {
  selectedProject.value = ''
  search.value = ''
  offset.value = 0
  load()
}

function prevPage() { offset.value = Math.max(0, offset.value - pageSize); load() }
function nextPage() { offset.value += pageSize; load() }

onMounted(async () => {
  const pr = await getProjects()
  projects.value = pr.data
  await load()
})
</script>

<style scoped>
.label { @apply text-xs text-gray-400 mb-0.5; }
</style>
