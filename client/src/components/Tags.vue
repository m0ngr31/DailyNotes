<template>
  <div class="column light-white">
    <div v-if="sidebar.sidebarLoading" class="loading-wrapper">
      <b-loading :is-full-page="false" :active="sidebar.sidebarLoading"></b-loading>
    </div>
    <div v-else>
      <span class="fa-1x" v-if="sidebar.tags.length">Tags</span>
      <div class="tag-margin alt-button" v-if="sidebar.tags.length">
        <NestedTags :nodes="sidebar.tagTree" @tag-click="goToSearch('tag', $event)" />
      </div>

      <span class="fa-1x" v-if="sidebar.projects.length">Projects</span>
      <b-taglist class="tag-margin alt-button">
        <div @click="goToSearch('project', project)" v-for="project of sidebar.projects" v-bind:key="project" class="tags-margin">
          <b-tag :ellipsis="true" type="is-success">{{project}}</b-tag>
        </div>
      </b-taglist>

      <span class="fa-1x" v-if="sidebar.notes.length">Notes</span>
      <b-taglist class="tag-margin alt-button">
        <div @click="goToNote(note.uuid)" v-for="note of sidebar.notes" v-bind:key="note.uuid" class="tags-margin">
          <b-tag :ellipsis="true" type="is-danger" class="note-tag">{{note.title}}</b-tag>
        </div>
      </b-taglist>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import SidebarInst from '../services/sidebar';
import NestedTags from './NestedTags.vue';

const router = useRouter();
const sidebar = SidebarInst;

const goToNote = (uuid: string) => {
  router.push({ name: 'note-id', params: { uuid } });
};

const goToSearch = (searchType: string, tag: string) => {
  router.push({ name: 'search', query: { [searchType]: tag } }).catch((_err) => {});
};
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

.note-tag {
  background-color: var(--accent-warning) !important;
}
</style>
