<template>
  <div class="level full-height">
    <div class="msg level-item has-text-centered">
      <div>
        <b-icon icon="eye-slash" size="is-large" class="huge center-icon" custom-class="huge-icon"></b-icon>
        <h1 class="title text-center">You are unauthorized to view this page. Please go back.</h1>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'unauthorized',
  metaInfo: {
    title: 'Unauthorized',
  },
};
</script>