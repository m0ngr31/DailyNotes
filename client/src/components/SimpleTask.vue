<template>
  <div class="field">
    <b-checkbox v-model="completed" @input="updateTask">
      {{ taskName }}
    </b-checkbox>
  </div>
</template>

<script setup lang="ts">
import { computed, getCurrentInstance, onMounted, ref } from 'vue';
import type { IMeta } from '../interfaces';
import eventHub from '../services/eventHub';
import SidebarInst from '../services/sidebar';

interface Props {
  task: IMeta;
}

const props = defineProps<Props>();

const sidebar = SidebarInst;
const completed = ref(false);
const instance = getCurrentInstance();

onMounted(() => {
  completed.value = props.task.name.split('- [x] ').length > 1;
});

const updateTask = async () => {
  let taskName: string;

  if (completed.value) {
    taskName = props.task.name.replace('- [ ]', '- [x]');
  } else {
    taskName = props.task.name.replace('- [x]', '- [ ]');
  }

  try {
    await sidebar.saveTaskProgress(taskName, props.task.uuid);
    eventHub.emit('taskUpdated', {
      note_id: props.task.note_id,
      task: taskName,
      completed: completed.value,
    });
  } catch {}
};

const taskName = computed(() => {
  if (props.task?.name) {
    let split = props.task.name.split('- [x] ');

    if (split.length > 1) {
      return split[1];
    }

    split = props.task.name.split('- [ ] ');

    if (split.length > 1) {
      return split[1];
    }

    return 'No data';
  }

  return 'No data';
});
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
