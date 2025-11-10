<template>
  <div>
    <Header :options="headerOptions"></Header>
    <Editor v-bind:value="text" :useVimMode="sidebar.vimMode" v-on:valChanged="valChanged" v-on:saveShortcut="saveNote"></Editor>
  </div>
</template>

<script setup lang="ts">
import { useHead } from '@unhead/vue';
import { computed, getCurrentInstance, onBeforeUnmount, onMounted, reactive, ref } from 'vue';
import { onBeforeRouteLeave, useRouter } from 'vue-router';
import Editor from '@/components/Editor.vue';
import Header from '@/components/Header.vue';
import UnsavedForm from '@/components/UnsavedForm.vue';
import type { IHeaderOptions, INote } from '../interfaces';
import { newNote } from '../services/consts';
import { NoteService } from '../services/notes';
import SidebarInst from '../services/sidebar';

const router = useRouter();
const instance = getCurrentInstance();
const buefy = (instance?.appContext.config.globalProperties as any).$buefy;

const sidebar = SidebarInst;
const text = ref('');
const modifiedText = ref('');
const unsavedChanges = ref(false);
const title = ref('New Note');
const note = ref<INote>({
  data: '',
  uuid: null,
});

useHead({
  title: computed(() => title.value),
});

const headerOptions = reactive<IHeaderOptions>({
  title: 'New Note',
  saveDisabled: true,
  saveFn: () => saveNote(),
});

const saveNote = async () => {
  const updatedNote = Object.assign(note.value, { data: modifiedText.value });
  try {
    const res = await NoteService.createNote(updatedNote);
    sidebar.getSidebarInfo();
    unsavedChanges.value = false;
    router.push({ name: 'note-id', params: { uuid: (res as { uuid: string }).uuid } });
  } catch (_e) {
    buefy?.toast.open({
      duration: 5000,
      message: 'There was an error saving. Please try again.',
      position: 'is-top',
      type: 'is-danger',
    });
  }

  headerOptions.showDelete = !!note.value.uuid;
};

const valChanged = (data: string) => {
  modifiedText.value = data;

  if (modifiedText.value !== text.value) {
    title.value = '* New Note';
    headerOptions.saveDisabled = false;
    unsavedChanges.value = true;
  } else {
    title.value = 'New Note';
    headerOptions.saveDisabled = true;
  }
};

const unsavedAlert = (e: Event) => {
  if (unsavedChanges.value) {
    // Attempt to modify event will trigger Chrome/Firefox alert msg
    e.returnValue = true;
  }
};

onBeforeRouteLeave((_to, _from, next) => {
  if (unsavedChanges.value) {
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
          await saveNote();
          unsavedChanges.value = false;
          next();
        },
      },
    });
  } else {
    next();
  }
});

onMounted(() => {
  window.addEventListener('beforeunload', unsavedAlert);

  text.value = newNote;

  note.value = {
    data: text.value,
    uuid: null,
  };
});

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', unsavedAlert);
});
</script>

<style scoped>
.loading-wrapper {
  width: 100%;
  height: 100vh;
  position: relative;
}
</style>
