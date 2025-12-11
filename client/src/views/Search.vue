<template>
  <div>
    <Header :options="headerOptions"></Header>
    <div class="search-container">
      <b-field explanded>
        <b-select v-model="sidebar.selectedSearch">
          <option value="project">Project</option>
          <option value="tag">Tag</option>
          <option value="search">Text</option>
        </b-select>
        <b-input placeholder="Searcy query" v-model="sidebar.searchString" expanded @keyup.enter="sidebar.searchNotes"></b-input>
        <p class="control">
          <button class="button is-success" type="button" @click="sidebar.searchNotes()">Search</button>
        </p>
      </b-field>
      <div v-if="!sidebar.searchLoading">
        <div v-if="!sidebar.filteredNotes.length" class="mt-25">
          <b-notification
            type="is-dark"
            :closable="false"
          >
            There are no notes that match that query.
          </b-notification>
        </div>
        <div class="masonry-grid mt-25">
          <NoteCard v-for="note in sidebar.filteredNotes" :key="note.uuid" :note="note"></NoteCard>
        </div>
      </div>
      <div v-else class="loading-wrapper">
        <b-loading :is-full-page="false" :active="sidebar.searchLoading"></b-loading>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useHead } from '@unhead/vue';
import { onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';

import Header from '@/components/Header.vue';
import NoteCard from '@/components/NoteCard.vue';
import type { IHeaderOptions } from '../interfaces';
import SidebarInst from '../services/sidebar';

useHead({
  title: 'Search',
});

const route = useRoute();
const sidebar = SidebarInst;
const headerOptions: IHeaderOptions = {
  title: 'Search',
};

const setSearch = () => {
  const searchHash = `${sidebar.selectedSearch}:${sidebar.searchString}`;

  let selectedSearch: string;
  let searchString: string;

  if (route.query.tag) {
    selectedSearch = 'tag';
    searchString = String(route.query.tag);
  } else if (route.query.project) {
    selectedSearch = 'project';
    searchString = String(route.query.project);
  } else if (route.query.search) {
    selectedSearch = 'search';
    searchString = String(route.query.search);
  } else {
    selectedSearch = 'search';
    searchString = '';
  }

  if (searchHash !== `${selectedSearch}:${searchString}`) {
    sidebar.selectedSearch = selectedSearch;
    sidebar.searchString = searchString;

    sidebar.searchNotes();
  }
};

watch(
  () => route.query,
  () => {
    setSearch();
  },
  { immediate: true, deep: true }
);

onMounted(() => {
  setSearch();
});
</script>

<style scoped>
.search-container {
  padding: 1.5em;
  height: calc(100vh - 60px);
  height: calc(100dvh - 60px);
  overflow-y: auto;
}

.mt-25 {
  margin-top: 25px;
}

.masonry-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 10px;
  align-items: start;
}

@media (max-width: 767px) {
  .search-container {
    padding: 0.75em;
    height: calc(100vh - 52px);
    height: calc(100dvh - 52px);
  }

  .masonry-grid {
    grid-template-columns: 1fr;
  }

  .mt-25 {
    margin-top: 15px;
  }
}

@media (min-width: 768px) and (max-width: 1000px) {
  .masonry-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1001px) and (max-width: 1250px) {
  .masonry-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 1251px) {
  .masonry-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}

.loading-wrapper {
  width: 100%;
  height: 50vh;
  position: relative;
}
</style>