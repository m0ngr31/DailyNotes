<template>
  <div>
    <Header :options="headerOptions"></Header>
    <Editor v-bind:value="text" :useVimMode="sidebar.vimMode" v-on:valChanged="valChanged" v-on:saveShortcut="saveNote"></Editor>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import type { Route } from 'vue-router/types/router';
import Editor from '@/components/Editor.vue';
import Header from '@/components/Header.vue';
import UnsavedForm from '@/components/UnsavedForm.vue';
import type { IHeaderOptions, INote } from '../interfaces';
import { newNote } from '../services/consts';
import { NoteService } from '../services/notes';
import SidebarInst from '../services/sidebar';

Component.registerHooks(['metaInfo', 'beforeRouteLeave']);

@Component({
  components: {
    Editor,
    Header,
  },
})
export default class NewNote extends Vue {
  public sidebar = SidebarInst;
  public text: string = '';
  public modifiedText: string = '';
  public unsavedChanges: boolean = false;
  public title: string = 'New Note';
  public note!: INote;
  public headerOptions: IHeaderOptions = {
    title: 'New Note',
    saveDisabled: true,
    saveFn: () => this.saveNote(),
  };

  public metaInfo(): { title: string } {
    return {
      title: this.title,
    };
  }

  created() {
    window.addEventListener('beforeunload', this.unsavedAlert);
  }

  mounted() {
    this.text = newNote;

    this.note = {
      data: this.text,
      uuid: null,
    };
  }

  beforeDestroy() {
    window.removeEventListener('beforeunload', this.unsavedAlert);
  }

  public async saveNote() {
    const updatedNote = Object.assign(this.note, { data: this.modifiedText });
    try {
      const res = await NoteService.createNote(updatedNote);
      this.sidebar.getSidebarInfo();
      this.unsavedChanges = false;
      this.$router.push({ name: 'note-id', params: { uuid: (res as { uuid: string }).uuid } });
    } catch (_e) {
      this.$buefy.toast.open({
        duration: 5000,
        message: 'There was an error saving. Please try again.',
        position: 'is-top',
        type: 'is-danger',
      });
    }

    this.headerOptions.showDelete = !!this.note.uuid;
  }

  beforeRouteLeave(_to: Route, _from: Route, next: (arg?: boolean) => void) {
    if (this.unsavedChanges) {
      this.$buefy.modal.open({
        parent: this,
        component: UnsavedForm,
        hasModalCard: true,
        trapFocus: true,
        events: {
          cancel: () => {
            next(false);
          },
          discard: () => {
            next();
          },
          save: () => {
            this.saveNote();
            next();
          },
        },
      });
    } else {
      next();
    }
  }

  public valChanged(data: string) {
    this.modifiedText = data;

    if (this.modifiedText !== this.text) {
      this.title = '* New Note';
      this.headerOptions.saveDisabled = false;
      this.unsavedChanges = true;
    } else {
      this.title = 'New Note';
      this.headerOptions.saveDisabled = true;
    }
  }

  unsavedAlert(e: Event) {
    if (this.unsavedChanges) {
      // Attempt to modify event will trigger Chrome/Firefox alert msg
      e.returnValue = true;
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
