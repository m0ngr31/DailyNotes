<template>
  <div class="note-card" @click="goToNote">
    <h1>{{ parsedTitle }}</h1>

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

<script lang="ts">
import format from 'date-fns/format';
import parse from 'date-fns/parse';
import Vue from 'vue';
import Component from 'vue-class-component';
import type { INote } from '../interfaces';
import router from '../router/index';

@Component({
  props: {
    note: {
      type: Object,
      required: true,
    },
  },
})
export default class NoteCard extends Vue {
  public note!: INote;

  public goToNote() {
    if (this.note.is_date) {
      router.push({ name: 'day-id', params: { id: this.note.title || '' } });
      return;
    }

    router.push({ name: 'note-id', params: { uuid: this.note.uuid || '' } });
  }

  get parsedTitle() {
    if (this.note.is_date) {
      try {
        return format(parse(this.note.title || '', 'MM-dd-yyyy', new Date()), 'EEE. MMM dd, yyyy');
      } catch (_e) {
        return this.note.title;
      }
    }

    return this.note.title;
  }
}
</script>

<style scoped>
.note-card {
  min-height: 100px;
  background-color: var(--main-bg-darker);
  color: #ddd;
  padding: 1em;
  border-radius: 10px;
  cursor: pointer;
  margin-bottom: 1em;
}

.note-card:hover {
  transform: translateY(0.05em);
}

.note-card > h1 {
  text-align: center;
}

.tag-margin {
  margin-top: 10px;
}
</style>