<template>
  <b-datepicker
    inline
    v-model="calendar.date"
    indicators="bars"
    @input="changeDate"
  >
  </b-datepicker>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import format from 'date-fns/format';

import CalendarInst from '../services/calendar';

@Component
export default class Calendar extends Vue {
  public calendar = CalendarInst;
  public tracker: any = null;

  mounted() {
    this.calendar.updateDate(this.$route);

    this.tracker = setInterval(() => this.calendar.getActivity(), 60000);
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