<template>
  <div class="header-wrapper light-white" @click="prevent($event)">
    <div class="main-header level is-mobile">
      <div class="level-left">
        <div class="level-item alt-button" @click="toggleSidebar(true)">
          <b-icon
            v-show="!sidebar.hide"
            icon="grip-lines"
          >
          </b-icon>
        </div>
        <div class="level-item alt-button" @click="toggleSidebar()">
          <b-icon
            v-show="sidebar.hide"
            icon="grip-lines-vertical"
          >
          </b-icon>
        </div>
        <div class="level-item alt-button" v-if="!options.hideCreate">
          <div @click="newNote()">
            <b-tooltip label="Create new note" position="is-bottom">
              <b-icon icon="plus"></b-icon>
            </b-tooltip>
          </div>
        </div>
        <Tasks></Tasks>
        <div class="level-item alt-button">
          <div @click="goToSearch()">
            <b-tooltip label="Search notes" position="is-bottom">
              <b-icon icon="search"></b-icon>
            </b-tooltip>
          </div>
        </div>
      </div>
      <div class="level-item has-text-primary">
        <div @click="prevDay()" class="alt-button" v-if="options.showDateNavs">
          <b-icon icon="chevron-left"></b-icon>
        </div>
        <div class="header-title light-white">{{ options.title }}</div>
        <div @click="nextDay()" class="alt-button" v-if="options.showDateNavs">
          <b-icon icon="chevron-right"></b-icon>
        </div>
      </div>
      <div class="level-right">
        <div class="level-item" v-if="isSaving">
          <div class="header-loading">
            <b-loading :is-full-page="false" :active="true"></b-loading>
          </div>
        </div>
        <div
          v-show="options.showPreview"
          class="level-item alt-button"
          v-bind:class="{ 'preview-active': options.previewMode !== 'none' }"
        >
          <b-dropdown position="is-bottom-left">
            <b-tooltip slot="trigger" label="Preview" position="is-bottom">
              <b-icon icon="eye"></b-icon>
            </b-tooltip>
            <b-dropdown-item @click="togglePreview('side')">
              <b-icon icon="columns" size="is-small"></b-icon>
              <span class="dropdown-text">Preview Side-by-Side</span>
              <span class="dropdown-shortcut">⌘K V</span>
            </b-dropdown-item>
            <b-dropdown-item @click="togglePreview('replace')">
              <b-icon icon="file-alt" size="is-small"></b-icon>
              <span class="dropdown-text">Preview Only</span>
              <span class="dropdown-shortcut">⇧⌘V</span>
            </b-dropdown-item>
            <b-dropdown-item v-if="options.previewMode !== 'none'" @click="closePreview()">
              <b-icon icon="times" size="is-small"></b-icon>
              <span class="dropdown-text">Close Preview</span>
            </b-dropdown-item>
          </b-dropdown>
        </div>
        <div
          v-show="options.saveFn"
          class="level-item alt-button"
          v-bind:class="{ 'save-disabled': options.saveDisabled }"
          @click="save()"
        >
          <b-tooltip label="Save" position="is-bottom">
            <b-icon icon="save"></b-icon>
          </b-tooltip>
        </div>
        <div
          class="level-item alt-button"
          v-show="options.showDelete"
          @click="deleteNote()"
        >
          <b-tooltip label="Delete" position="is-bottom">
            <b-icon icon="trash-alt"></b-icon>
          </b-tooltip>
        </div>
        <div class="level-item alt-button">
          <b-dropdown position="is-bottom-left" :close-on-click="false">
            <b-icon slot="trigger" icon="ellipsis-v"></b-icon>
            <b-dropdown-item>
              <b-switch
                v-model="sidebar.autoSave"
                @input="sidebar.toggleAutoSave"
              >
                {{ sidebar.autoSave ? 'Disable Auto-Save' : 'Enable Auto-Save' }}
              </b-switch>
            </b-dropdown-item>
            <b-dropdown-item @click="exportNotes()">Export Notes</b-dropdown-item>
            <b-dropdown-item @click="logout()">Logout</b-dropdown-item>
          </b-dropdown>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import _ from 'lodash';
import addDays from 'date-fns/addDays';
import subDays from 'date-fns/subDays'
import format from 'date-fns/format';

import SidebarInst from '../services/sidebar';
import {clearToken} from '../services/user';
import {NoteService} from '../services/notes';

import {IHeaderOptions} from '../interfaces';

import Tasks from './Tasks.vue';

@Component({
  components: {
    Tasks
  },
  props: {
    options: {
      type: Object,
      required: true
    }
  }
})
export default class Header extends Vue {
  public sidebar = SidebarInst;
  public options!: IHeaderOptions;
  public isSaving: boolean = false;

  public toggleSidebar(show = false) {
    this.sidebar.hide = show;
  }

  public newNote() {
    this.$router.push({name: 'new-note'}).catch(err => {});
  }

  public goToSearch(searchType: string, tag: string) {
    this.$router.push({name: 'search'}).catch(err => {});
  }

  public prevent($event: any) {
    $event.stopPropagation();
  }

  public prevDay() {
    const date = subDays(this.sidebar.date, 1);
    this.$router.push({ name: 'day-id', params: { id: format(date, 'MM-dd-yyyy') } });
  }

  public nextDay() {
    const date = addDays(this.sidebar.date, 1);
    this.$router.push({ name: 'day-id', params: { id: format(date, 'MM-dd-yyyy') } });
  }

  public async save() {
    if (
      this.options.saveDisabled ||
      this.isSaving ||
      !this.options.saveFn ||
      !_.isFunction(this.options.saveFn)
    ) {
      return;
    }

    this.isSaving = true;

    try {
      await this.options.saveFn();
    } catch(e) {}

    this.isSaving = false;
  }

  public async deleteNote() {
    if (
      !this.options.showDelete ||
      this.isSaving ||
      !this.options.deleteFn ||
      !_.isFunction(this.options.deleteFn)
    ) {
      return;
    }

    this.isSaving = true;

    try {
      await this.options.deleteFn();
    } catch(e) {}

    this.isSaving = false;
  }

  public async exportNotes() {
    NoteService.exportNotes();
  }

  public togglePreview(mode: 'side' | 'replace' | 'none') {
    if (this.options.togglePreviewFn && _.isFunction(this.options.togglePreviewFn)) {
      this.options.togglePreviewFn(mode);
    }
  }

  public closePreview() {
    if (this.options.togglePreviewFn && _.isFunction(this.options.togglePreviewFn)) {
      this.options.togglePreviewFn('none');
    }
  }

  public logout() {
    clearToken();
    this.$router.push({name: 'Login'});
  }
}
</script>

<style scoped>
.header-wrapper {
  width: 100%;
  padding: 10px 20px 0px 20px;
  border-bottom: 2px solid var(--main-bg-darker);
  position: sticky;
  z-index: 30;
  top: 0;
  background-color: var(--main-bg-color);
}

.main-header {
  margin-right: auto;
  margin-left: auto;
  height: 3em;
}

.header-title {
  margin-left: 1em;
  margin-right: 1em;
  font-weight: bold;
}

.save-disabled {
  color: #888;
  cursor: unset;
}

.preview-active {
  color: #82aaff;
}

.dropdown-text {
  margin-left: 8px;
  margin-right: 12px;
}

.dropdown-shortcut {
  opacity: 0.6;
  font-size: 0.85em;
  margin-left: auto;
  float: right;
}
</style>
