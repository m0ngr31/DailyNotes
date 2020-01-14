<template>
  <div>
    <Header :options="headerOptions"></Header>
    <Editor v-bind:value="text" v-on:valChanged="valChanged"></Editor>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';

import SidebarInst from '../services/sidebar';
import {NoteService} from '../services/notes';

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
export default class NewNote extends Vue {
  public sidebar = SidebarInst;
  public text: string = '';
  public modifiedText : string = '';
  public title: string = 'New Note';
  public note!: INote;
  public headerOptions: IHeaderOptions = {
    title: 'New Note',
    saveDisabled: true,
    saveFn: () => this.saveNote(),
  };

  public metaInfo(): any {
    return {
      title: this.title
    };
  };

  mounted() {
    this.text = `---\ntitle:\ntags:\nprojects:\n---\n\n`;

    this.note = {
      data: this.text,
      uuid: null
    };
  }

  public async saveNote() {
    const updatedNote = Object.assign(this.note, {data: this.modifiedText});
    try {
      const res = await NoteService.createNote(updatedNote);
      this.sidebar.getSidebarInfo();
      this.$router.push({name: 'note-id', params: {uuid: (res as any).uuid}})
    } catch(e) {
      this.$buefy.toast.open({
        duration: 5000,
        message: 'There was an error saving. Please try again.',
        position: 'is-top',
        type: 'is-danger'
      });
    }

    this.headerOptions.showDelete = !!this.note.uuid;
  }

  public valChanged(data: string) {
    this.modifiedText = data;

    if (this.modifiedText !== this.text) {
      this.title = '* New Note';
      this.headerOptions.saveDisabled = false;
    } else {
      this.title = 'New Note';
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