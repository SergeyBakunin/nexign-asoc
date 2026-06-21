<template>
  <span class="badge" :class="colors[status] || 'bg-gray-100 text-gray-700'">
    {{ labels[status] || status }}
  </span>
</template>

<script setup>
defineProps({ status: String })

const colors = {
  open: 'bg-red-100 text-red-700',
  suppressed: 'bg-gray-100 text-gray-500',
  accepted: 'bg-green-100 text-green-700',
}

const labels = {
  open: 'Open',
  suppressed: 'Suppressed',
  accepted: 'Accepted',
}
</script>
