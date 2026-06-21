<template>
  <div class="p-6 max-w-2xl mx-auto">
    <h1 class="text-2xl font-bold mb-6">Ручной импорт результатов</h1>

    <div class="card">
      <p class="text-sm text-gray-600 mb-4">
        Загрузите файл сканирования (SARIF или CycloneDX BOM) в нужный Scan Class.
        Формат определяется автоматически.
      </p>

      <div class="flex flex-col gap-4">
        <!-- Project -->
        <div>
          <label class="block text-sm font-medium mb-1">Проект</label>
          <select v-model="projectId" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
            @change="onProjectChange">
            <option value="">— выберите проект —</option>
            <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
          </select>
        </div>

        <!-- Scan Class -->
        <div v-if="projectId">
          <label class="block text-sm font-medium mb-1">Scan Class</label>
          <select v-model="scanClassId" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
            <option value="">— выберите —</option>
            <optgroup v-for="cat in groupedCategories" :key="cat.key" :label="cat.label">
              <option v-for="sc in cat.items" :key="sc.id" :value="sc.id">
                {{ sc.name }}
              </option>
            </optgroup>
          </select>
        </div>

        <!-- Optional metadata -->
        <div v-if="scanClassId" class="grid grid-cols-2 gap-3">
          <div>
            <label class="block text-xs text-gray-500 mb-1">Компонент</label>
            <input v-model="meta.component" placeholder="backend, frontend..."
              class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm" />
          </div>
          <div>
            <label class="block text-xs text-gray-500 mb-1">Язык</label>
            <input v-model="meta.language" placeholder="python, javascript..."
              class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm" />
          </div>
          <div class="col-span-2">
            <label class="block text-xs text-gray-500 mb-1">Ветка</label>
            <input v-model="meta.branch" placeholder="main, develop..."
              class="w-full border border-gray-300 rounded px-2 py-1.5 text-sm" />
          </div>
        </div>

        <!-- File -->
        <div>
          <label class="block text-sm font-medium mb-1">Файл (.json / .sarif)</label>
          <input type="file" accept=".json,.sarif" @change="onFile"
            class="block w-full text-sm text-gray-500
                   file:mr-3 file:py-1.5 file:px-3 file:rounded file:border-0
                   file:text-sm file:font-medium file:bg-brand file:text-white
                   hover:file:bg-brand-dark cursor-pointer" />
        </div>

        <button class="btn-primary w-full justify-center py-2" @click="submit" :disabled="uploading">
          {{ uploading ? 'Загрузка...' : 'Импортировать' }}
        </button>

        <!-- Result -->
        <div v-if="result" class="rounded-lg p-3 text-sm"
          :class="result.error ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'">
          <template v-if="result.error">{{ result.error }}</template>
          <template v-else>
            <p>✓ Импортировано: <strong>{{ result.findings }}</strong> находок,
               <strong>{{ result.components }}</strong> пакетов</p>
            <p class="text-xs mt-1">Формат: {{ result.format }} · scan_id:
              <span class="font-mono">{{ result.scan_id }}</span></p>
          </template>
        </div>
      </div>
    </div>

    <!-- API Reference -->
    <div class="card mt-6">
      <h2 class="font-semibold text-sm mb-3">API (TRON-совместимый)</h2>
      <pre class="text-xs bg-gray-900 text-green-300 p-3 rounded overflow-x-auto">
# SARIF / CycloneDX → Scan Class
curl -X POST http://asoc:8000/api/v1/scan-classes/&lt;id&gt;/ingest \
  -H "x-api-token: $ASOC_TOKEN" \
  -H "content-type: application/json" \
  -H "x-component: backend" \
  -H "x-language: python" \
  --data-binary @trivy.sarif

# CycloneDX BOM → Scan Class (SBOM/зависимости)
curl -X POST http://asoc:8000/api/v1/scan-classes/&lt;id&gt;/sbom \
  -H "x-api-token: $ASOC_TOKEN" \
  -F "sbom=@bom.json;type=application/json" \
  -F "component=backend"

# TRON-алиасы (для существующих CI без изменений):
# /check/{id}/external  →  /scan-classes/{id}/ingest
# /layer/{id}/sbom      →  /scan-classes/{id}/sbom</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getProjects, getScanClasses, manualImport } from '../api'

const projects = ref([])
const scanClasses = ref([])
const projectId = ref('')
const scanClassId = ref('')
const meta = ref({ component: '', language: '', branch: '' })
const file = ref(null)
const uploading = ref(false)
const result = ref(null)

const CATEGORY_LABELS = {
  sca: 'SCA', sast: 'SAST', container: 'Container', secrets: 'Secrets', dast: 'DAST',
}

const groupedCategories = computed(() => {
  const groups = {}
  for (const sc of scanClasses.value) {
    if (!groups[sc.category]) groups[sc.category] = []
    groups[sc.category].push(sc)
  }
  return Object.entries(groups).map(([key, items]) => ({
    key, label: CATEGORY_LABELS[key] || key, items,
  }))
})

function onFile(e) { file.value = e.target.files[0] || null; result.value = null }

async function onProjectChange() {
  scanClassId.value = ''
  scanClasses.value = []
  if (!projectId.value) return
  const r = await getScanClasses(projectId.value)
  scanClasses.value = r.data
}

async function submit() {
  result.value = null
  if (!file.value || !scanClassId.value) {
    result.value = { error: 'Выберите файл и Scan Class' }
    return
  }
  const fd = new FormData()
  fd.append('file', file.value)
  fd.append('scan_class_id', scanClassId.value)
  if (meta.value.component) fd.append('component', meta.value.component)
  if (meta.value.language) fd.append('language', meta.value.language)
  if (meta.value.branch) fd.append('branch', meta.value.branch)

  uploading.value = true
  try {
    const r = await manualImport(fd)
    result.value = r.data
  } catch (e) {
    const detail = e.response?.data?.detail
    let msg
    if (!detail) msg = `Ошибка ${e.response?.status ?? ''}: ${e.message}`
    else if (typeof detail === 'string') msg = detail
    else if (Array.isArray(detail)) msg = detail.map(d => `${d.loc?.slice(-1)} — ${d.msg}`).join('; ')
    else msg = JSON.stringify(detail)
    result.value = { error: msg }
  } finally {
    uploading.value = false
  }
}

onMounted(async () => {
  const r = await getProjects()
  projects.value = r.data
})
</script>
