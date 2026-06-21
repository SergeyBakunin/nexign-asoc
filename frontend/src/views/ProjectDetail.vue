<template>
  <div class="p-6 max-w-6xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <div>
        <button class="text-sm text-gray-400 hover:text-gray-700 mb-1" @click="$router.push('/projects')">
          ← Проекты
        </button>
        <h1 class="text-2xl font-bold">{{ project?.name || '...' }}</h1>
      </div>
      <button class="btn-primary"
        @click="$router.push({ path: '/findings', query: { project_id: projectId } })">
        Все находки проекта
      </button>
    </div>

    <div v-for="cat in usedCategories" :key="cat" class="card mb-4">
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-2">
          <CategoryBadge :category="cat" />
          <span class="font-semibold">{{ categoryLabel(cat) }}</span>
          <span class="text-xs text-gray-400">({{ scanClassesByCategory[cat]?.length || 0 }})</span>
        </div>
        <button class="btn-primary text-xs" @click="openForm(cat)">+ Добавить</button>
      </div>

      <table class="w-full text-left">
        <thead>
          <tr class="border-b border-gray-100">
            <th class="table-th">ID</th>
            <th class="table-th">Название</th>
            <th class="table-th">Описание</th>
            <th class="table-th"></th>
          </tr>
        </thead>
        <tbody>
          <template v-for="sc in scanClassesByCategory[cat]" :key="sc.id">
            <!-- Scan class row -->
            <tr class="border-b border-gray-100 hover:bg-gray-50">
              <td class="table-td font-mono text-xs text-gray-400 select-all" :title="sc.id">
                {{ sc.id.slice(0, 8) }}…
              </td>
              <td class="table-td font-medium">{{ sc.name }}</td>
              <td class="table-td text-gray-500 text-sm">{{ sc.description || '—' }}</td>
              <td class="table-td">
                <div class="flex gap-1 items-center">
                  <button class="btn-secondary text-xs"
                    @click="$router.push({ path: '/findings', query: { scan_class_id: sc.id } })">
                    Находки
                  </button>
                  <button class="btn-secondary text-xs"
                    @click="toggleScans(sc.id)">
                    {{ expandedSc === sc.id ? '▲' : '▼' }} Сканы
                  </button>
                  <button class="text-xs text-red-500 hover:text-red-700 px-2"
                    @click="removeScanClass(sc.id)">✕</button>
                </div>
              </td>
            </tr>
            <!-- Scan history (expandable) -->
            <tr v-if="expandedSc === sc.id">
              <td colspan="4" class="bg-gray-50 px-4 py-3">
                <div v-if="scansLoading" class="text-xs text-gray-400">Загрузка...</div>
                <div v-else-if="!scanHistory.length" class="text-xs text-gray-400">Нет прогонов</div>
                <table v-else class="w-full text-xs">
                  <thead>
                    <tr class="text-gray-400 border-b border-gray-200">
                      <th class="py-1 pr-3 text-left font-medium">Дата</th>
                      <th class="py-1 pr-3 text-left font-medium">Инструмент</th>
                      <th class="py-1 pr-3 text-left font-medium">Компонент</th>
                      <th class="py-1 pr-3 text-left font-medium">Формат</th>
                      <th class="py-1 pr-3 text-right font-medium">Находок</th>
                      <th class="py-1 pr-3 text-right font-medium">Пакетов</th>
                      <th class="py-1"></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="s in scanHistory" :key="s.id"
                      class="border-b border-gray-100 hover:bg-gray-100">
                      <td class="py-1.5 pr-3 text-gray-500 whitespace-nowrap">{{ fmtDate(s.created_at) }}</td>
                      <td class="py-1.5 pr-3 font-mono">{{ s.tool || '—' }}</td>
                      <td class="py-1.5 pr-3 text-gray-600">{{ s.component || '—' }}</td>
                      <td class="py-1.5 pr-3 text-gray-400">{{ s.format }}</td>
                      <td class="py-1.5 pr-3 text-right font-semibold"
                        :class="s.findings_count > 0 ? 'text-red-600' : 'text-green-600'">
                        {{ s.findings_count }}
                      </td>
                      <td class="py-1.5 pr-3 text-right text-gray-500">
                        {{ s.components_count || '—' }}
                      </td>
                      <td class="py-1.5">
                        <button class="text-red-400 hover:text-red-600"
                          @click="removeScan(s.id, sc.id)" title="Удалить прогон">✕</button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- Add new category section -->
    <div class="card border-dashed border-gray-300 bg-gray-50">
      <button class="btn-secondary text-sm w-full justify-center" @click="openForm('')">
        + Добавить Scan Class
      </button>
    </div>

    <!-- Create form modal -->
    <div v-if="showForm" class="fixed inset-0 bg-black/30 z-30 flex items-center justify-center"
      @click.self="showForm = false">
      <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
        <h2 class="font-semibold mb-4">Новый Scan Class</h2>
        <div class="flex flex-col gap-3">
          <div>
            <label class="block text-xs text-gray-500 mb-1">Категория</label>
            <select v-model="form.category"
              class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
              <option v-for="c in allCategories" :key="c.key" :value="c.key">
                {{ c.label }} — {{ c.desc }}
              </option>
            </select>
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">Название</label>
            <input v-model="form.name" placeholder="Напр. codescoring-backend-source"
              class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand" />
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">Описание (опционально)</label>
            <input v-model="form.description"
              class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand" />
          </div>
          <p v-if="formError" class="text-red-600 text-sm">{{ formError }}</p>
          <div class="flex gap-2 mt-1">
            <button class="btn-primary flex-1 justify-center" @click="createSc">Создать</button>
            <button class="btn-secondary" @click="showForm = false">Отмена</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getProjects, getScanClasses, createScanClass, deleteScanClass, getScans, deleteScan } from '../api'
import CategoryBadge from '../components/CategoryBadge.vue'

const route = useRoute()
const projectId = route.params.id

const project = ref(null)
const scanClasses = ref([])
const showForm = ref(false)
const form = ref({ category: 'sca', name: '', description: '' })
const formError = ref('')

const expandedSc = ref(null)
const scanHistory = ref([])
const scansLoading = ref(false)

const allCategories = [
  { key: 'sca',       label: 'SCA',       desc: 'Анализ зависимостей (CodeScoring, Trivy source)' },
  { key: 'sast',      label: 'SAST',      desc: 'Статический анализ кода (PT AI, Semgrep)' },
  { key: 'container', label: 'Container', desc: 'Сканирование образов (Trivy image)' },
  { key: 'secrets',   label: 'Secrets',   desc: 'Поиск секретов (Gitleaks)' },
  { key: 'dast',      label: 'DAST',      desc: 'Динамическое тестирование (ZAP)' },
]

const categoryLabelMap = Object.fromEntries(allCategories.map(c => [c.key, c.label]))
function categoryLabel(cat) { return categoryLabelMap[cat] || cat }

function fmtDate(iso) {
  return new Date(iso).toLocaleString('ru-RU', { dateStyle: 'short', timeStyle: 'short' })
}

const scanClassesByCategory = computed(() => {
  const result = {}
  for (const sc of scanClasses.value) {
    if (!result[sc.category]) result[sc.category] = []
    result[sc.category].push(sc)
  }
  return result
})

const usedCategories = computed(() => {
  const order = ['sca', 'sast', 'container', 'secrets', 'dast']
  return order.filter(c => scanClassesByCategory.value[c]?.length)
})

async function load() {
  const [pr, sr] = await Promise.all([getProjects(), getScanClasses(projectId)])
  project.value = pr.data.find(p => p.id === projectId)
  scanClasses.value = sr.data
}

async function toggleScans(scId) {
  if (expandedSc.value === scId) {
    expandedSc.value = null
    scanHistory.value = []
    return
  }
  expandedSc.value = scId
  scansLoading.value = true
  try {
    const r = await getScans(scId)
    scanHistory.value = r.data
  } finally {
    scansLoading.value = false
  }
}

async function removeScan(scanId, scId) {
  if (!confirm('Удалить этот прогон сканирования?')) return
  try {
    await deleteScan(scanId)
    const r = await getScans(scId)
    scanHistory.value = r.data
    await load()
  } catch (e) {
    alert(e.response?.data?.detail || `Ошибка ${e.response?.status ?? e.message}`)
  }
}

function openForm(cat) {
  form.value = { category: cat || 'sca', name: '', description: '' }
  formError.value = ''
  showForm.value = true
}

async function createSc() {
  formError.value = ''
  if (!form.value.name.trim()) { formError.value = 'Введите название'; return }
  try {
    await createScanClass(projectId, form.value)
    showForm.value = false
    await load()
  } catch (e) {
    formError.value = e.response?.data?.detail || 'Ошибка'
  }
}

async function removeScanClass(id) {
  if (!confirm('Удалить Scan Class и все его данные?')) return
  try {
    await deleteScanClass(projectId, id)
    await load()
  } catch (e) {
    const detail = e.response?.data?.detail
    alert(typeof detail === 'string' ? detail : `Ошибка ${e.response?.status ?? e.message}`)
  }
}

onMounted(load)
</script>
