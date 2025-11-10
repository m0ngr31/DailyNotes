<template>
  <div class="level full-height">
    <div class="msg level-item has-text-centered">
      <div>
        <b-icon icon="dumpster-fire" size="is-large" class="huge center-icon" custom-class="huge-icon"></b-icon>
        <h1 class="title text-center">There was an error. Please go back and try again.</h1>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'error',
  metaInfo: {
    title: 'Error',
  },
};
</script>
