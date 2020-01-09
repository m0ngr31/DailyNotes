<template>
  <div class="full-height">
    <editor v-if="$route.params.id" v-bind:value="text" v-on:valChanged="valChanged"></editor>
    <div class="level full-height" v-else-if="!$route.params.id">
      <div class="msg level-item has-text-centered">
        <div>
          <b-icon icon="hand-point-left" size="is-large" class="huge center-icon"></b-icon>
          <p class="text-center">Please select a date or tag from the left to get started.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';
import _ from 'lodash';

import CalendarInst from '../services/calendar';

import Editor from '@/components/Editor.vue';

Component.registerHooks([
  'metaInfo'
]);

@Component({
  components: {
    'editor': Editor,
  }
})
export default class Day extends Vue {
  public calendar = CalendarInst;
  public text: string = '';
  public title: string = 'Day';

  public metaInfo(): any {
    return {
      title: this.title
    };
  };

  async mounted() {
    this.calendar.updateDate(this.$route);
    this.text = `---\ndate: ${this.$route.params.id}\n---\n\n`;

    try {
      const res = await this.calendar.getDate();
      // console.log(res);
    } catch (e) {
      console.log(e);
    }
  }

  public valChanged(data: string) {
    if (data !== this.text) {
      this.title = '* Day';
    } else {
      this.title = 'Day';
    }
  }
}
</script>