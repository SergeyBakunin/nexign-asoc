<template>
  <div class="p-6 max-w-5xl mx-auto">
    <div class="flex items-center justify-between mb-6">
      <h1 class="text-2xl font-bold">Проекты</h1>
      <button class="btn-primary" @click="showForm = !showForm">+ Новый проект</button>
    </div>

    <!-- Create form -->
    <div v-if="showForm" class="card mb-6">
      <h2 class="font-semibold mb-3">Новый проект</h2>
      <div class="flex flex-col gap-3">
        <input v-model="form.name" placeholder="Название"
          class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand" />
        <textarea v-model="form.description" placeholder="Описание (опционально)" rows="2"
          class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand resize-none" />
        <div class="flex gap-2">
          <button class="btn-primary" @click="create">Создать</button>
          <button class="btn-secondary" @click="showForm = false">Отмена</button>
        </div>
        <p v-if="error" class="text-red-600 text-sm">{{ error }}</p>
      </div>
    </div>

    <!-- Projects list -->
    <div v-if="loading" class="text-gray-400">Загрузка...</div>
    <div v-else-if="!projects.length" class="card text-center text-gray-400 py-10">
      Нет проектов. Создайте первый!
    </div>
    <div v-else class="grid gap-4">
      <div v-for="p in projects" :key="p.id"
        class="card hover:shadow-md transition-shadow cursor-pointer flex items-center justify-between"
        @click="$router.push('/projects/' + p.id)">
        <div>
          <div class="font-semibold text-gray-900">{{ p.name }}</div>
          <div class="text-sm text-gray-500 mt-0.5">{{ p.description || 'Нет описания' }}</div>
          <div class="text-xs text-gray-400 mt-1">{{ fmtDate(p.created_at) }}</div>
        </div>
        <button class="btn-danger shrink-0" @click.stop="remove(p.id)">Удалить</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getProjects, createProject, deleteProject } from '../api'

const projects = ref([])
const loading = ref(true)
const showForm = ref(false)
const form = ref({ name: '', description: '' })
const error = ref('')

function fmtDate(iso) {
  return new Date(iso).toLocaleDateString('ru-RU')
}

async function load() {
  loading.value = true
  const r = await getProjects()
  projects.value = r.data
  loading.value = false
}

async function create() {
  error.value = ''
  if (!form.value.name.trim()) { error.value = 'Введите название'; return }
  try {
    await createProject(form.value)
    form.value = { name: '', description: '' }
    showForm.value = false
    await load()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Ошибка'
  }
}

async function remove(id) {
  if (!confirm('Удалить проект и все его данные?')) return
  await deleteProject(id)
  await load()
}

onMounted(load)
</script>
