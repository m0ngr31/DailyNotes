<template>
  <div class="level-item alt-button">
    <!-- Kanban mode: show button that opens modal -->
    <div v-if="sidebar.kanbanEnabled" @click="openKanban">
      <b-tooltip label="Tasks (Kanban)" position="is-bottom" role="button">
        <b-icon icon="columns"></b-icon>
      </b-tooltip>
    </div>

    <!-- List mode: show dropdown -->
    <b-dropdown v-else aria-role="list">
      <template #trigger>
        <b-tooltip label="Tasks" position="is-bottom" role="button">
          <b-icon icon="tasks"></b-icon>
        </b-tooltip>
      </template>
      <b-dropdown-item custom v-for="(task, idx) in global.taskList.value" :key="task.index">
        <task-item :task="task" :index="idx"></task-item>
      </b-dropdown-item>
      <div class="no-tasks" v-if="!global.taskList.value.length">No tasks found</div>
    </b-dropdown>
  </div>
</template>

<script setup lang="ts">
import { getCurrentInstance, inject } from 'vue';
import type { IGlobal } from '../interfaces';
import sidebar from '../services/sidebar';
import Kanban from './Kanban.vue';
import TaskItem from './TaskItem.vue';

const global = inject<IGlobal>('global');
if (!global) {
  throw new Error('Global context not provided');
}

const instance = getCurrentInstance();
const buefy = (instance?.appContext.config.globalProperties as any).$buefy;

const openKanban = () => {
  buefy?.modal.open({
    parent: instance,
    component: Kanban,
    hasModalCard: true,
    trapFocus: true,
    canCancel: ['escape', 'x', 'outside'],
  });
};
</script>

<style scoped>
.no-tasks {
  margin-left: 1em;
  color: var(--text-muted);
}
</style>
