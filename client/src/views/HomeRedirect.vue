<template>
  <div></div>
</template>

<script setup lang="ts">
import { useHead } from '@unhead/vue';
import { format } from 'date-fns/format';
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';

useHead({
  title: 'Home',
});

const router = useRouter();

// Automatically go to today
onMounted(() => {
  router.push({ name: 'day-id', params: { id: format(new Date(), 'MM-dd-yyyy') } });
});
</script>
