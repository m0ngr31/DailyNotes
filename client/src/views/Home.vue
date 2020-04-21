<template>
  <div class="columns no-margin is-mobile full-height">
    <div class="column sidebar is-6-mobile is-6-tablet is-two-fifths-desktop is-4-widescreen is-3-fullhd" v-show="!sidebar.hide">
      <div class="columns light-white center-columns text-center">
        <div class="column">
          <b-icon
            icon="book-open"
            size="is-medium"
            style="margin-top: .8em"
          >
          </b-icon>
        </div>
      </div>
      <Calendar />
      <Tags />
    </div>
    <div class="column no-padding main-area" @click="focusEditor">
      <router-view :key="$route.path"></router-view>
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';

import Calendar from "@/components/Calendar.vue";
import Tags from "@/components/Tags.vue";

import {updateJWT} from '../services/user';

import SidebarInst from '../services/sidebar';
import eventHub from '../services/eventHub';

const MINUTES = 60;
const SECONDS = 60;
const HOUR = MINUTES * SECONDS * 1000; // MS in an hour

@Component({
  components: {
    Calendar,
    Tags,
  },
  metaInfo: {
    title: 'Home',
  }
})
export default class Admin extends Vue {
  public auth_timer: any = null;
  public sidebar = SidebarInst;

  mounted() {
    // Get new JWT every hour
    this.auth_timer = setInterval(() => updateJWT(), HOUR);
  }

  beforeDestroy() {
    if (this.auth_timer) {
      clearInterval(this.auth_timer);
    }
  }

  focusEditor() {
    eventHub.$emit('focusEditor');
  }
}
</script>

<style scoped>
.no-margin {
  margin: 0px;
}

.no-padding {
  padding: 0px;
}

.center-columns {
  margin-left: auto;
  margin-right: auto;
}

.sidebar {
  overflow-y: auto;
  overflow-x: hidden;
}

.full-height {
  height: 100vh;
}

.main-area {
  background-color: var(--main-bg-color);
  overflow-y: auto;
  overflow-x: hidden;
}
</style>