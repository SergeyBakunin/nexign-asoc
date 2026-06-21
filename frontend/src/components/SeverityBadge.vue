<template>
  <span class="badge" :class="colors[severity] || colors.info">
    {{ labels[severity] || (severity ? severity.toUpperCase() : 'INFO') }}
  </span>
</template>

<script setup>
defineProps({ severity: String })

const colors = {
  critical: 'bg-red-100 text-red-800',
  high: 'bg-orange-100 text-orange-800',
  medium: 'bg-yellow-100 text-yellow-800',
  low: 'bg-blue-100 text-blue-800',
  info: 'bg-gray-100 text-gray-700',
}

const labels = {
  critical: 'CRITICAL',
  high: 'HIGH',
  medium: 'MEDIUM',
  low: 'LOW',
  info: 'INFO',
}
</script>
