<template>
  <b-datepicker
    inline
    v-model="sidebar.date"
    indicators="bars"
    @input="changeDate"
  >
  </b-datepicker>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import format from 'date-fns/format';

import SidebarInst from '../services/sidebar';

@Component
export default class Calendar extends Vue {
  public sidebar = SidebarInst;
  public tracker: any = null;

  mounted() {
    this.sidebar.updateDate(this.$route);
    this.sidebar.getActivity();
    this.sidebar.getSidebarInfo();

    this.tracker = setInterval(() => this.sidebar.getActivity(), 60000);
  }

  beforeDestroy() {
    if (this.tracker) {
      clearInterval(this.tracker);
    }
  }

  public changeDate(value: any) {
    if (value) {
      this.$router.push({ name: 'day-id', params: { id: format(value, 'MM-dd-yyyy') } });
    }
  }
}
</script>