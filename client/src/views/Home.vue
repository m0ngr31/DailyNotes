<template>
  <div class="columns no-margin full-height">
    <div
      class="column is-12-mobile is-6-tablet is-two-fifths-desktop is-4-widescreen is-3-fullhd sidebar"
      :class="{
        show: !sidebar.hide,
        hide: sidebar.hide,
        active: sidebar.active
      }"
    >
      <div
        class="light-white is-block-mobile is-hidden-tablet"
        style="float:right"
      >
        <div @click="closeSidebar()">
          <b-icon icon="times" class="alt-button"></b-icon>
        </div>
      </div>
      <div class="columns light-white center-columns text-center">
        <div class="column">
          <b-tooltip label="Go to Today" position="is-bottom">
            <div @click="today()">
              <b-icon
                icon="book-open"
                size="is-medium"
                style="margin-top: .8em"
                class="alt-button"
              >
              </b-icon>
            </div>
          </b-tooltip>
        </div>
      </div>
      <Calendar />
      <Tags />
    </div>
    <div
      class="column no-padding main-area full-height"
      @click="focusEditor"
      :class="{
        'is-offset-0-mobile': !sidebar.hide,
        'is-offset-6-tablet': !sidebar.hide,
        'is-offset-two-fifths-desktop': !sidebar.hide,
        'is-offset-4-widescreen': !sidebar.hide,
        'is-offset-3-fullhd': !sidebar.hide
      }"
    >
      <router-view :key="$route.path"></router-view>
    </div>
  </div>
</template>

<script lang="ts">
import Vue from "vue";
import Component from "vue-class-component";

import Calendar from "@/components/Calendar.vue";
import Tags from "@/components/Tags.vue";

import { updateJWT } from "../services/user";

import SidebarInst from "../services/sidebar";
import eventHub from "../services/eventHub";

const MINUTES = 60;
const SECONDS = 60;
const HOUR = MINUTES * SECONDS * 1000; // MS in an hour

@Component({
  components: {
    Calendar,
    Tags
  },
  metaInfo: {
    title: "Home"
  }
})
export default class Admin extends Vue {
  public auth_timer: any = null;
  public sidebar = SidebarInst;

  mounted() {
    // Get new JWT every hour
    this.auth_timer = setInterval(() => updateJWT(), HOUR);
  }

  today() {
    this.$router.push({ name: "Home Redirect" });
  }

  beforeDestroy() {
    if (this.auth_timer) {
      clearInterval(this.auth_timer);
    }
  }

  focusEditor() {
    eventHub.$emit("focusEditor");
    this.sidebar.deactivate();
  }

  closeSidebar() {
    this.sidebar.deactivate();
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
  z-index: 5;
  position: absolute;
  background-color: var(--main-bg-darker);
  transition: all 0.4s;

  overflow-y: auto;
  overflow-x: hidden;
}

@media screen and (max-width: 768px) {
  .sidebar {
    transform: translate3d(-100%, 0, 0);
    opacity: 0;
  }
  .sidebar.active {
    transform: translate3d(0, 0, 0);
    opacity: 1;
  }
}

@media screen and (min-width: 769px) {
  .sidebar.show {
    opacity: 1;
  }
  .sidebar.hide {
    transform: translate3d(-100%, 0, 0);
    opacity: 0;
  }
}

.full-height {
  height: 100vh;
}

.main-area {
  background-color: var(--main-bg-color);
  transition: all 0.4s;
  overflow-y: auto;
  overflow-x: hidden;
}
</style>
