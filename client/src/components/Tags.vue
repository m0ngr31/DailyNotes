<template>
  <div class="column light-white">
    <span class="fa-1x">Tags</span>
    <b-taglist class="tag-margin">
      <b-tag :ellipsis="true" type="is-info" v-for="tag of sidebar.tags" v-bind:key="tag">{{tag}}</b-tag>
    </b-taglist>

    <span class="fa-1x">Projects</span>
    <b-taglist class="tag-margin">
      <b-tag :ellipsis="true" type="is-success" v-for="project of sidebar.projects" v-bind:key="project">{{project}}</b-tag>
    </b-taglist>

    <span class="fa-1x">Notes</span>
    <b-taglist class="tag-margin">
      <b-tag :ellipsis="true" type="is-danger" v-for="note of sidebar.notes" v-bind:key="note.uuid">{{note.title}}</b-tag>
    </b-taglist>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';

import SidebarInst from '../services/sidebar';

@Component
export default class Tags extends Vue {
  sidebar = SidebarInst;
}
</script>

<style scoped>
.tag-margin {
  margin-top: 10px;
}
</style>