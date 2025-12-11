<template>
  <div class="calendar-stack">
    <b-datepicker
      inline
      :model-value="sidebar.date"
      indicators="bars"
      :events="sidebar.events"
      :nearby-month-days="true"
      :nearby-selectable-month-days="true"
      :focusable="false"
      @update:model-value="changeDate"
    >
    </b-datepicker>

    <ExternalEventsSidebar
      :events="sidebar.externalEvents"
      :loading="sidebar.externalEventsLoading"
    />
  </div>
</template>

<script setup lang="ts">
import { format } from 'date-fns/format';
import { nextTick, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import SidebarInst from '../services/sidebar';
import ExternalEventsSidebar from './ExternalEventsSidebar.vue';

const router = useRouter();
const route = useRoute();
const sidebar = SidebarInst;

onMounted(() => {
  sidebar.updateDate(route);
  sidebar.getEvents();
  sidebar.getSidebarInfo(true);
  sidebar.getExternalEvents();
});

const changeDate = async (value: Date | null) => {
  if (value) {
    const previousRoute = route.params.id;
    const previousDate = sidebar.date;

    await router.push({ name: 'day-id', params: { id: format(value, 'MM-dd-yyyy') } }).catch(() => {
      // Navigation was blocked - do nothing, the catch prevents unhandled rejection
    });

    // Check if route actually changed
    if (route.params.id === previousRoute) {
      // Navigation was cancelled
      // Force datepicker to reset by temporarily changing sidebar.date and changing it back
      sidebar.date = null;
      await nextTick();
      sidebar.date = previousDate;
    }
  }
};

// Keep sidebar date and external events in sync when the route changes (prev/next navigation)
watch(
  () => route.params.id,
  (newId) => {
    if (!newId) return;
    sidebar.updateDate(route);
    sidebar.getExternalEvents();
  }
);
</script>

<style scoped>
.calendar-stack {
  display: flex;
  flex-direction: column;
}
</style>
