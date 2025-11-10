<template>
  <div>
    <Header :options="headerOptions"></Header>
    <div v-if="!isLoading" class="editor-container" :class="{ 'split-view': previewMode === 'side' }">
      <Editor
        ref="editor"
        v-show="previewMode !== 'replace'"
        v-bind:value="modifiedText || text"
        :useVimMode="sidebar.vimMode"
        v-on:valChanged="valChanged"
        v-on:saveShortcut="saveNote"
        :class="{ 'editor-split': previewMode === 'side' }"
      ></Editor>
      <MarkdownPreview
        v-if="previewMode !== 'none'"
        v-bind:value="modifiedText || text"
        v-on:checkbox-toggled="handleCheckboxToggled"
        :class="{ 'preview-split': previewMode === 'side' }"
      ></MarkdownPreview>
    </div>
    <div v-else class="loading-wrapper">
      <b-loading :is-full-page="false" :active="isLoading"></b-loading>
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import { Route } from "vue-router";
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
import MarkdownPreview from '@/components/MarkdownPreview.vue';

import {IHeaderOptions} from '../interfaces';


Component.registerHooks([
  'metaInfo',
  'beforeRouteUpdate',
  'beforeRouteLeave'
]);

@Component({
  components: {
    Editor,
    Header,
    MarkdownPreview,
  }
})
export default class Note extends Vue {
  public sidebar = SidebarInst;
  public text: string = '';
  public modifiedText : string = '';
  public unsavedChanges : boolean = false;
  public title: string = 'Note';
  public note!: INote;
  public isLoading: boolean = false;
  public isSaving: boolean = false;
  public previewMode: 'none' | 'side' | 'replace' = 'none';
  public headerOptions: IHeaderOptions = {
    showDelete: true,
    showPreview: true,
    previewMode: 'none',
    title: '',
    saveDisabled: true,
    saveFn: () => this.saveNote(),
    deleteFn: () => this.deleteNote(),
    togglePreviewFn: (mode) => this.togglePreview(mode),
  }

  public metaInfo(): any {
    return {
      title: this.title
    };
  };

  created() {
    window.addEventListener('beforeunload', this.unsavedAlert);
    window.addEventListener('keydown', this.handleKeydown);
  }

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

  beforeRouteUpdate(to: Route, from: Route, next: Function) {
    if (this.unsavedChanges) {
      this.unsavedDialog(next);
    } else {
      next();
    }
  }

  beforeRouteLeave(to: Route, from: Route, next: Function) {
    if (this.unsavedChanges) {
      this.unsavedDialog(next);
    } else {
      next();
    }
  }

  beforeDestroy() {
    window.removeEventListener('beforeunload', this.unsavedAlert);
    window.removeEventListener('keydown', this.handleKeydown);
    // Cancel any pending autosaves when component is destroyed
    this.autoSaveThrottle.cancel();
  }

  public async saveNote(isAutoSave: boolean = false) {
    // Cancel any pending autosave when manually saving
    if (!isAutoSave) {
      this.autoSaveThrottle.cancel();
    }

    // Prevent concurrent saves
    if (this.isSaving) {
      return;
    }

    // Don't save if there are no changes
    if (this.modifiedText === this.text) {
      return;
    }

    this.isSaving = true;
    const updatedNote = Object.assign(this.note, {data: this.modifiedText});

    try {
      this.note = await NoteService.saveNote(updatedNote);
      this.text = this.modifiedText;
      this.modifiedText = '';  // Reset so editor shows the saved text
      this.headerOptions.title = this.note.title || '';

      // Update the UI state directly
      this.unsavedChanges = false;
      this.title = this.note.title || '';
      this.headerOptions.saveDisabled = true;

      this.sidebar.getSidebarInfo();

      // Show subtle feedback for autosave
      if (isAutoSave) {
        this.$buefy.toast.open({
          duration: 1500,
          message: 'Autosaved',
          position: 'is-bottom-right',
          type: 'is-success'
        });
      }
    } catch(e) {
      this.$buefy.toast.open({
        duration: 5000,
        message: 'There was an error saving. Please try again.',
        position: 'is-top',
        type: 'is-danger'
      });
    } finally {
      this.isSaving = false;
    }
  }

  public async deleteNote() {
    this.$buefy.dialog.confirm({
      title: 'Deleting Note',
      message: 'Are you sure you want to <b>delete</b> this note? This action cannot be undone!',
      confirmText: 'Delete',
      focusOn: 'cancel',
      type: 'is-danger',
      hasIcon: true,
      onConfirm: async () => {
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
        this.$buefy.toast.open({
          duration: 2000,
          message: 'Note deleted!'
        });
      }
    })
  }

  public valChanged(data: string) {
    this.modifiedText = data;

    if (this.modifiedText !== this.text) {
      this.unsavedChanges = true;
      this.title = `* ${this.note.title}`;
      this.headerOptions.saveDisabled = false;

      if (this.sidebar.autoSave) {
        this.autoSaveThrottle();
      }
    } else {
      this.title = this.note.title || '';
      this.headerOptions.saveDisabled = true;
    }
  }

  public autoSaveThrottle = _.debounce(() => this.saveNote(true), 3000, {
    leading: false,
    trailing: true
  });

  private cmdKPressed: boolean = false;
  private cmdKTimeout: any = null;

  public handleKeydown(e: KeyboardEvent) {
    // Handle Cmd+K then V for side-by-side preview
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      this.cmdKPressed = true;

      // Reset after 1 second
      if (this.cmdKTimeout) {
        clearTimeout(this.cmdKTimeout);
      }
      this.cmdKTimeout = setTimeout(() => {
        this.cmdKPressed = false;
      }, 1000);
      return;
    }

    // V after Cmd+K
    if (this.cmdKPressed && e.key === 'v') {
      e.preventDefault();
      this.cmdKPressed = false;
      if (this.cmdKTimeout) {
        clearTimeout(this.cmdKTimeout);
      }
      this.togglePreview('side');
      return;
    }

    // Handle Shift+Cmd+V for preview only
    if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'v') {
      e.preventDefault();
      this.togglePreview('replace');
      return;
    }
  }

  public togglePreview(mode: 'side' | 'replace' | 'none') {
    const wasHidden = this.previewMode === 'replace';

    if (mode === 'none') {
      this.previewMode = 'none';
    } else if (this.previewMode === mode) {
      this.previewMode = 'none';
    } else {
      this.previewMode = mode;
    }
    this.headerOptions.previewMode = this.previewMode;

    // Refresh the editor when it becomes visible
    if (wasHidden && this.previewMode !== 'replace') {
      this.$nextTick(() => {
        const editor = this.$refs.editor as any;
        if (editor && editor.refresh) {
          editor.refresh();
        }
      });
    }
  }

  public handleCheckboxToggled(updatedMarkdown: string) {
    // Update the text with the toggled checkbox
    this.valChanged(updatedMarkdown);
  }

  unsavedAlert(e: Event) {
    if (this.unsavedChanges) {
      // Attempt to modify event will trigger Chrome/Firefox alert msg
      e.returnValue = true;
    }
  }

  async unsavedDialog(next: Function) {
    this.$buefy.dialog.confirm({
      title: "Unsaved Content",
      message: "Are you sure you want to discard the unsaved content?",
      confirmText: "Discard",
      type: "is-warning",
      hasIcon: true,
      onConfirm: () => next(),
      onCancel: () => next(false)
    });
  }
}
</script>

<style scoped>
.loading-wrapper {
  width: 100%;
  height: 100vh;
  position: relative;
}

.editor-container {
  height: calc(100vh - 60px);
  display: flex;
  flex-direction: row;
}

.split-view {
  display: flex;
}

.editor-split,
.preview-split {
  flex: 1;
  width: 50%;
  height: 100%;
  overflow-y: auto;
}

.editor-split {
  border-right: 1px solid #404854;
}
</style>
