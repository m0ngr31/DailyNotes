<template>
  <router-view></router-view>
</template>

<script setup lang="ts">
import { useHead } from '@unhead/vue';
import { getCurrentInstance, onMounted, provide, ref } from 'vue';
import type { ITask } from './interfaces';
import { type BuefyInstance, SharedBuefy } from './services/sharedBuefy';

useHead({
  titleTemplate: '%s | DailyNotes',
});

const taskList = ref<ITask[]>([]);

provide('global', {
  taskList,
});

onMounted(() => {
  const instance = getCurrentInstance();
  if (instance) {
    const buefy = (instance.appContext.config.globalProperties as { $buefy?: BuefyInstance })
      .$buefy;
    if (buefy) {
      SharedBuefy.notifications = buefy.toast;
      SharedBuefy.dialog = buefy.dialog;
    }
  }
});
</script>

<style lang="scss">
// Import Bulma CSS (compiled version to avoid SASS module conflicts)
@import '~bulma/css/bulma.css';

html, body {
  background-color: #263238;
  font-family: 'Montserrat', sans-serif;
}

code, pre {
  font-family: 'Fira Code', monospace;
}
</style>

<style lang="scss">
/* Import Buefy compiled CSS */
@import '~buefy/dist/css/buefy.css';

/* Import FontAwesome icons */
@import '~@fortawesome/fontawesome-free/css/all.css';

:root {
  --main-bg-color: #263238;
  --main-bg-darker: #212b30;
  --bulma-arrow-color: #4a5f6a;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity .5s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}

.pagination-previous, .pagination-next {
  border: 0;
}

.is-inline > .dropdown-menu {
  width: 100%;
}

html, body {
  font-family: 'Montserrat', sans-serif;
  overflow-x: hidden;
  overflow-y: hidden;
  -webkit-overflow-scrolling: touch; /* Smooth scrolling on iOS */
}

/* Mobile viewport fixes */
@media screen and (max-width: 767px) {
  html, body {
    /* Allow scrolling within containers on mobile */
    position: fixed;
    width: 100%;
    height: 100%;
  }
}

*:focus {
  outline:none;
  border: transparent;
}

.light-white {
  color: #ddd;
}

.full-height {
  height: 100%;
}

.center-icon {
  width: 100% !important;
}

.huge.icon.is-large {
  height: auto;
}

.fas.huge-icon, .fas.huge-icon::before {
  font-size: 2.5em !important;
}

.text-center {
  text-align: center;
}

.title {
  color: #ddd !important;
  margin-top: 15px;
}

.msg {
  color: #ddd !important;
  margin-top: auto;
  margin-bottom: auto;
}

.inputs {
  width: 90%;
  margin: 20px auto;
}

.mt-20 {
  margin-top: 20px;
}

.alt-button {
  cursor: pointer;
}

.msgs {
  color: #eea170;
}

.light-white > .loading-wrapper > .loading-overlay .loading-background {
  background-color: var(--main-bg-darker);
}

.header-loading {
  position: relative;
  height: 2em;
  width: 2em;
}

.header-loading > .loading-overlay .loading-icon::after {
  width: 1em !important;
  height: 1em !important;
  top: calc(50% - .5em) !important;
  left: calc(50% - .5em) !important;
}

.notification.is-dark {
  background-color: var(--main-bg-color);
  color: #ddd;
}

.CodeMirror-vscrollbar {
  overflow-y: auto;
}

/* Datepicker dark theme */
.datepicker {
  background-color: var(--main-bg-darker);
}

.datepicker .dropdown-content {
  background-color: var(--main-bg-darker);
  border: none;
  border-radius: 0;
  box-shadow: none;
  padding-top: 0;
}

.datepicker-header {
  background-color: var(--main-bg-darker) !important;
}

.datepicker-header select,
.datepicker-header .select select {
  background-color: var(--main-bg-darker);
  color: #ddd;
  border-color: #364850;
}

.datepicker-header select:hover,
.datepicker-header .select select:hover {
  border-color: #4a5f6a;
}

.datepicker-header .pagination-previous,
.datepicker-header .pagination-next {
  color: #ddd;
  background-color: transparent;
}

.datepicker-header .pagination-previous:hover,
.datepicker-header .pagination-next:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.datepicker-table {
  background-color: var(--main-bg-darker);
}

.datepicker-table .datepicker-header {
  color: #fff;
}

.datepicker-table .datepicker-body .datepicker-cell {
  color: #fff !important;
  border: none;
  font-weight: 500;
}

.datepicker-table .datepicker-body .datepicker-cell.is-unselectable {
  color: #aaa !important;
}

.datepicker-table .datepicker-body .datepicker-cell.is-nearby {
  color: #666 !important;
}

.datepicker-table .datepicker-body .datepicker-cell span {
  color: inherit !important;
}

.datepicker-table .datepicker-body .datepicker-cell:not(.is-selected):hover {
  background-color: rgba(255, 255, 255, 0.05);
  color: #fff;
}

.datepicker-table .datepicker-body .datepicker-cell.is-today {
  background-color: #4a90a4;
  color: #fff;
}

.datepicker-table .datepicker-body .datepicker-cell.is-selected {
  background-color: #4a90a4;
  color: #fff;
}

.datepicker-table .datepicker-body .datepicker-cell.has-event {
  position: relative;
}

.datepicker-table .datepicker-body .datepicker-cell.has-event .events .event {
  background-color: #4a90a4;
}

/* Make datepicker fit in sidebar */
.datepicker {
  width: 100%;
  max-width: 100%;
}

.datepicker .dropdown-content {
  width: 100%;
  max-width: 100%;
}

.datepicker-table {
  width: 100%;
}

.datepicker-header {
  padding: 0 8px;
}

/* Mobile datepicker adjustments */
@media screen and (max-width: 767px) {
  .datepicker-table .datepicker-body .datepicker-cell {
    padding: 0.3rem 0.5rem;
    font-size: 0.85rem;
  }

  .datepicker-header .pagination-previous,
  .datepicker-header .pagination-next {
    min-width: 2rem;
  }

  .datepicker-header select,
  .datepicker-header .select select {
    font-size: 0.85rem;
  }
}
</style>
