<template>
  <b-datepicker
    inline
    v-model="date"
    indicators="bars"
    @input="changeDate"
  >
  </b-datepicker>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import parse from 'date-fns/parse';
import format from 'date-fns/format';

@Component
export default class Calendar extends Vue {
  public date: any = null;

  mounted() {
    if (this.$route.params && this.$route.params.id) {
      try {
        this.date = parse(this.$route.params.id, 'MM-dd-yyyy', new Date());
      } catch (e) {
        // Reset date
        this.date = null;
      }
    }
  }

  public changeDate(value: any) {
    if (value) {
      this.$router.push({ name: 'day-id', params: { id: format(value, 'MM-dd-yyyy') } });
    }
  }
}
</script>