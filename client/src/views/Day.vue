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
        v-on:saveShortcut="saveDay"
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
import format from 'date-fns/format';
import isValid from 'date-fns/isValid';
import parse from 'date-fns/parse';
import _ from 'lodash';
import Vue from 'vue';
import Component from 'vue-class-component';
import type { Route } from 'vue-router/types/router';
import Editor from '@/components/Editor.vue';
import Header from '@/components/Header.vue';
import MarkdownPreview from '@/components/MarkdownPreview.vue';
import UnsavedForm from '@/components/UnsavedForm.vue';
import type { IHeaderOptions, INote } from '../interfaces';
import { newDay } from '../services/consts';
import { NoteService } from '../services/notes';
import { SharedBuefy } from '../services/sharedBuefy';
import SidebarInst from '../services/sidebar';

Component.registerHooks(['metaInfo', 'beforeRouteUpdate', 'beforeRouteLeave']);

@Component({
  components: {
    Editor,
    Header,
    MarkdownPreview,
  },
})
export default class Day extends Vue {
  public sidebar = SidebarInst;
  public text: string = '';
  public modifiedText: string = '';
  public unsavedChanges: boolean = false;
  public title: string = '';
  public day!: INote;
  public isLoading: boolean = false;
  public isSaving: boolean = false;
  public previewMode: 'none' | 'side' | 'replace' = 'none';
  public headerOptions: IHeaderOptions = {
    showDateNavs: true,
    showDelete: false,
    showPreview: true,
    previewMode: 'none',
    title: '',
    saveDisabled: true,
    saveFn: () => this.saveDay(),
    deleteFn: () => this.deleteNote(),
    togglePreviewFn: (mode) => this.togglePreview(mode),
  };

  public metaInfo(): { title: string } {
    return {
      title: this.title,
    };
  }

  created() {
    window.addEventListener('beforeunload', this.unsavedAlert);
    window.addEventListener('keydown', this.handleKeydown);
  }

  mounted() {
    const date = parse(this.$route.params.id, 'MM-dd-yyyy', new Date());
    if (!isValid(date)) {
      this.$router.push({ name: 'Home Redirect' });
      this.$buefy.toast.open({
        duration: 5000,
        message: 'There was an error retrieving that date. Redirecting to today.',
        position: 'is-top',
        type: 'is-danger',
      });
      return;
    }

    this.sidebar.updateDate(this.$route);
    this.getDayData();

    this.headerOptions.title = format(date, 'EEE. MMM dd, yyyy');
    this.title = this.headerOptions.title;

    this.$root.$on('taskUpdated', (data: { note_id: string; task: string; completed: boolean }) => {
      const { note_id, task, completed } = data;

      if (note_id !== this.day.uuid) {
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

  beforeRouteUpdate(_to: Route, _from: Route, next: () => void) {
    if (this.unsavedChanges) {
      this.unsavedDialog(next);
    } else {
      next();
    }
  }

  beforeRouteLeave(_to: Route, _from: Route, next: () => void) {
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

  public async getDayData() {
    if (this.isLoading) {
      return;
    }

    this.isLoading = true;

    try {
      const res = await NoteService.getDate(this.$route.params.id);
      this.day = res;
      this.text = this.day.data || '';

      this.headerOptions.showDelete = !!this.day.uuid;
    } catch (_e) {
      SharedBuefy.openConfirmDialog({
        message: 'Failed to fetch the selected date. Would you like to start fresh or try again?',
        onConfirm: () => this.getDayData(),
        onCancel: () => this.setDefaultText(),
        confirmText: 'Try again',
        cancelText: 'Start Fresh',
      });
    }

    this.isLoading = false;
  }

  public async saveDay(isAutoSave: boolean = false) {
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
    const updatedDay = Object.assign(this.day, { data: this.modifiedText });

    try {
      const res = await NoteService.saveDay(updatedDay);
      this.text = this.modifiedText;
      this.modifiedText = ''; // Reset so editor shows the saved text
      this.day.uuid = res.uuid;

      // Update the UI state directly
      this.unsavedChanges = false;
      this.title = this.headerOptions.title;
      this.headerOptions.saveDisabled = true;
      this.headerOptions.showDelete = !!this.day.uuid;

      this.sidebar.getEvents();
      this.sidebar.getSidebarInfo();

      // Show subtle feedback for autosave
      if (isAutoSave) {
        this.$buefy.toast.open({
          duration: 1500,
          message: 'Autosaved',
          position: 'is-bottom-right',
          type: 'is-success',
        });
      }
    } catch (_e) {
      this.$buefy.toast.open({
        duration: 5000,
        message: 'There was an error saving. Please try again.',
        position: 'is-top',
        type: 'is-danger',
      });
    } finally {
      this.isSaving = false;
    }
  }

  public async deleteNote() {
    this.$buefy.dialog.confirm({
      title: 'Deleting Daily Note',
      message:
        'Are you sure you want to <b>delete</b> this daily note? This action cannot be undone!',
      confirmText: 'Delete',
      focusOn: 'cancel',
      type: 'is-danger',
      hasIcon: true,
      onConfirm: async () => {
        if (!this.day.uuid) {
          return;
        }
        try {
          await NoteService.deleteNote(this.day.uuid);
          this.sidebar.getEvents();
          this.sidebar.getSidebarInfo();
          this.$router.push({ name: 'Home Redirect' });
        } catch (_e) {
          this.$buefy.toast.open({
            duration: 5000,
            message: 'There was an error deleting note. Please try again.',
            position: 'is-top',
            type: 'is-danger',
          });
        }
        this.$buefy.toast.open({
          duration: 2000,
          message: 'Daily note deleted!',
        });
      },
    });
  }

  public setDefaultText() {
    this.text = newDay;

    this.day = {
      data: this.text,
      title: this.$route.params.id,
      uuid: null,
    };

    this.headerOptions.showDelete = false;
  }

  public valChanged(data: string) {
    this.modifiedText = data;

    if (this.modifiedText !== this.text) {
      this.unsavedChanges = true;
      this.title = `* ${this.headerOptions.title}`;
      this.headerOptions.saveDisabled = false;

      if (this.sidebar.autoSave) {
        this.autoSaveThrottle();
      }
    } else {
      this.title = this.headerOptions.title;
      this.headerOptions.saveDisabled = true;
    }
  }

  public autoSaveThrottle = _.debounce(() => this.saveDay(true), 3000, {
    leading: false,
    trailing: true,
  });

  private cmdKPressed: boolean = false;
  private cmdKTimeout: ReturnType<typeof setTimeout> | null = null;

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
        const editor = this.$refs.editor as { refresh?: () => void };
        if (editor?.refresh) {
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

  async unsavedDialog(next: (arg?: boolean) => void) {
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
          this.saveDay();
          next();
        },
      },
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
