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
  background-color: var(--main-bg-color);
  font-family: 'Montserrat', sans-serif;
  transition: background-color 0.2s ease;
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

/* ========================================
   Theme CSS Variables
   ======================================== */

/* Dark Theme (default) */
:root, .theme-dark {
  /* Background colors */
  --main-bg-color: #263238;
  --main-bg-darker: #212b30;
  --main-bg-lighter: #2e3d44;
  --sidebar-bg: #212b30;
  --card-bg: #2e3d44;
  --input-bg: #1e272e;
  --modal-bg: #263238;
  --dropdown-bg: #212b30;

  /* Text colors */
  --text-primary: #EEFFFF;
  --text-secondary: #ddd;
  --text-muted: #aaa;
  --text-disabled: #666;
  --text-link: #82AAFF;
  --text-link-hover: #a8c7ff;

  /* Border colors */
  --border-color: #364850;
  --border-color-light: #4a5f6a;
  --border-color-focus: #4a90a4;

  /* Accent colors */
  --accent-primary: #4a90a4;
  --accent-secondary: #78c4d4;
  --accent-success: #C3E88D;
  --accent-warning: #FFCB6B;
  --accent-error: #FF5370;
  --accent-info: #82AAFF;

  /* Bulma overrides */
  --bulma-arrow-color: #4a5f6a;

  /* Editor colors */
  --editor-bg: #263238;
  --editor-gutter-bg: #263238;
  --editor-gutter-text: #546E7A;
  --editor-selection: #545454;
  --editor-cursor: #80CBC4;
  --editor-line-highlight: rgba(0, 0, 0, 0.15);

  /* Syntax highlighting */
  --syntax-keyword: #C792EA;
  --syntax-string: #C3E88D;
  --syntax-number: #F78C6C;
  --syntax-comment: #546E7A;
  --syntax-function: #82AAFF;
  --syntax-variable: #EEFFFF;
  --syntax-operator: #89DDFF;
  --syntax-tag: #f07178;
  --syntax-attribute: #FFCB6B;
  --syntax-heading: #aaa;
  --syntax-link: #82AAFF;
  --syntax-meta: #FFCB6B;

  /* Code blocks */
  --code-bg: #1e272e;
  --code-text: #EEFFFF;

  /* Scrollbar */
  --scrollbar-track: #1e272e;
  --scrollbar-thumb: #4a5f6a;
  --scrollbar-thumb-hover: #5a7080;

  /* Tags & badges */
  --tag-bg: #364850;
  --tag-text: #ddd;
  --tag-hover-bg: #4a5f6a;

  /* Calendar */
  --calendar-today-bg: #4a90a4;
  --calendar-selected-bg: #4a90a4;
  --calendar-event-dot: #4a90a4;
  --calendar-hover-bg: rgba(255, 255, 255, 0.05);

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.3);
}

/* Light Theme */
.theme-light {
  /* Background colors */
  --main-bg-color: #f5f7fa;
  --main-bg-darker: #e8ecf0;
  --main-bg-lighter: #ffffff;
  --sidebar-bg: #e8ecf0;
  --card-bg: #ffffff;
  --input-bg: #ffffff;
  --modal-bg: #ffffff;
  --dropdown-bg: #ffffff;

  /* Text colors */
  --text-primary: #2c3e50;
  --text-secondary: #4a5568;
  --text-muted: #718096;
  --text-disabled: #a0aec0;
  --text-link: #3182ce;
  --text-link-hover: #2c5282;

  /* Border colors */
  --border-color: #e2e8f0;
  --border-color-light: #cbd5e0;
  --border-color-focus: #4a90a4;

  /* Accent colors */
  --accent-primary: #4a90a4;
  --accent-secondary: #5fa8bc;
  --accent-success: #48bb78;
  --accent-warning: #ed8936;
  --accent-error: #f56565;
  --accent-info: #4299e1;

  /* Bulma overrides */
  --bulma-arrow-color: #718096;

  /* Editor colors */
  --editor-bg: #ffffff;
  --editor-gutter-bg: #f5f7fa;
  --editor-gutter-text: #a0aec0;
  --editor-selection: #b4d5fe;
  --editor-cursor: #4a90a4;
  --editor-line-highlight: rgba(0, 0, 0, 0.04);

  /* Syntax highlighting (light theme) */
  --syntax-keyword: #8959a8;
  --syntax-string: #718c00;
  --syntax-number: #f5871f;
  --syntax-comment: #8e908c;
  --syntax-function: #4271ae;
  --syntax-variable: #4d4d4c;
  --syntax-operator: #3e999f;
  --syntax-tag: #c82829;
  --syntax-attribute: #eab700;
  --syntax-heading: #4d4d4c;
  --syntax-link: #4271ae;
  --syntax-meta: #f5871f;

  /* Code blocks */
  --code-bg: #f5f7fa;
  --code-text: #2c3e50;

  /* Scrollbar */
  --scrollbar-track: #f5f7fa;
  --scrollbar-thumb: #cbd5e0;
  --scrollbar-thumb-hover: #a0aec0;

  /* Tags & badges */
  --tag-bg: #e2e8f0;
  --tag-text: #4a5568;
  --tag-hover-bg: #cbd5e0;

  /* Calendar */
  --calendar-today-bg: #4a90a4;
  --calendar-selected-bg: #4a90a4;
  --calendar-event-dot: #4a90a4;
  --calendar-hover-bg: rgba(0, 0, 0, 0.05);

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.1);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
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
  color: var(--text-secondary);
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
  color: var(--text-secondary) !important;
  margin-top: 15px;
}

.msg {
  color: var(--text-secondary) !important;
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
  color: var(--text-secondary);
}

.CodeMirror-vscrollbar {
  overflow-y: auto;
}

/* Datepicker theme */
.datepicker {
  background-color: var(--dropdown-bg);
}

.datepicker .dropdown-content {
  background-color: var(--dropdown-bg);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  box-shadow: var(--shadow-md);
  padding-top: 0;
}

.datepicker-header {
  background-color: var(--dropdown-bg) !important;
}

.datepicker-header select,
.datepicker-header .select select {
  background-color: var(--input-bg);
  color: var(--text-secondary);
  border-color: var(--border-color);
}

.datepicker-header select:hover,
.datepicker-header .select select:hover {
  border-color: var(--border-color-light);
}

.datepicker-header .pagination-previous,
.datepicker-header .pagination-next {
  color: var(--text-secondary);
  background-color: transparent;
}

.datepicker-header .pagination-previous:hover,
.datepicker-header .pagination-next:hover {
  background-color: var(--calendar-hover-bg);
}

.datepicker-table {
  background-color: var(--dropdown-bg);
}

.datepicker-table .datepicker-header {
  color: var(--text-primary);
}

.datepicker-table .datepicker-body .datepicker-cell {
  color: var(--text-primary) !important;
  border: none;
  font-weight: 500;
}

.datepicker-table .datepicker-body .datepicker-cell.is-unselectable {
  color: var(--text-muted) !important;
}

.datepicker-table .datepicker-body .datepicker-cell.is-nearby {
  color: var(--text-disabled) !important;
}

.datepicker-table .datepicker-body .datepicker-cell span {
  color: inherit !important;
}

.datepicker-table .datepicker-body .datepicker-cell:not(.is-selected):hover {
  background-color: var(--calendar-hover-bg);
  color: var(--text-primary);
}

.datepicker-table .datepicker-body .datepicker-cell.is-today {
  background-color: var(--calendar-today-bg);
  color: #fff;
}

.datepicker-table .datepicker-body .datepicker-cell.is-selected {
  background-color: var(--calendar-selected-bg);
  color: #fff;
}

.datepicker-table .datepicker-body .datepicker-cell.has-event {
  position: relative;
}

.datepicker-table .datepicker-body .datepicker-cell.has-event .events .event {
  background-color: var(--calendar-event-dot);
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
