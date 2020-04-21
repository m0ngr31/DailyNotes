<template>
  <div class="column light-white">
    <div v-if="sidebar.sidebarLoading" class="loading-wrapper">
      <b-loading :is-full-page="false" :active="sidebar.sidebarLoading"></b-loading>
    </div>
    <div v-else>
      <span class="fa-1x" v-if="sidebar.tags.length">Tags</span>
      <b-taglist class="tag-margin alt-button">
        <div @click="goToSearch('tag', tag)" v-for="tag of sidebar.tags" v-bind:key="tag" class="tags-margin">
          <b-tag :ellipsis="true" type="is-info">{{tag}}</b-tag>
        </div>
      </b-taglist>

      <span class="fa-1x" v-if="sidebar.projects.length">Projects</span>
      <b-taglist class="tag-margin alt-button">
        <div @click="goToSearch('project', project)" v-for="project of sidebar.projects" v-bind:key="project" class="tags-margin">
          <b-tag :ellipsis="true" type="is-success">{{project}}</b-tag>
        </div>
      </b-taglist>

      <span class="fa-1x" v-if="sidebar.notes.length">Notes</span>
      <b-taglist class="tag-margin alt-button">
        <div @click="goToNote(note.uuid)" v-for="note of sidebar.notes" v-bind:key="note.uuid" class="tags-margin">
          <b-tag :ellipsis="true" type="is-danger">{{note.title}}</b-tag>
        </div>
      </b-taglist>
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';

import router from '../router/index';

import SidebarInst from '../services/sidebar';

@Component
export default class Tags extends Vue {
  sidebar = SidebarInst;

  public goToNote(uuid: string) {
    router.push({name: 'note-id', params: {uuid}});
  }

  public goToSearch(searchType: string, tag: string) {
    router.push({name: 'search', query: {[searchType]: tag}}).catch(err => {});
  }
}
</script>

<style scoped>
.tag-margin {
  margin-top: 10px;
}

.loading-wrapper {
  height: 100px;
  position: relative;
}

.tags-margin {
  margin-right: .5em;
  margin-bottom: .5em;
}
</style>