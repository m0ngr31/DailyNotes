<template>
  <div class="level-item alt-button">
    <b-dropdown aria-role="list" :can-close="['escape', 'outside']">
      <b-tooltip
        label="Tasks"
        position="is-bottom"
        slot="trigger"
        role="button"
      >
        <b-icon icon="tasks"></b-icon>
      </b-tooltip>
      <b-dropdown-item
        custom
        v-for="(task, idx) in global.taskList"
        :key="task.index"
      >
        <task-item :task="task" :index="idx"></task-item>
      </b-dropdown-item>
      <div class="no-tasks" v-if="!global.taskList.length">No tasks found</div>
    </b-dropdown>
  </div>
</template>

<script lang="ts">
import { Component, Inject, Vue } from 'vue-property-decorator';
import type { IGlobal } from '../interfaces';

import TaskItem from './TaskItem.vue';

@Component({
  components: { TaskItem },
})
export default class Tasks extends Vue {
  @Inject()
  public global!: IGlobal;
}
</script>

<style scoped>
.no-tasks {
  margin-left: 1em;
  color: black;
}
</style>
