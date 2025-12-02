<template>
  <div class="header-wrapper light-white" @click="prevent($event)">
    <div class="main-header">
      <!-- Left section - sidebar toggle and actions -->
      <div class="header-left">
        <div class="header-item alt-button" @click="toggleSidebar(true)">
          <b-icon
            v-show="!sidebar.hide"
            icon="grip-lines"
          >
          </b-icon>
        </div>
        <div class="header-item alt-button" @click="toggleSidebar()">
          <b-icon
            v-show="sidebar.hide"
            icon="grip-lines-vertical"
          >
          </b-icon>
        </div>
        <div class="header-item alt-button hide-mobile" v-if="!options.hideCreate">
          <div @click="newNote()">
            <b-tooltip label="Create new note" position="is-bottom">
              <b-icon icon="plus"></b-icon>
            </b-tooltip>
          </div>
        </div>
        <div class="hide-mobile">
          <Tasks></Tasks>
        </div>
        <div class="header-item alt-button hide-mobile">
          <div @click="goToSearch()">
            <b-tooltip label="Search notes" position="is-bottom">
              <b-icon icon="search"></b-icon>
            </b-tooltip>
          </div>
        </div>
      </div>

      <!-- Center section - title and date navigation -->
      <div class="header-center">
        <div @click="prevDay()" class="alt-button nav-button" v-if="options.showDateNavs">
          <b-icon icon="chevron-left"></b-icon>
        </div>
        <div class="header-title light-white">{{ options.title }}</div>
        <div @click="nextDay()" class="alt-button nav-button" v-if="options.showDateNavs">
          <b-icon icon="chevron-right"></b-icon>
        </div>
      </div>

      <!-- Right section - save, delete, menu -->
      <div class="header-right">
        <div class="header-item" v-if="isSaving">
          <div class="header-loading">
            <b-loading :is-full-page="false" :active="true"></b-loading>
          </div>
        </div>
        <div
          v-show="options.showPreview"
          class="header-item alt-button hide-mobile"
          v-bind:class="{ 'preview-active': options.previewMode !== 'none' }"
        >
          <b-dropdown position="is-bottom-left">
            <template #trigger>
              <b-tooltip label="Preview" position="is-bottom">
                <b-icon icon="eye"></b-icon>
              </b-tooltip>
            </template>
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
          class="header-item alt-button"
          v-bind:class="{ 'save-disabled': options.saveDisabled }"
          @click="save()"
        >
          <b-tooltip label="Save" position="is-bottom">
            <b-icon icon="save"></b-icon>
          </b-tooltip>
        </div>
        <div
          class="header-item alt-button hide-mobile"
          v-show="options.showDelete"
          @click="deleteNote()"
        >
          <b-tooltip label="Delete" position="is-bottom">
            <b-icon icon="trash-alt"></b-icon>
          </b-tooltip>
        </div>
        <div class="header-item alt-button">
          <b-dropdown position="is-bottom-left">
            <template #trigger>
              <b-icon icon="ellipsis-v"></b-icon>
            </template>
            <!-- Mobile-only menu items -->
            <b-dropdown-item class="show-mobile-only" v-if="!options.hideCreate" @click="newNote()">
              <b-icon icon="plus" size="is-small"></b-icon>
              <span class="dropdown-text">New Note</span>
            </b-dropdown-item>
            <b-dropdown-item class="show-mobile-only" @click="goToSearch()">
              <b-icon icon="search" size="is-small"></b-icon>
              <span class="dropdown-text">Search</span>
            </b-dropdown-item>
            <b-dropdown-item class="show-mobile-only" v-if="options.showPreview" @click="togglePreview('replace')">
              <b-icon icon="eye" size="is-small"></b-icon>
              <span class="dropdown-text">Preview</span>
            </b-dropdown-item>
            <b-dropdown-item class="show-mobile-only" v-if="options.showDelete" @click="deleteNote()">
              <b-icon icon="trash-alt" size="is-small"></b-icon>
              <span class="dropdown-text">Delete</span>
            </b-dropdown-item>
            <hr class="dropdown-divider show-mobile-only" v-if="options.showDelete || options.showPreview || !options.hideCreate" />
            <!-- Always visible menu items -->
            <b-dropdown-item @click="openSettings()">Settings</b-dropdown-item>
            <b-dropdown-item @click="exportNotes()">Export Notes</b-dropdown-item>
            <b-dropdown-item @click="triggerImport()">Import Notes</b-dropdown-item>
            <b-dropdown-item @click="logout()">Logout</b-dropdown-item>
            <input
              ref="importInput"
              type="file"
              accept=".zip"
              style="display: none"
              @change="importNotes"
            />
          </b-dropdown>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { addDays } from 'date-fns/addDays';
import { format } from 'date-fns/format';
import { subDays } from 'date-fns/subDays';
import _ from 'lodash';
import { getCurrentInstance, ref } from 'vue';
import { useRouter } from 'vue-router';
import type { IHeaderOptions } from '../interfaces';
import { NoteService } from '../services/notes';
import SidebarInst from '../services/sidebar';
import { clearToken } from '../services/user';
import Settings from './Settings.vue';
import Tasks from './Tasks.vue';

interface Props {
  options: IHeaderOptions;
}

const props = defineProps<Props>();
const router = useRouter();
const instance = getCurrentInstance();
const buefy = (instance?.appContext.config.globalProperties as any).$buefy;

const sidebar = SidebarInst;
const isSaving = ref(false);
const importInput = ref<HTMLInputElement>();

const toggleSidebar = (show = false) => {
  sidebar.hide = show;
};

const newNote = () => {
  router.push({ name: 'new-note' }).catch((_err) => {});
};

const goToSearch = () => {
  router.push({ name: 'search' }).catch((_err) => {});
};

const prevent = ($event: Event) => {
  $event.stopPropagation();
};

const prevDay = () => {
  const date = subDays(sidebar.date || new Date(), 1);
  router.push({ name: 'day-id', params: { id: format(date, 'MM-dd-yyyy') } });
};

const nextDay = () => {
  const date = addDays(sidebar.date || new Date(), 1);
  router.push({ name: 'day-id', params: { id: format(date, 'MM-dd-yyyy') } });
};

const save = async () => {
  if (
    props.options.saveDisabled ||
    isSaving.value ||
    !props.options.saveFn ||
    !_.isFunction(props.options.saveFn)
  ) {
    return;
  }

  isSaving.value = true;

  try {
    await props.options.saveFn();
  } catch (_e) {}

  isSaving.value = false;
};

const deleteNote = async () => {
  if (
    !props.options.showDelete ||
    isSaving.value ||
    !props.options.deleteFn ||
    !_.isFunction(props.options.deleteFn)
  ) {
    return;
  }

  isSaving.value = true;

  try {
    await props.options.deleteFn();
  } catch (_e) {}

  isSaving.value = false;
};

const exportNotes = async () => {
  NoteService.exportNotes();
};

const triggerImport = () => {
  const input = importInput.value;
  if (input) {
    input.click();
  }
};

const importNotes = async (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];

  if (!file) {
    return;
  }

  buefy?.dialog.confirm({
    title: 'Import Notes',
    message:
      'Importing notes will add all notes from the ZIP file. Daily notes that already exist will be skipped. Do you want to continue?',
    confirmText: 'Import',
    type: 'is-info',
    hasIcon: true,
    onConfirm: async () => {
      const loading = buefy?.loading.open({
        container: null,
      });

      try {
        const result = await NoteService.importNotes(file);

        loading?.close();

        buefy?.toast.open({
          message: `Import completed! Imported: ${result.imported}, Skipped: ${result.skipped}, Errors: ${result.errors}`,
          type: 'is-success',
          duration: 5000,
        });

        // Reset file input
        target.value = '';

        // Refresh sidebar and calendar to show new notes
        if (sidebar) {
          if (_.isFunction(sidebar.getSidebarInfo)) {
            sidebar.getSidebarInfo();
          }
          if (_.isFunction(sidebar.getEvents)) {
            sidebar.getEvents();
          }
        }
      } catch (e: unknown) {
        loading?.close();
        let errorMessage =
          'Failed to import notes. Please make sure the file is a valid ZIP containing markdown files.';

        // Try to extract more specific error message
        if (e && typeof e === 'object' && 'response' in e) {
          const response = (e as { response?: { data?: { error?: string } } }).response;
          if (response?.data?.error) {
            errorMessage = response.data.error;
          }
        } else if (e instanceof Error && e.message) {
          errorMessage = `Import failed: ${e.message}`;
        }

        buefy?.toast.open({
          message: errorMessage,
          type: 'is-danger',
          duration: 7000,
        });
        // Reset file input
        target.value = '';
      }
    },
    onCancel: () => {
      // Reset file input
      target.value = '';
    },
  });
};

const togglePreview = (mode: 'side' | 'replace' | 'none') => {
  if (props.options.togglePreviewFn && _.isFunction(props.options.togglePreviewFn)) {
    props.options.togglePreviewFn(mode);
  }
};

const closePreview = () => {
  if (props.options.togglePreviewFn && _.isFunction(props.options.togglePreviewFn)) {
    props.options.togglePreviewFn('none');
  }
};

const openSettings = () => {
  buefy?.modal.open({
    parent: instance,
    component: Settings,
    hasModalCard: true,
    trapFocus: true,
    canCancel: ['escape', 'x'],
  });
};

const logout = () => {
  clearToken();
  router.push({ name: 'Login' });
};
</script>

<style scoped>
.header-wrapper {
  width: 100%;
  padding: 10px 12px 0px 12px;
  border-bottom: 2px solid var(--main-bg-darker);
  position: sticky;
  z-index: 30;
  top: 0;
  background-color: var(--main-bg-color);
}

.main-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 3em;
  gap: 8px;
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.header-center {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  min-width: 0; /* Allow text truncation */
  overflow: hidden;
}

.header-item {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px;
}

.nav-button {
  padding: 4px;
  flex-shrink: 0;
}

.header-title {
  font-weight: bold;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
  font-size: 0.95rem;
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

/* Mobile-only items in dropdown - hidden by default */
.show-mobile-only {
  display: none !important;
}

/* Hide elements on mobile */
@media screen and (max-width: 767px) {
  .hide-mobile {
    display: none !important;
  }

  .show-mobile-only {
    display: flex !important;
  }

  .header-wrapper {
    padding: 8px 8px 0px 8px;
  }

  .main-header {
    gap: 4px;
  }

  .header-title {
    font-size: 0.85rem;
    padding: 0 4px;
  }
}

/* Tablet and up */
@media screen and (min-width: 768px) {
  .header-wrapper {
    padding: 10px 20px 0px 20px;
  }

  .header-title {
    margin-left: 0.5em;
    margin-right: 0.5em;
  }

  .header-left,
  .header-right {
    gap: 8px;
  }
}
</style>
