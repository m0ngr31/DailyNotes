<template>
  <div class="field">
    <b-checkbox v-model="task.completed" @input="updateTask">
      {{ this.task.name }}
    </b-checkbox>
  </div>
</template>

<script lang="ts">
import Vue from "vue";
import Component from "vue-class-component";
import { Inject } from "vue-property-decorator";

import SidebarInst from "../services/sidebar";

@Component({
  props: {
    task: {
      type: Object,
      required: true
    },
    index: {
      type: Number,
      required: true
    }
  }
})
export default class TaskItem extends Vue {
  public task: any;
  public index: any;
  public sidebar = SidebarInst;
  public completed: Boolean = false;

  @Inject()
  public global: any;

  public async updateTask() {
    this.global.taskList.splice(this.index, 1, this.task);
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
