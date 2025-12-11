<template>
  <div>
    <Header :options="headerOptions"></Header>
    <div class="search-container">
      <div class="search-input-wrapper">
        <b-field>
          <b-input
            ref="searchInput"
            v-model="searchQuery"
            placeholder="Search... (e.g., tag:meeting project:work notes)"
            expanded
            icon="search"
            @keyup.enter="executeSearch"
            @input="onSearchInput"
            @keydown="onKeyDown"
            @blur="onBlur"
          ></b-input>
          <p class="control">
            <b-button type="is-success" @click="executeSearch">Search</b-button>
          </p>
          <p class="control" v-if="searchQuery">
            <b-button icon-left="times-circle" type="is-danger" @click="clearSearch"></b-button>
          </p>
          <p class="control">
            <b-dropdown aria-role="menu" position="is-bottom-left">
              <template #trigger>
                <b-button icon-left="question-circle" type="is-light"></b-button>
              </template>
              <b-dropdown-item custom paddingless>
                <div class="syntax-help">
                  <h4>Search Syntax</h4>
                  <table>
                    <tr>
                      <td><code>tag:value</code></td>
                      <td>Filter by tag</td>
                    </tr>
                    <tr>
                      <td><code>project:value</code></td>
                      <td>Filter by project</td>
                    </tr>
                    <tr>
                      <td><code>t:value</code></td>
                      <td>Shorthand for tag</td>
                    </tr>
                    <tr>
                      <td><code>p:value</code></td>
                      <td>Shorthand for project</td>
                    </tr>
                    <tr>
                      <td><code>tag:"multi word"</code></td>
                      <td>Use quotes for spaces</td>
                    </tr>
                    <tr>
                      <td><code>text</code></td>
                      <td>Search note content</td>
                    </tr>
                  </table>
                  <h4>Examples</h4>
                  <ul>
                    <li><code>tag:meeting</code></li>
                    <li><code>project:work budget</code></li>
                    <li><code>tag:1on1 tag:Q4 promotion</code></li>
                  </ul>
                  <p class="help-note">
                    Multiple tags = AND<br>
                    Multiple projects = OR<br>
                    Multiple words = AND
                  </p>
                </div>
              </b-dropdown-item>
            </b-dropdown>
          </p>
        </b-field>

        <!-- Autocomplete dropdown -->
        <div v-if="showAutocomplete && autocompleteItems.length > 0" class="autocomplete-dropdown">
          <div
            v-for="(item, index) in autocompleteItems"
            :key="item.value"
            class="autocomplete-item"
            :class="{ 'is-active': index === selectedAutocompleteIndex }"
            @mousedown.prevent="selectAutocompleteItem(item)"
          >
            <span class="autocomplete-type">{{ item.type }}</span>
            <span class="autocomplete-value">{{ item.value }}</span>
          </div>
        </div>
      </div>

      <div v-if="!sidebar.searchLoading">
        <div v-if="hasSearched && !sidebar.filteredNotes.length" class="mt-25">
          <b-notification type="is-dark" :closable="false">
            There are no notes that match that query.
          </b-notification>
        </div>
        <div class="masonry-grid mt-25">
          <NoteCard
            v-for="note in sidebar.filteredNotes"
            :key="note.uuid || ''"
            :note="note"
            :snippet="note.snippet"
            :highlights="note.highlights"
          ></NoteCard>
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
import { computed, onMounted, ref, watch } from 'vue';
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

const searchQuery = ref('');
const hasSearched = ref(false);
const showAutocomplete = ref(false);
const selectedAutocompleteIndex = ref(0);
const searchInput = ref<HTMLElement | null>(null);

interface AutocompleteItem {
  type: 'tag' | 'project';
  value: string;
  prefix: string;
}

const autocompleteItems = computed((): AutocompleteItem[] => {
  const query = searchQuery.value;
  const cursorPos = getCursorPosition();

  // Find if we're currently typing a tag: or project: filter
  const beforeCursor = query.substring(0, cursorPos);

  // Check for project: or p: prefix FIRST (before tag check to avoid t: matching end of "project:")
  const projectMatch = beforeCursor.match(/(?:project|(?:^|[\s])p):([^"\s]*)$/i);
  if (projectMatch) {
    const partial = projectMatch[1].toLowerCase();
    return sidebar.projects
      .filter((project) => project.toLowerCase().includes(partial))
      .slice(0, 8)
      .map((project) => ({
        type: 'project' as const,
        value: project,
        prefix: projectMatch[0].replace(projectMatch[1], '').trimStart(),
      }));
  }

  // Check for tag: or t: prefix (t: must be at start or after whitespace)
  const tagMatch = beforeCursor.match(/(?:tag|(?:^|[\s])t):([^"\s]*)$/i);
  if (tagMatch) {
    const partial = tagMatch[1].toLowerCase();
    return sidebar.tags
      .filter((tag) => tag.toLowerCase().includes(partial))
      .slice(0, 8)
      .map((tag) => ({
        type: 'tag' as const,
        value: tag,
        prefix: tagMatch[0].replace(tagMatch[1], '').trimStart(),
      }));
  }

  return [];
});

function getCursorPosition(): number {
  const inputEl = searchInput.value as unknown as { $el?: HTMLElement } | null;
  const input = inputEl?.$el?.querySelector('input') as HTMLInputElement | null;
  return input?.selectionStart ?? searchQuery.value.length;
}

function onSearchInput() {
  showAutocomplete.value = true;
  selectedAutocompleteIndex.value = 0;
}

function onBlur() {
  // Delay hiding to allow click on autocomplete item
  setTimeout(() => {
    showAutocomplete.value = false;
  }, 200);
}

function onKeyDown(event: KeyboardEvent) {
  if (!showAutocomplete.value || autocompleteItems.value.length === 0) {
    return;
  }

  if (event.key === 'ArrowDown') {
    event.preventDefault();
    selectedAutocompleteIndex.value = Math.min(
      selectedAutocompleteIndex.value + 1,
      autocompleteItems.value.length - 1
    );
  } else if (event.key === 'ArrowUp') {
    event.preventDefault();
    selectedAutocompleteIndex.value = Math.max(selectedAutocompleteIndex.value - 1, 0);
  } else if (event.key === 'Tab' || (event.key === 'Enter' && autocompleteItems.value.length > 0)) {
    if (autocompleteItems.value.length > 0 && showAutocomplete.value) {
      event.preventDefault();
      selectAutocompleteItem(autocompleteItems.value[selectedAutocompleteIndex.value]);
    }
  } else if (event.key === 'Escape') {
    showAutocomplete.value = false;
  }
}

function selectAutocompleteItem(item: AutocompleteItem) {
  const query = searchQuery.value;
  const cursorPos = getCursorPosition();
  const beforeCursor = query.substring(0, cursorPos);
  const afterCursor = query.substring(cursorPos);

  // Find the partial match to replace
  const pattern = item.type === 'tag' ? /(?:tag|t):([^"\s]*)$/i : /(?:project|p):([^"\s]*)$/i;
  const match = beforeCursor.match(pattern);

  if (match) {
    const prefix = match[0].replace(match[1], '');
    const valueNeedsQuotes = item.value.includes(' ');
    const formattedValue = valueNeedsQuotes ? `"${item.value}"` : item.value;
    const newBeforeCursor = beforeCursor.replace(pattern, prefix + formattedValue + ' ');
    searchQuery.value = newBeforeCursor + afterCursor;
  }

  showAutocomplete.value = false;
}

function executeSearch() {
  if (!searchQuery.value.trim()) {
    return;
  }

  hasSearched.value = true;
  showAutocomplete.value = false;
  sidebar.searchQuery = searchQuery.value;
  sidebar.selectedSearch = '';
  sidebar.searchString = '';
  sidebar.searchNotes();
}

function clearSearch() {
  searchQuery.value = '';
  sidebar.searchQuery = '';
  sidebar.selectedSearch = '';
  sidebar.searchString = '';
  sidebar.filteredNotes = [];
  hasSearched.value = false;
  showAutocomplete.value = false;
}

const setSearch = () => {
  // Handle new q param
  if (route.query.q) {
    const newQuery = String(route.query.q);
    if (searchQuery.value !== newQuery) {
      searchQuery.value = newQuery;
      sidebar.searchQuery = newQuery;
      sidebar.selectedSearch = '';
      sidebar.searchString = '';
      hasSearched.value = true;
      sidebar.searchNotes();
    }
    return;
  }

  // Handle legacy params (tag, project, search)
  let selectedSearch: string;
  let searchString: string;

  if (route.query.tag) {
    selectedSearch = 'tag';
    searchString = String(route.query.tag);
    searchQuery.value = `tag:${searchString}`;
  } else if (route.query.project) {
    selectedSearch = 'project';
    searchString = String(route.query.project);
    searchQuery.value = `project:${searchString}`;
  } else if (route.query.search) {
    selectedSearch = 'search';
    searchString = String(route.query.search);
    searchQuery.value = searchString;
  } else {
    // No query params - restore from sidebar if we have previous results
    if (sidebar.searchQuery && sidebar.filteredNotes.length > 0) {
      searchQuery.value = sidebar.searchQuery;
      hasSearched.value = true;
    }
    return;
  }

  const searchHash = `${sidebar.selectedSearch}:${sidebar.searchString}`;
  if (searchHash !== `${selectedSearch}:${searchString}`) {
    sidebar.selectedSearch = selectedSearch;
    sidebar.searchString = searchString;
    sidebar.searchQuery = '';
    hasSearched.value = true;
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

.search-input-wrapper {
  position: relative;
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

/* Autocomplete dropdown styles */
.autocomplete-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #dbdbdb;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  z-index: 100;
  max-height: 300px;
  overflow-y: auto;
  margin-top: 2px;
}

.autocomplete-item {
  padding: 8px 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
}

.autocomplete-item:hover,
.autocomplete-item.is-active {
  background-color: #f5f5f5;
}

.autocomplete-type {
  font-size: 0.75rem;
  padding: 2px 6px;
  border-radius: 4px;
  background-color: #e8e8e8;
  color: #666;
  text-transform: uppercase;
}

.autocomplete-item .autocomplete-type {
  min-width: 55px;
  text-align: center;
}

.autocomplete-value {
  color: #363636;
}

/* Syntax help dropdown styles */
.syntax-help {
  padding: 16px;
  min-width: 280px;
}

.syntax-help h4 {
  font-weight: 600;
  margin-bottom: 8px;
  color: #363636;
}

.syntax-help h4:not(:first-child) {
  margin-top: 12px;
}

.syntax-help table {
  width: 100%;
  font-size: 0.9rem;
}

.syntax-help table td {
  padding: 4px 0;
}

.syntax-help table td:first-child {
  padding-right: 12px;
}

.syntax-help code {
  background-color: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', monospace;
  font-size: 0.85rem;
}

.syntax-help ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.syntax-help ul li {
  padding: 2px 0;
}

.syntax-help .help-note {
  margin-top: 12px;
  font-size: 0.85rem;
  color: #666;
  line-height: 1.4;
}
</style>
