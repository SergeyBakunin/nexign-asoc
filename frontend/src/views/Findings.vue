<template>
  <div class="p-6 max-w-7xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Находки</h1>
      <a :href="exportUrl" download="findings.csv"
        class="btn-secondary text-sm flex items-center gap-1.5">
        ↓ Экспорт CSV
      </a>
    </div>

    <!-- Filters -->
    <div class="card mb-4">
      <!-- Search -->
      <div class="flex gap-2 mb-3">
        <input v-model="search" placeholder="Поиск по названию, CVE, URI..."
          class="flex-1 border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand"
          @keydown.enter="applyFilters" />
        <button class="btn-primary" @click="applyFilters">Найти</button>
      </div>
      <!-- Filter row -->
      <div class="flex flex-wrap gap-3 items-end">
        <div class="flex flex-col gap-1">
          <label class="text-xs text-gray-500">Проект</label>
          <select v-model="filters.project_id" class="border border-gray-300 rounded px-2 py-1.5 text-sm w-44">
            <option value="">Все проекты</option>
            <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-xs text-gray-500">Критичность</label>
          <select v-model="filters.severity" class="border border-gray-300 rounded px-2 py-1.5 text-sm">
            <option value="">Все</option>
            <option>critical</option><option>high</option>
            <option>medium</option><option>low</option><option>info</option>
          </select>
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-xs text-gray-500">Статус</label>
          <select v-model="filters.status" class="border border-gray-300 rounded px-2 py-1.5 text-sm">
            <option value="">Все</option>
            <option>open</option><option>suppressed</option><option>accepted</option>
          </select>
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-xs text-gray-500">Анализатор</label>
          <select v-model="filters.tool" class="border border-gray-300 rounded px-2 py-1.5 text-sm w-36">
            <option value="">Все</option>
            <option v-for="t in tools" :key="t" :value="t">{{ t }}</option>
          </select>
        </div>
        <div class="flex flex-col gap-1">
          <label class="text-xs text-gray-500">Компонент</label>
          <select v-model="filters.component" class="border border-gray-300 rounded px-2 py-1.5 text-sm w-32">
            <option value="">Все</option>
            <option v-for="c in components" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>
        <button class="btn-primary" @click="applyFilters">Применить</button>
        <button class="btn-secondary" @click="resetFilters">Сброс</button>
        <span class="text-sm text-gray-400 ml-auto">
          {{ total }} шт.
        </span>
      </div>
    </div>

    <!-- Table -->
    <div class="card overflow-x-auto p-0">
      <div v-if="loading" class="p-6 text-gray-400">Загрузка...</div>
      <div v-else-if="!findings.length" class="p-8 text-center text-gray-400">Нет находок</div>
      <table v-else class="w-full text-left">
        <thead class="bg-gray-50">
          <tr>
            <th class="table-th cursor-pointer select-none" @click="toggleSort('severity')">
              Критичность {{ sortIndicator('severity') }}
            </th>
            <th class="table-th cursor-pointer select-none" @click="toggleSort('name')">
              Название {{ sortIndicator('name') }}
            </th>
            <th class="table-th cursor-pointer select-none" @click="toggleSort('cve')">
              CVE {{ sortIndicator('cve') }}
            </th>
            <th class="table-th">Файл / URI</th>
            <th class="table-th">Статус</th>
            <th class="table-th cursor-pointer select-none" @click="toggleSort('created_at')">
              Дата {{ sortIndicator('created_at') }}
            </th>
            <th class="table-th w-32"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="f in findings" :key="f.id"
            class="border-t border-gray-100 hover:bg-gray-50 cursor-pointer"
            @click="selected = f">
            <td class="table-td"><SeverityBadge :severity="f.severity" /></td>
            <td class="table-td max-w-xs truncate font-medium">{{ f.name }}</td>
            <td class="table-td font-mono text-xs text-blue-600">{{ f.cve || '—' }}</td>
            <td class="table-td font-mono text-xs text-gray-400 max-w-[180px] truncate">
              {{ f.uri || '—' }}
            </td>
            <td class="table-td"><StatusBadge :status="f.status" /></td>
            <td class="table-td text-gray-400 text-xs whitespace-nowrap">{{ fmtDate(f.created_at) }}</td>
            <td class="table-td" @click.stop>
              <select class="border border-gray-200 rounded text-xs px-1 py-0.5 w-full"
                :value="f.status" @change="changeStatus(f, $event.target.value)">
                <option>open</option><option>suppressed</option><option>accepted</option>
              </select>
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
          <h2 class="font-semibold text-sm">Детали находки</h2>
          <button class="text-gray-400 hover:text-gray-700 text-xl" @click="selected = null">✕</button>
        </div>
        <div class="px-5 py-4 space-y-4 flex-1 text-sm">
          <div><div class="label">Критичность</div><SeverityBadge :severity="selected.severity" /></div>
          <div><div class="label">Название</div><div class="font-medium">{{ selected.name }}</div></div>
          <div v-if="selected.rule_id">
            <div class="label">Rule ID</div>
            <div class="font-mono text-xs bg-gray-50 px-2 py-1 rounded">{{ selected.rule_id }}</div>
          </div>
          <div v-if="selected.cve">
            <div class="label">CVE</div>
            <div class="font-mono text-blue-600">{{ selected.cve }}</div>
          </div>
          <div v-if="selected.description">
            <div class="label">Описание</div>
            <div class="text-gray-700 whitespace-pre-wrap">{{ selected.description }}</div>
          </div>
          <div v-if="selected.uri">
            <div class="label">URI / Файл</div>
            <div class="font-mono text-xs break-all bg-gray-50 px-2 py-1 rounded">{{ selected.uri }}</div>
          </div>
          <div v-if="selected.region?.snippet">
            <div class="label">Фрагмент кода</div>
            <pre class="text-xs bg-gray-900 text-green-300 px-3 py-2 rounded overflow-x-auto">{{ selected.region.snippet }}</pre>
          </div>
          <div v-if="selected.region?.startLine">
            <div class="text-xs text-gray-400">
              Строка: {{ selected.region.startLine }}
              {{ selected.region.endLine ? '– ' + selected.region.endLine : '' }}
            </div>
          </div>
          <div>
            <div class="label">Статус</div>
            <select class="border border-gray-300 rounded px-2 py-1 text-sm"
              :value="selected.status" @change="changeStatus(selected, $event.target.value)">
              <option>open</option><option>suppressed</option><option>accepted</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getFindings, getComponents, getTools, updateFindingStatus, exportFindings, getProjects } from '../api'
import SeverityBadge from '../components/SeverityBadge.vue'
import StatusBadge from '../components/StatusBadge.vue'

const route = useRoute()
const findings = ref([])
const total = ref(0)
const components = ref([])
const tools = ref([])
const projects = ref([])
const loading = ref(true)
const selected = ref(null)

const pageSize = 50
const offset = ref(0)
const search = ref('')
const sortBy = ref('created_at')
const sortDir = ref('desc')

const filters = ref({
  project_id: route.query.project_id || '',
  severity: route.query.severity || '',
  status: route.query.status || '',
  scan_class_id: route.query.scan_class_id || '',
  component: route.query.component || '',
  tool: '',
})

const exportUrl = computed(() => {
  const params = buildParams()
  return exportFindings(params)
})

function buildParams() {
  const p = {}
  for (const [k, v] of Object.entries(filters.value)) { if (v) p[k] = v }
  if (search.value) p.search = search.value
  p.sort_by = sortBy.value
  p.sort_dir = sortDir.value
  p.limit = pageSize
  p.offset = offset.value
  return p
}

function fmtDate(iso) {
  return new Date(iso).toLocaleString('ru-RU', { dateStyle: 'short', timeStyle: 'short' })
}

function sortIndicator(col) {
  if (sortBy.value !== col) return ''
  return sortDir.value === 'desc' ? '▼' : '▲'
}

function toggleSort(col) {
  if (sortBy.value === col) {
    sortDir.value = sortDir.value === 'desc' ? 'asc' : 'desc'
  } else {
    sortBy.value = col
    sortDir.value = 'desc'
  }
  offset.value = 0
  load()
}

function applyFilters() {
  offset.value = 0
  load()
}

function resetFilters() {
  filters.value = { project_id: '', severity: '', status: '', scan_class_id: '', component: '', tool: '' }
  search.value = ''
  offset.value = 0
  sortBy.value = 'created_at'
  sortDir.value = 'desc'
  load()
}

function prevPage() { offset.value = Math.max(0, offset.value - pageSize); load() }
function nextPage() { offset.value += pageSize; load() }

async function loadFilters() {
  const params = {}
  if (filters.value.project_id) params.project_id = filters.value.project_id
  if (filters.value.scan_class_id) params.scan_class_id = filters.value.scan_class_id
  const [cr, tr] = await Promise.all([getComponents(params), getTools(params)])
  components.value = cr.data
  tools.value = tr.data
}

watch(() => [filters.value.project_id, filters.value.scan_class_id], () => {
  filters.value.component = ''
  filters.value.tool = ''
  loadFilters()
})

async function load() {
  loading.value = true
  const r = await getFindings(buildParams())
  findings.value = r.data.items
  total.value = r.data.total
  loading.value = false
}

async function changeStatus(f, status) {
  await updateFindingStatus(f.id, status)
  f.status = status
  if (selected.value?.id === f.id) selected.value = { ...selected.value, status }
}

onMounted(async () => {
  const pr = await getProjects()
  projects.value = pr.data
  load()
  loadFilters()
})
</script>

<style scoped>
.label { @apply text-xs text-gray-400 mb-0.5; }
</style>
