<template>
  <div>
    <Header :options="headerOptions"></Header>
    <Editor v-if="!isLoading" v-bind:value="text" v-on:valChanged="valChanged"></Editor>
    <div v-else class="loading-wrapper">
      <b-loading :is-full-page="false" :active="isLoading"></b-loading>
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import format from 'date-fns/format';
import isValid from 'date-fns/isValid';
import parse from 'date-fns/parse';
import _ from 'lodash';

import SidebarInst from '../services/sidebar';
import {NoteService} from '../services/notes';
import {SharedBuefy} from '../services/sharedBuefy';

import {INote} from '../interfaces';

import Editor from '@/components/Editor.vue';
import Header from '@/components/Header.vue';

import {IHeaderOptions} from '../interfaces';


Component.registerHooks([
  'metaInfo'
]);

@Component({
  components: {
    Editor,
    Header,
  }
})
export default class Note extends Vue {
  public sidebar = SidebarInst;
  public text: string = '';
  public modifiedText : string = '';
  public title: string = 'Note';
  public note!: INote;
  public isLoading: boolean = false;
  public headerOptions: IHeaderOptions = {
    showDelete: true,
    title: '',
    saveDisabled: true,
    saveFn: () => this.saveNote(),
    deleteFn: () => this.deleteNote(),
  }

  public metaInfo(): any {
    return {
      title: this.title
    };
  };

  async mounted() {
    this.isLoading = true;

    try {
      this.note = await NoteService.getNote(this.$route.params.uuid);
      this.text = this.note.data;

      this.headerOptions.title = this.note.title || '';
      this.title = this.note.title || '';
    } catch (e) {
      this.$router.push({name: 'Home Redirect'});
    }

    this.isLoading = false;
    
    this.$root.$on('taskUpdated', (data: any) => {
      const {note_id, task, completed} = data;

      if (note_id !== this.note.uuid) {
        return;
      }

      let original = task;

      if (!completed) {
        original = original.replace('- [ ]', '- [x]');
      } else {
        original = original.replace('- [x]', '- [ ]');
      }

      this.text = this.text.replace(original, task);
      this.modifiedText = this.modifiedText.replace(original, task);
    });
  }

  public async saveNote() {
    const updatedNote = Object.assign(this.note, {data: this.modifiedText});
    try {
      this.note = await NoteService.saveNote(updatedNote);
      this.text = this.modifiedText;
      this.headerOptions.title = this.note.title || '';

      // Update the indicators
      this.valChanged(this.text);
      this.sidebar.getSidebarInfo();
    } catch(e) {
      this.$buefy.toast.open({
        duration: 5000,
        message: 'There was an error saving. Please try again.',
        position: 'is-top',
        type: 'is-danger'
      });
    }
  }

  public async deleteNote() {
    if (!this.note.uuid) {
      return;
    }

    try {
      await NoteService.deleteNote(this.note.uuid);
      this.sidebar.getSidebarInfo();
      this.$router.push({name: 'Home Redirect'});
    } catch(e) {
      this.$buefy.toast.open({
        duration: 5000,
        message: 'There was an error deleting note. Please try again.',
        position: 'is-top',
        type: 'is-danger'
      });
    }
  }

  public valChanged(data: string) {
    this.modifiedText = data;

    if (this.modifiedText !== this.text) {
      this.title = `* ${this.note.title}`;
      this.headerOptions.saveDisabled = false;
    } else {
      this.title = this.note.title || '';
      this.headerOptions.saveDisabled = true;
    }
  }
}
</script>

<style scoped>
.loading-wrapper {
  width: 100%;
  height: 100vh;
  position: relative;
}
</style>