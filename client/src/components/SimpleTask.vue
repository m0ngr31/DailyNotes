<template>
  <div class="field">
    <b-checkbox v-model="completed" @input="updateTask">
      {{ taskName }}
    </b-checkbox>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import format from 'date-fns/format';

import SidebarInst from '../services/sidebar';
import {IMeta} from '../interfaces';

@Component({
  props: {
    task: {
      type: Object,
      required: true
    }
  }
})
export default class SimpleTask extends Vue {
  public task!: IMeta;
  public sidebar = SidebarInst;
  public completed: Boolean = false;

  mounted() {
    this.completed = this.task.name.split('- [x] ').length > 1;
  }

  public async updateTask() {
    let taskName;

    if (this.completed) {
      taskName = this.task.name.replace('- [ ]', '- [x]');
    } else {
      taskName = this.task.name.replace('- [x]', '- [ ]');
    }

    try {
      await this.sidebar.saveTaskProgress(taskName, this.task.uuid);
      this.$root.$emit('taskUpdated', {
        note_id: this.task.note_id,
        task: taskName,
        completed: this.completed, 
      });
    } catch {}
  }

  get taskName() {
    if (this.task && this.task.name) {
      let split = this.task.name.split('- [x] ');

      if (split.length > 1) {
        return split[1];
      }

      split = this.task.name.split('- [ ] ');

      if (split.length > 1) {
        return split[1];
      }

      return 'No data';
    }

    return 'No data';
  }
}
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