<template>
  <span class="badge" :class="colors[category] || 'bg-gray-100 text-gray-600'">
    {{ labels[category] || category?.toUpperCase() || '?' }}
  </span>
</template>

<script setup>
defineProps({ category: String })

const colors = {
  sca:       'bg-purple-100 text-purple-700',
  sast:      'bg-blue-100 text-blue-700',
  container: 'bg-cyan-100 text-cyan-700',
  secrets:   'bg-red-100 text-red-700',
  dast:      'bg-orange-100 text-orange-700',
}

const labels = {
  sca:       'SCA',
  sast:      'SAST',
  container: 'Container',
  secrets:   'Secrets',
  dast:      'DAST',
}
</script>
