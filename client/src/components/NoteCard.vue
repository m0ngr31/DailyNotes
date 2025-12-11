<template>
  <div class="note-card" @click="goToNote">
    <h1>{{ parsedTitle }}</h1>

    <!-- Search snippet with highlights -->
    <div v-if="snippet" class="search-snippet" v-html="highlightedSnippet"></div>

    <br />
    <span class="fa-1x" v-if="note.tags.length">Tags</span>
    <b-taglist class="tag-margin">
      <b-tag :ellipsis="true" v-for="tag of note.tags" v-bind:key="tag" type="is-info">{{tag}}</b-tag>
    </b-taglist>

    <span class="fa-1x" v-if="note.projects.length">Projects</span>
    <b-taglist class="tag-margin">
      <b-tag :ellipsis="true" v-for="project of note.projects" v-bind:key="project" type="is-success">{{project}}</b-tag>
    </b-taglist>
  </div>
</template>

<script setup lang="ts">
import { format } from 'date-fns/format';
import { parse } from 'date-fns/parse';
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import type { INote } from '../interfaces';

interface Props {
  note: INote;
  snippet?: string;
  highlights?: string[];
}

const props = defineProps<Props>();
const router = useRouter();

const goToNote = () => {
  if (props.note.is_date) {
    router.push({ name: 'day-id', params: { id: props.note.title || '' } });
    return;
  }

  router.push({ name: 'note-id', params: { uuid: props.note.uuid || '' } });
};

const parsedTitle = computed(() => {
  if (props.note.is_date) {
    try {
      return format(parse(props.note.title || '', 'MM-dd-yyyy', new Date()), 'EEE. MMM dd, yyyy');
    } catch (_e) {
      return props.note.title;
    }
  }

  return props.note.title;
});

const highlightedSnippet = computed(() => {
  if (!props.snippet) return '';

  let result = escapeHtml(props.snippet);

  if (props.highlights && props.highlights.length > 0) {
    for (const term of props.highlights) {
      const escapedTerm = escapeHtml(term);
      const regex = new RegExp(`(${escapeRegex(escapedTerm)})`, 'gi');
      result = result.replace(regex, '<mark>$1</mark>');
    }
  }

  return result;
});

function escapeHtml(text: string): string {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function escapeRegex(text: string): string {
  return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
</script>

<style scoped>
.note-card {
  min-height: 100px;
  background-color: var(--card-bg);
  color: var(--text-secondary);
  padding: 1em;
  border-radius: 10px;
  cursor: pointer;
  margin-bottom: 1em;
  border: 1px solid var(--border-color);
  transition: background-color 0.2s ease, border-color 0.2s ease;
}

.note-card:hover {
  transform: translateY(0.05em);
  border-color: var(--border-color-light);
}

.note-card > h1 {
  text-align: center;
  color: var(--text-primary);
}

.tag-margin {
  margin-top: 10px;
}

.search-snippet {
  margin-top: 0.75em;
  padding: 0.5em 0.75em;
  background-color: var(--code-bg);
  border-radius: 4px;
  font-size: 0.9em;
  line-height: 1.4;
  color: var(--text-muted);
  white-space: pre-wrap;
  word-break: break-word;
}

.search-snippet :deep(mark) {
  background-color: var(--accent-warning);
  color: #333;
  padding: 0 2px;
  border-radius: 2px;
}
</style>
