<template>
  <div class="field">
    <b-checkbox v-model="task.completed" @update:modelValue="updateTask">
      {{ task.name }}
    </b-checkbox>
  </div>
</template>

<script setup lang="ts">
import { inject } from 'vue';
import type { IGlobal, ITask } from '../interfaces';
import SidebarInst from '../services/sidebar';

interface Props {
  task: ITask;
  index: number;
}

const props = defineProps<Props>();
const global = inject<IGlobal>('global');
if (!global) {
  throw new Error('Global context not provided');
}

const updateTask = () => {
  global.taskList.value.splice(props.index, 1, props.task);
};
</script>

<style>
.level-item > .dropdown > .dropdown-menu {
  width: 300px;
}

.level-item > .dropdown > .dropdown-menu > .dropdown-content {
  max-height: 400px;
  overflow-y: auto;
}
</style>
