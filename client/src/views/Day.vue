<template>
  <div class="full-height">
    <editor v-if="!isLoading" v-bind:value="text" v-on:valChanged="valChanged"></editor>
    <div v-else class="loading-wrapper">
      <b-loading :is-full-page="false" :active="isLoading"></b-loading>
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import _ from 'lodash';

import SidebarInst from '../services/sidebar';
import {NoteService, INote} from '../services/notes';
import {SharedBuefy} from '../services/sharedBuefy';

import Editor from '@/components/Editor.vue';

Component.registerHooks([
  'metaInfo'
]);

@Component({
  components: {
    'editor': Editor,
  }
})
export default class Day extends Vue {
  public sidebar = SidebarInst;
  public text: string = '';
  public title: string = 'Day';
  public day!: INote;
  public isLoading: boolean = false;

  public metaInfo(): any {
    return {
      title: this.title
    };
  };

  mounted() {
    this.sidebar.updateDate(this.$route);
    this.getDayData();
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
    } catch (e) {
      SharedBuefy.activeDialog = this.$buefy.dialog.confirm({
        message: 'Failed to fetch the selected date. Would you like to start fresh or try again?',
        onConfirm: () => this.getDayData(),
        onCancel: () => this.setDefaultText(),
        confirmText: 'Try again',
        cancelText: 'Start Fresh'
      });
    }

    this.isLoading = false;
  }

  public setDefaultText() {
    this.text = `---\ndate: ${this.$route.params.id}\n---\n\n`;
  }

  public valChanged(data: string) {
    if (data !== this.text) {
      this.title = '* Day';
    } else {
      this.title = 'Day';
    }
  }
}
</script>

<style scoped>
.loading-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
}
</style>