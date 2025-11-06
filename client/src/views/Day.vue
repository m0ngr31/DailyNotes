<template>
  <div>
    <Header :options="headerOptions"></Header>
    <Editor v-if="!isLoading" v-bind:value="text" v-on:valChanged="valChanged" v-on:saveShortcut="saveDay"></Editor>
    <div v-else class="loading-wrapper">
      <b-loading :is-full-page="false" :active="isLoading"></b-loading>
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import type { Route } from "vue-router/types/router";
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
import UnsavedForm from '@/components/UnsavedForm.vue';

import {IHeaderOptions} from '../interfaces';

import {newDay} from '../services/consts';


Component.registerHooks([
  'metaInfo',
  'beforeRouteUpdate',
  'beforeRouteLeave'
]);

@Component({
  components: {
    Editor,
    Header,
  }
})
export default class Day extends Vue {
  public sidebar = SidebarInst;
  public text: string = '';
  public modifiedText : string = '';
  public unsavedChanges : boolean = false;
  public title: string = '';
  public day!: INote;
  public isLoading: boolean = false;
  public isSaving: boolean = false;
  public headerOptions: IHeaderOptions = {
    showDateNavs: true,
    showDelete: false,
    title: '',
    saveDisabled: true,
    saveFn: () => this.saveDay(),
    deleteFn: () => this.deleteNote(),
  }

  public metaInfo(): any {
    return {
      title: this.title
    };
  };

  created() {
    window.addEventListener('beforeunload', this.unsavedAlert);
  }

  mounted() {
    const date = parse(this.$route.params.id, 'MM-dd-yyyy', new Date());
    if (!isValid(date)) {
      this.$router.push({name: 'Home Redirect'});
      this.$buefy.toast.open({
        duration: 5000,
        message: 'There was an error retrieving that date. Redirecting to today.',
        position: 'is-top',
        type: 'is-danger'
      });
      return;
    }

    this.sidebar.updateDate(this.$route);
    this.getDayData();

    this.headerOptions.title = format(date, 'EEE. MMM dd, yyyy');
    this.title = this.headerOptions.title;

    this.$root.$on('taskUpdated', (data: any) => {
      const {note_id, task, completed} = data;

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
    } catch (e) {
      SharedBuefy.openConfirmDialog({
        message: 'Failed to fetch the selected date. Would you like to start fresh or try again?',
        onConfirm: () => this.getDayData(),
        onCancel: () => this.setDefaultText(),
        confirmText: 'Try again',
        cancelText: 'Start Fresh'
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
    const updatedDay = Object.assign(this.day, {data: this.modifiedText});

    try {
      const res = await NoteService.saveDay(updatedDay);
      if (!this.sidebar.autoSave) {
        this.text = this.modifiedText;
      }
      this.day.uuid = res.uuid;

      // Update the indicators
      this.valChanged(this.text);
      this.sidebar.getEvents();
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

    this.unsavedChanges = false;
    this.headerOptions.showDelete = !!this.day.uuid;
  }

  public async deleteNote() {
    this.$buefy.dialog.confirm({
      title: 'Deleting Daily Note',
      message: 'Are you sure you want to <b>delete</b> this daily note? This action cannot be undone!',
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
          message: 'Daily note deleted!'
        });
      }
    })
  }

  public setDefaultText() {
    this.text = newDay;

    this.day = {
      data: this.text,
      title: this.$route.params.id,
      uuid: null
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
    trailing: true
  });

  unsavedAlert(e: Event) {
    if (this.unsavedChanges) {
    // Attempt to modify event will trigger Chrome/Firefox alert msg
    e.returnValue = true;
    }
  }

  async unsavedDialog(next: Function) {
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
        }
      }
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
</style>
