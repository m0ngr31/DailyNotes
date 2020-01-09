<template>
  <div></div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import format from 'date-fns/format';


@Component({
  metaInfo: {
    title: 'Home'
  }
})
export default class HomeRedirect extends Vue {
  // Automatically go to today
  mounted() {
    this.$router.push({ name: 'day-id', params: { id: format(new Date(), 'MM-dd-yyyy') } });
  }
}
</script>