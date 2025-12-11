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

<script setup lang="ts">
import { useHead } from '@unhead/vue';
import { format } from 'date-fns/format';
import { isValid } from 'date-fns/isValid';
import { parse } from 'date-fns/parse';
import _ from 'lodash';
import {
  computed,
  getCurrentInstance,
  nextTick,
  onBeforeUnmount,
  onMounted,
  reactive,
  ref,
  watch,
} from 'vue';
import { onBeforeRouteLeave, onBeforeRouteUpdate, useRoute, useRouter } from 'vue-router';
import Editor from '@/components/Editor.vue';
import Header from '@/components/Header.vue';
import MarkdownPreview from '@/components/MarkdownPreview.vue';
import UnsavedForm from '@/components/UnsavedForm.vue';
import type { IHeaderOptions, INote } from '../interfaces';
import { newDay } from '../services/consts';
import eventHub from '../services/eventHub';
import { getFoldState, saveFoldState } from '../services/localstorage';
import { NoteService } from '../services/notes';
import { SharedBuefy } from '../services/sharedBuefy';
import SidebarInst from '../services/sidebar';
import type { SSEEventData } from '../services/sse';
import { markNoteUpdatedLocally, wasRecentlyUpdatedLocally } from '../services/sse';

const router = useRouter();
const route = useRoute();
const instance = getCurrentInstance();
const buefy = (instance?.appContext.config.globalProperties as any).$buefy;
const root = instance?.appContext.config.globalProperties as any;
const sidebar = SidebarInst;

const editor = ref<InstanceType<typeof Editor>>();
const text = ref('');
const modifiedText = ref('');
const unsavedChanges = ref(false);
const title = ref('');
const day = ref<INote>({
  data: '',
  uuid: null,
});
const isLoading = ref(false);
const isSaving = ref(false);
const previewMode = ref<'none' | 'side' | 'replace'>('none');

useHead({
  title: computed(() => title.value),
});

const headerOptions = reactive<IHeaderOptions>({
  showDateNavs: true,
  showDelete: false,
  showPreview: true,
  previewMode: 'none',
  title: '',
  saveDisabled: true,
  saveFn: () => saveDay(),
  deleteFn: () => deleteNote(),
  togglePreviewFn: (mode) => togglePreview(mode),
});

let cmdKPressed = false;
let cmdKTimeout: ReturnType<typeof setTimeout> | null = null;
let currentNoteId: string | null = null;

const autoSaveThrottle = _.debounce(() => saveDay(true), 3000, {
  leading: false,
  trailing: true,
});

const saveCurrentFoldState = () => {
  if (currentNoteId && editor.value?.getFoldState) {
    const folds = editor.value.getFoldState();
    saveFoldState(currentNoteId, folds);
  }
};

const restoreFoldState = () => {
  if (currentNoteId && editor.value?.setFoldState) {
    const folds = getFoldState(currentNoteId);
    if (folds.length) {
      editor.value.setFoldState(folds);
    }
  }
};

const getDayData = async () => {
  if (isLoading.value) {
    return;
  }

  isLoading.value = true;

  try {
    const res = await NoteService.getDate(route.params.id as string);
    day.value = res;
    text.value = day.value.data || '';

    // Set current note ID for fold state (use date as identifier for daily notes)
    currentNoteId = `day-${route.params.id}`;

    // Set current note ID for Kanban filtering
    sidebar.currentNoteId = day.value.uuid || null;

    headerOptions.showDelete = !!day.value.uuid;

    // Restore fold state after content is loaded
    nextTick(() => {
      restoreFoldState();
    });
  } catch (_e) {
    SharedBuefy.openConfirmDialog({
      message: 'Failed to fetch the selected date. Would you like to start fresh or try again?',
      onConfirm: () => getDayData(),
      onCancel: () => setDefaultText(),
      confirmText: 'Try again',
      cancelText: 'Start Fresh',
    });
  }

  isLoading.value = false;
};

const saveDay = async (isAutoSave: boolean = false) => {
  // Cancel any pending autosave when manually saving
  if (!isAutoSave) {
    autoSaveThrottle.cancel();
  }

  // Prevent concurrent saves
  if (isSaving.value) {
    return;
  }

  // Don't save if there are no changes
  if (modifiedText.value === text.value) {
    return;
  }

  isSaving.value = true;
  const updatedDay = Object.assign(day.value, { data: modifiedText.value });

  try {
    const res = await NoteService.saveDay(updatedDay);
    // Mark as locally updated to prevent SSE duplicate processing
    if (res.uuid) {
      markNoteUpdatedLocally(res.uuid);
    }
    text.value = modifiedText.value;
    // Don't reset modifiedText - it's already correct and resetting causes editor glitches
    day.value.uuid = res.uuid;

    // Update sidebar with current note ID for Kanban filtering
    sidebar.currentNoteId = day.value.uuid || null;

    // Update the UI state directly
    unsavedChanges.value = false;
    title.value = headerOptions.title;
    headerOptions.saveDisabled = true;
    headerOptions.showDelete = !!day.value.uuid;

    sidebar.getEvents();
    sidebar.getSidebarInfo();

    // Show subtle feedback for autosave
    if (isAutoSave) {
      buefy?.toast.open({
        duration: 1500,
        message: 'Autosaved',
        position: 'is-bottom-right',
        type: 'is-success',
      });
    }
  } catch (_e) {
    buefy?.toast.open({
      duration: 5000,
      message: 'There was an error saving. Please try again.',
      position: 'is-top',
      type: 'is-danger',
    });
  } finally {
    isSaving.value = false;
  }
};

const deleteNote = async () => {
  buefy?.dialog.confirm({
    title: 'Deleting Daily Note',
    message:
      'Are you sure you want to <b>delete</b> this daily note? This action cannot be undone!',
    confirmText: 'Delete',
    focusOn: 'cancel',
    type: 'is-danger',
    hasIcon: true,
    onConfirm: async () => {
      if (!day.value.uuid) {
        return;
      }
      try {
        await NoteService.deleteNote(day.value.uuid);
        sidebar.getEvents();
        sidebar.getSidebarInfo();
        router.push({ name: 'Home Redirect' });
      } catch (_e) {
        buefy?.toast.open({
          duration: 5000,
          message: 'There was an error deleting note. Please try again.',
          position: 'is-top',
          type: 'is-danger',
        });
      }
      buefy?.toast.open({
        duration: 2000,
        message: 'Daily note deleted!',
      });
    },
  });
};

const setDefaultText = () => {
  text.value = newDay;

  day.value = {
    data: text.value,
    title: route.params.id as string,
    uuid: null,
  };

  headerOptions.showDelete = false;
};

const valChanged = (data: string) => {
  modifiedText.value = data;

  if (modifiedText.value !== text.value) {
    unsavedChanges.value = true;
    title.value = `* ${headerOptions.title}`;
    headerOptions.saveDisabled = false;

    if (sidebar.autoSave) {
      autoSaveThrottle();
    }
  } else {
    title.value = headerOptions.title;
    headerOptions.saveDisabled = true;
  }
};

const handleKeydown = (e: KeyboardEvent) => {
  // Handle Cmd+K then V for side-by-side preview
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault();
    cmdKPressed = true;

    // Reset after 1 second
    if (cmdKTimeout) {
      clearTimeout(cmdKTimeout);
    }
    cmdKTimeout = setTimeout(() => {
      cmdKPressed = false;
    }, 1000);
    return;
  }

  // V after Cmd+K
  if (cmdKPressed && e.key === 'v') {
    e.preventDefault();
    cmdKPressed = false;
    if (cmdKTimeout) {
      clearTimeout(cmdKTimeout);
    }
    togglePreview('side');
    return;
  }

  // Handle Shift+Cmd+V for preview only
  if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === 'v') {
    e.preventDefault();
    togglePreview('replace');
    return;
  }
};

const handleTaskUpdate = (data: { note_id: string; task: string; completed: boolean }) => {
  const { note_id, task, completed } = data;

  if (note_id !== day.value.uuid) {
    return;
  }

  let original = task;

  if (!completed) {
    original = original.replace('- [ ]', '- [x]');
  } else {
    original = original.replace('- [x]', '- [ ]');
  }

  text.value = text.value.replace(original, task);
  modifiedText.value = modifiedText.value.replace(original, task);
};

const handleTaskColumnUpdate = (data: { note_id: string; old_task: string; new_task: string }) => {
  const { note_id, old_task, new_task } = data;

  if (note_id !== day.value.uuid) {
    return;
  }

  text.value = text.value.replace(old_task, new_task);
  modifiedText.value = modifiedText.value.replace(old_task, new_task);
};

// Handle SSE events for real-time sync from other browsers/devices
const handleSSENoteUpdated = async (data: SSEEventData) => {
  // Only handle updates for the current note
  if (data.note_uuid !== day.value.uuid) {
    return;
  }

  // Skip if this was a local update (prevents duplicate processing)
  if (data.note_uuid && wasRecentlyUpdatedLocally(data.note_uuid)) {
    return;
  }

  // If we have unsaved changes, don't overwrite - notify user instead
  if (unsavedChanges.value) {
    buefy?.toast.open({
      duration: 5000,
      message: 'Note updated elsewhere. Save your changes to sync.',
      position: 'is-top',
      type: 'is-warning',
    });
    return;
  }

  // Reload the note content
  try {
    const res = await NoteService.getDate(route.params.id as string);
    day.value = res;
    text.value = day.value.data || '';
    modifiedText.value = text.value;

    buefy?.toast.open({
      duration: 2000,
      message: 'Note synced from another device',
      position: 'is-bottom-right',
      type: 'is-info',
    });
  } catch (_e) {
    console.error('Failed to sync note update:', _e);
  }
};

const handleSSETaskColumnUpdated = (data: SSEEventData) => {
  // Handle task column updates from other browsers/devices
  if (data.note_uuid !== day.value.uuid) {
    return;
  }

  // Skip if this was a local update (prevents duplicate processing)
  if (data.note_uuid && wasRecentlyUpdatedLocally(data.note_uuid)) {
    return;
  }

  if (data.old_task && data.new_task) {
    // If we have unsaved changes, check if the task line exists
    if (unsavedChanges.value) {
      // Only update if the old task line exists (not already modified locally)
      if (modifiedText.value.includes(data.old_task)) {
        modifiedText.value = modifiedText.value.replace(data.old_task, data.new_task);
      }
      if (text.value.includes(data.old_task)) {
        text.value = text.value.replace(data.old_task, data.new_task);
      }
    } else {
      text.value = text.value.replace(data.old_task, data.new_task);
      modifiedText.value = text.value;
    }

    // Refresh sidebar to update Kanban
    sidebar.getSidebarInfo();
  }
};

const togglePreview = (mode: 'side' | 'replace' | 'none') => {
  const wasHidden = previewMode.value === 'replace';

  if (mode === 'none') {
    previewMode.value = 'none';
  } else if (previewMode.value === mode) {
    previewMode.value = 'none';
  } else {
    previewMode.value = mode;
  }
  headerOptions.previewMode = previewMode.value;

  // Refresh the editor when it becomes visible
  if (wasHidden && previewMode.value !== 'replace') {
    nextTick(() => {
      if (editor.value?.refresh) {
        editor.value.refresh();
      }
    });
  }
};

const handleCheckboxToggled = (updatedMarkdown: string) => {
  // Update the text with the toggled checkbox
  valChanged(updatedMarkdown);
};

const unsavedAlert = (e: Event) => {
  // Save fold state before page unload
  saveCurrentFoldState();

  if (unsavedChanges.value) {
    // Attempt to modify event will trigger Chrome/Firefox alert msg
    e.returnValue = true;
  }
};

const unsavedDialog = async (next: (arg?: boolean) => void) => {
  buefy?.modal.open({
    parent: instance,
    component: UnsavedForm,
    hasModalCard: true,
    trapFocus: true,
    events: {
      cancel: () => {
        next(false);
      },
      discard: () => {
        unsavedChanges.value = false;
        modifiedText.value = '';
        next();
      },
      save: async () => {
        await saveDay();
        unsavedChanges.value = false;
        next();
      },
    },
  });
};

onBeforeRouteUpdate((_to, _from, next) => {
  if (unsavedChanges.value) {
    unsavedDialog(next);
  } else {
    next();
  }
});

onBeforeRouteLeave((_to, _from, next) => {
  // Save fold state before leaving
  saveCurrentFoldState();

  if (unsavedChanges.value) {
    unsavedDialog(next);
  } else {
    next();
  }
});

// Watch for route changes to update the sidebar date and reload day data
watch(
  () => route.params.id,
  () => {
    const date = parse(route.params.id as string, 'MM-dd-yyyy', new Date());
    if (!isValid(date)) {
      router.push({ name: 'Home Redirect' });
      buefy?.toast.open({
        duration: 5000,
        message: 'There was an error retrieving that date. Redirecting to today.',
        position: 'is-top',
        type: 'is-danger',
      });
      return;
    }

    sidebar.updateDate(route);
    getDayData();

    headerOptions.title = format(date, 'EEE. MMM dd, yyyy');
    title.value = headerOptions.title;
  }
);

onMounted(() => {
  window.addEventListener('beforeunload', unsavedAlert);
  window.addEventListener('keydown', handleKeydown);

  const date = parse(route.params.id as string, 'MM-dd-yyyy', new Date());
  if (!isValid(date)) {
    router.push({ name: 'Home Redirect' });
    buefy?.toast.open({
      duration: 5000,
      message: 'There was an error retrieving that date. Redirecting to today.',
      position: 'is-top',
      type: 'is-danger',
    });
    return;
  }

  sidebar.updateDate(route);
  getDayData();

  headerOptions.title = format(date, 'EEE. MMM dd, yyyy');
  title.value = headerOptions.title;

  eventHub.on('taskUpdated', handleTaskUpdate);
  eventHub.on('taskColumnUpdated', handleTaskColumnUpdate);
  eventHub.on('sseNoteUpdated', handleSSENoteUpdated);
  eventHub.on('sseTaskColumnUpdated', handleSSETaskColumnUpdated);
});

onBeforeUnmount(() => {
  // Save fold state before component is destroyed
  saveCurrentFoldState();

  window.removeEventListener('beforeunload', unsavedAlert);
  window.removeEventListener('keydown', handleKeydown);
  eventHub.off('taskUpdated', handleTaskUpdate);
  eventHub.off('taskColumnUpdated', handleTaskColumnUpdate);
  eventHub.off('sseNoteUpdated', handleSSENoteUpdated);
  eventHub.off('sseTaskColumnUpdated', handleSSETaskColumnUpdated);
  // Cancel any pending autosaves when component is destroyed
  autoSaveThrottle.cancel();
});
</script>

<style scoped>
.loading-wrapper {
  width: 100%;
  height: 100vh;
  position: relative;
}

.editor-container {
  height: calc(100vh - 60px);
  height: calc(100dvh - 60px); /* Dynamic viewport height for mobile */
  width: 100%;
  display: flex;
  flex-direction: row;
  border: none;
  outline: none;
  padding: 0 12px;
  box-sizing: border-box;
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

/* external events component sits above editor */
:deep(.external-events) {
  margin: 12px;
}

/* Mobile styles */
@media screen and (max-width: 767px) {
  .editor-container {
    height: calc(100vh - 52px);
    height: calc(100dvh - 52px);
    padding: 0 4px;
  }

  /* On mobile, split view stacks vertically */
  .split-view {
    flex-direction: column;
  }

  .editor-split,
  .preview-split {
    width: 100%;
    height: 50%;
  }

  .editor-split {
    border-right: none;
    border-bottom: 1px solid #404854;
  }

  :deep(.external-events) {
    margin: 8px;
  }
}
</style>
