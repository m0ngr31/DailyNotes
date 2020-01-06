<template>
  <div class="column light-white">
    <span class="fa-1x">Tags</span>
    <b-taglist class="tag-margin">
      <b-tag :ellipsis="true" type="is-info">Aurelia</b-tag>
      <b-tag :ellipsis="true" type="is-info">Vue</b-tag>
      <b-tag :ellipsis="true" type="is-info">React</b-tag>
      <b-tag :ellipsis="true" type="is-info">Angular</b-tag>
      <b-tag :ellipsis="true" type="is-info">Lodash</b-tag>
      <b-tag :ellipsis="true" type="is-info">Study</b-tag>
      <b-tag :ellipsis="true" type="is-info">Python</b-tag>
      <b-tag :ellipsis="true" type="is-info">Flask</b-tag>
      <b-tag :ellipsis="true" type="is-info">Typescript</b-tag>
    </b-taglist>

    <span class="fa-1x">Projects</span>
    <b-taglist class="tag-margin">
      <b-tag :ellipsis="true" type="is-success">Honey-Do</b-tag>
      <b-tag :ellipsis="true" type="is-success">Remodel</b-tag>
      <b-tag :ellipsis="true" type="is-success">Apps</b-tag>
      <b-tag :ellipsis="true" type="is-success">Homelab</b-tag>
    </b-taglist>

    <span class="fa-1x">Notes</span>
    <b-taglist class="tag-margin">
      <b-tag :ellipsis="true" type="is-danger">Electrical</b-tag>
      <b-tag :ellipsis="true" type="is-danger">Gift ideas</b-tag>
      <b-tag :ellipsis="true" type="is-danger">Some really long title that happens to be really long! Some say it's still running over</b-tag>
      <b-tag :ellipsis="true" type="is-danger">Birthday Party</b-tag>
    </b-taglist>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';

@Component
export default class Tags extends Vue {}
</script>

<style scoped>
.tag-margin {
  margin-top: 10px;
}
</style>