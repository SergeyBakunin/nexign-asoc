<template>
  <div class="p-6 max-w-6xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Дашборд</h1>
      <select v-model="selectedProject"
        class="border border-gray-300 rounded-lg px-3 py-1.5 text-sm min-w-[160px]">
        <option value="">Все проекты</option>
        <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
      </select>
    </div>

    <!-- Summary cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="card text-center">
        <div class="text-3xl font-bold text-brand">{{ stats.projects ?? '—' }}</div>
        <div class="text-sm text-gray-500 mt-1">Проектов</div>
      </div>
      <div class="card text-center">
        <div class="text-3xl font-bold text-gray-800">{{ stats.scans ?? '—' }}</div>
        <div class="text-sm text-gray-500 mt-1">Сканирований</div>
      </div>
      <div class="card text-center">
        <div class="text-3xl font-bold text-red-600">{{ stats.findings_open ?? '—' }}</div>
        <div class="text-sm text-gray-500 mt-1">Открытых находок</div>
      </div>
      <div class="card text-center">
        <div class="text-3xl font-bold text-gray-800">{{ stats.findings_total ?? '—' }}</div>
        <div class="text-sm text-gray-500 mt-1">Всего находок</div>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
      <!-- By severity -->
      <div class="card">
        <h2 class="font-semibold mb-4">Открытые находки по критичности</h2>
        <div class="flex flex-wrap gap-3">
          <div v-for="sev in severities" :key="sev.key"
            class="flex flex-col items-center px-5 py-3 rounded-lg border-2 min-w-[72px] cursor-pointer hover:opacity-80"
            :class="sev.border"
            @click="goToFindings({ severity: sev.key })">
            <span class="text-2xl font-bold" :class="sev.text">
              {{ stats.by_severity?.[sev.key] ?? 0 }}
            </span>
            <span class="text-xs mt-0.5 font-semibold" :class="sev.text">{{ sev.label }}</span>
          </div>
        </div>
      </div>

      <!-- By category -->
      <div class="card">
        <h2 class="font-semibold mb-4">Открытые находки по классу</h2>
        <div class="space-y-2">
          <div v-for="cat in categories" :key="cat.key" class="flex items-center gap-3">
            <span class="w-24 text-xs font-semibold uppercase text-gray-500">{{ cat.label }}</span>
            <div class="flex-1 bg-gray-100 rounded-full h-2.5 overflow-hidden">
              <div class="h-full rounded-full transition-all"
                :class="cat.color"
                :style="{ width: barWidth(stats.by_category?.[cat.key] ?? 0) }">
              </div>
            </div>
            <span class="w-8 text-right text-sm font-bold" :class="cat.textColor">
              {{ stats.by_category?.[cat.key] ?? 0 }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent scans -->
    <div class="card">
      <h2 class="font-semibold mb-4">Последние сканирования</h2>
      <div v-if="!stats.recent_scans?.length" class="text-gray-400 text-sm">Нет данных</div>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-left">
          <thead>
            <tr class="border-b border-gray-100">
              <th class="table-th">Время</th>
              <th class="table-th">Класс</th>
              <th class="table-th">Инструмент</th>
              <th class="table-th">Компонент</th>
              <th class="table-th">Находок</th>
              <th class="table-th">Пакетов</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in stats.recent_scans" :key="s.id"
              class="border-b border-gray-50 hover:bg-gray-50 cursor-pointer"
              @click="goToFindings({ scan_class_id: s.scan_class_id })">
              <td class="table-td text-gray-400 text-xs whitespace-nowrap">{{ fmtDate(s.created_at) }}</td>
              <td class="table-td"><CategoryBadge :category="s.category" /></td>
              <td class="table-td font-mono text-xs">{{ s.tool || '—' }}</td>
              <td class="table-td text-gray-600 text-xs">{{ s.component || '—' }}</td>
              <td class="table-td font-semibold text-sm"
                :class="s.findings_count > 0 ? 'text-red-600' : 'text-green-600'">
                {{ s.findings_count }}
              </td>
              <td class="table-td text-gray-500 text-sm">{{ s.components_count || '—' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getStats, getProjects } from '../api'
import CategoryBadge from '../components/CategoryBadge.vue'

const router = useRouter()
const stats = ref({})
const projects = ref([])
const selectedProject = ref('')

const severities = [
  { key: 'critical', label: 'Critical', text: 'text-red-700',    border: 'border-red-200 bg-red-50' },
  { key: 'high',     label: 'High',     text: 'text-orange-700', border: 'border-orange-200 bg-orange-50' },
  { key: 'medium',   label: 'Medium',   text: 'text-yellow-700', border: 'border-yellow-200 bg-yellow-50' },
  { key: 'low',      label: 'Low',      text: 'text-blue-700',   border: 'border-blue-200 bg-blue-50' },
  { key: 'info',     label: 'Info',     text: 'text-gray-600',   border: 'border-gray-200 bg-gray-50' },
]

const categories = [
  { key: 'sca',       label: 'SCA',       color: 'bg-purple-500', textColor: 'text-purple-700' },
  { key: 'sast',      label: 'SAST',      color: 'bg-blue-500',   textColor: 'text-blue-700' },
  { key: 'container', label: 'Container', color: 'bg-cyan-500',   textColor: 'text-cyan-700' },
  { key: 'secrets',   label: 'Secrets',   color: 'bg-red-500',    textColor: 'text-red-700' },
  { key: 'dast',      label: 'DAST',      color: 'bg-orange-500', textColor: 'text-orange-700' },
]

const maxCategoryCount = computed(() => {
  const vals = Object.values(stats.value?.by_category || {})
  return Math.max(...vals, 1)
})

function barWidth(count) {
  return `${Math.round((count / maxCategoryCount.value) * 100)}%`
}

function fmtDate(iso) {
  return new Date(iso).toLocaleString('ru-RU', { dateStyle: 'short', timeStyle: 'short' })
}

function goToFindings(query) {
  router.push({ path: '/findings', query })
}

async function loadStats() {
  const params = selectedProject.value ? { project_id: selectedProject.value } : {}
  const r = await getStats(params)
  stats.value = r.data
}

watch(selectedProject, loadStats)

onMounted(async () => {
  const [sr, pr] = await Promise.all([getStats({}), getProjects()])
  stats.value = sr.data
  projects.value = pr.data
})
</script>
