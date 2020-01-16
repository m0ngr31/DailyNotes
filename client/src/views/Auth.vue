<template>
  <div class="level full-height">
    <div class="msg level-item has-text-centered">
      <div>
        <b-icon icon="book-open" size="is-large" class="huge center-icon" custom-class="huge-icon logo"></b-icon>
        <div class="wrapper">
          <div class="fa-3x mb-40">DailyNotes</div>
          <router-view></router-view>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  export default {
    name: 'Auth',
    metaInfo: {
      title: ''
    }
  }
</script>

<style>
.logo {
  background-color: var(--main-bg-darker);
  z-index: 2;
  padding-left: 5px;
  padding-right: 5px;
}
</style>

<style scoped>
.full-height {
  height: 100vh;
}

.wrapper {
  min-height: 100px;
  border-color: white;
  border-width: 1px;
  padding-top: 55px;
  border-style: solid;
  margin-top: -35px;
  border-radius: 5px;
  width: 400px;
  margin-right: auto;
  margin-left: auto;
}

.mb-40 {
  margin-bottom: 40px;
}
</style>
