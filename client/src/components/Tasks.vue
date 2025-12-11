<template>
  <div class="level-item alt-button">
    <b-dropdown aria-role="list">
      <template #trigger>
        <b-tooltip
          label="Tasks"
          position="is-bottom"
          role="button"
        >
          <b-icon icon="tasks"></b-icon>
        </b-tooltip>
      </template>
      <b-dropdown-item
        custom
        v-for="(task, idx) in global.taskList.value"
        :key="task.index"
      >
        <task-item :task="task" :index="idx"></task-item>
      </b-dropdown-item>
      <div class="no-tasks" v-if="!global.taskList.value.length">No tasks found</div>
    </b-dropdown>
  </div>
</template>

<script setup lang="ts">
import { inject } from 'vue';
import type { IGlobal } from '../interfaces';
import TaskItem from './TaskItem.vue';

const global = inject<IGlobal>('global');
if (!global) {
  throw new Error('Global context not provided');
}
</script>

<style scoped>
.no-tasks {
  margin-left: 1em;
  color: black;
}
</style>
