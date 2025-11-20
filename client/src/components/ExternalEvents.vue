<template>
  <div class="external-events" v-if="events.length || loading">
    <div class="external-events__header">
      <span>Calendar events</span>
      <b-loading :is-full-page="false" :active="loading" :can-cancel="false" size="is-small"></b-loading>
    </div>
    <p v-if="!events.length && !loading" class="external-events__empty">No events for this day.</p>
    <div v-else class="external-events__list">
      <div v-for="ev in events" :key="ev.title + ev.start + ev.source" class="external-events__item">
        <div class="external-events__dot" :style="dotStyle(ev)"></div>
        <div class="external-events__body">
          <div class="external-events__title">
            <span>{{ ev.title }}</span>
            <span class="external-events__time">{{ formatTime(ev) }}</span>
          </div>
          <div class="external-events__meta">
            <span class="external-events__source">{{ ev.source }}</span>
            <a v-if="ev.url" class="external-events__link" :href="ev.url" target="_blank" rel="noopener">Open</a>
          </div>
          <div v-if="ev.location" class="external-events__location">{{ ev.location }}</div>
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
  background: #1e262f;
  border: 1px solid #304254;
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 12px;
  color: #e5ecf3;
}

.external-events__header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #9fb3c8;
  margin-bottom: 6px;
}

.external-events__empty {
  color: #778899;
  margin: 0;
  font-size: 14px;
}

.external-events__list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.external-events__item {
  display: flex;
  gap: 10px;
  background: #141b23;
  border: 1px solid #243241;
  border-radius: 8px;
  padding: 8px 10px;
}

.external-events__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-top: 6px;
}

.external-events__body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.external-events__title {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  font-weight: 600;
}

.external-events__time {
  color: #9fb3c8;
  font-size: 13px;
}

.external-events__meta {
  display: flex;
  gap: 10px;
  align-items: center;
  font-size: 13px;
  color: #9fb3c8;
}

.external-events__source {
  font-weight: 600;
  color: #c8d5e0;
}

.external-events__link {
  color: #7fc4ff;
}

.external-events__location {
  font-size: 13px;
  color: #cfd8e3;
}
</style>
