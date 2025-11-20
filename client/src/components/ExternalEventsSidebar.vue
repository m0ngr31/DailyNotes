<template>
  <div class="external-events" v-if="events.length || loading">
    <div class="external-events__header">
      <span>Events</span>
      <b-loading :is-full-page="false" :active="loading" :can-cancel="false" size="is-small"></b-loading>
    </div>
    <p v-if="!events.length && !loading" class="external-events__empty">No events for this day.</p>
    <div v-else class="external-events__list">
      <div v-for="ev in events" :key="ev.title + ev.start + ev.source" class="external-events__item">
        <div class="external-events__dot" :style="dotStyle(ev)"></div>
        <div class="external-events__body">
          <div class="external-events__title">
            <span>{{ ev.title }}</span>
          </div>
          <div class="external-events__meta">
            <span class="external-events__time">{{ formatTime(ev) }}</span>
            <span class="external-events__source">{{ ev.source }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { format } from 'date-fns/format';
import { parseISO } from 'date-fns/parseISO';
import type { IExternalEvent } from '../interfaces';

defineProps<{
  events: IExternalEvent[];
  loading: boolean;
}>();

const dotStyle = (ev: IExternalEvent) => {
  const fallback = '#8ab4f8';
  return { backgroundColor: ev.color || fallback };
};

const formatTime = (ev: IExternalEvent) => {
  if (ev.all_day) return 'All day';
  try {
    const start = parseISO(ev.start);
    const end = parseISO(ev.end);
    return `${format(start, 'h:mma')} – ${format(end, 'h:mma')}`;
  } catch (_e) {
    return '';
  }
};
</script>

<style scoped>
.external-events {
  margin: 10px 12px;
  padding: 10px;
  border: 1px solid #304254;
  border-radius: 8px;
  background: #1f2733;
  color: #e5ecf3;
}

.external-events__header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #9fb3c8;
  margin-bottom: 4px;
}

.external-events__empty {
  color: #8fa1b5;
  font-size: 13px;
  margin: 0;
}

.external-events__list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.external-events__item {
  display: flex;
  gap: 8px;
  align-items: center;
}

.external-events__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.external-events__body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.external-events__title {
  font-weight: 600;
  font-size: 13px;
}

.external-events__meta {
  display: flex;
  gap: 8px;
  font-size: 12px;
  color: #9fb3c8;
}

.external-events__source {
  font-weight: 600;
}
</style>
