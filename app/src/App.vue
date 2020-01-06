<template>
  <router-view></router-view>
</template>

<script>
  export default {
    name: 'App',
    metaInfo: {
      titleTemplate: '%s | DailyNotes'
    }
  }
</script>

<style lang="sass">
@import '~bulmaswatch/minty/_variables';
@import '~bulma/bulma';
@import '~bulmaswatch/minty/_overrides';

$app-background: #263238

$datepicker-background-color: darken($app-background, 2.5%)
$datepicker-shadow: none
$datepicker-item-color: #fff

@import "~buefy/src/scss/buefy";

html, body
  background-color: $datepicker-background-color
</style>

<style>
@import '~@fortawesome/fontawesome-free/css/all.css';

.fade-enter-active, .fade-leave-active {
  transition: opacity .5s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}

.pagination-previous, .pagination-next {
  border: 0;
}

.is-inline > .dropdown-menu {
  width: 100%;
}

html, body {
  height: 100%;
  overflow-y: hidden;
  font-family: 'Fira Code', monospace;
  font-family: 'Montserrat', sans-serif;
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
</style>
