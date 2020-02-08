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
export default class Day extends Vue {
  public sidebar = SidebarInst;
  public text: string = '';
  public modifiedText : string = '';
  public title: string = '';
  public day!: INote;
  public isLoading: boolean = false;
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

  mounted() {
    const date = parse(this.$route.params.id, 'MM-dd-yyyy', new Date());
    if (!isValid(date)) {
      this.$router.push({name: 'Home Redirect'});
      this.$buefy.toast.open({
        duration: 5000,
        message: 'There was an retrieving that date. Redirecting to today.',
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

  public async saveDay() {
    const updatedDay = Object.assign(this.day, {data: this.modifiedText});
    try {
      const res = await NoteService.saveDay(updatedDay);
      this.text = this.modifiedText;
      this.day.uuid = res.uuid;

      // Update the indicators
      this.valChanged(this.text);
      this.sidebar.getEvents();
      this.sidebar.getSidebarInfo();
    } catch(e) {
      this.$buefy.toast.open({
        duration: 5000,
        message: 'There was an error saving. Please try again.',
        position: 'is-top',
        type: 'is-danger'
      });
    }

    this.headerOptions.showDelete = !!this.day.uuid;
  }

  public async deleteNote() {
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
  }

  public setDefaultText() {
    this.text = `---\ntags:\nprojects:\n---\n\n`;

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
      this.title = `* ${this.headerOptions.title}`;
      this.headerOptions.saveDisabled = false;
    } else {
      this.title = this.headerOptions.title;
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