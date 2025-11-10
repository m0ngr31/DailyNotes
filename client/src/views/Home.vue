<template>
  <div class="columns no-margin is-mobile full-height">
    <div
      class="column sidebar is-6-mobile is-6-tablet is-two-fifths-desktop is-4-widescreen is-3-fullhd"
      v-show="!sidebar.hide"
    >
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
    <div class="column no-padding main-area" @click="focusEditor">
      <router-view :key="$route.path"></router-view>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useHead } from '@unhead/vue';
import { onBeforeUnmount, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import Calendar from '@/components/Calendar.vue';
import Tags from '@/components/Tags.vue';
import eventHub from '../services/eventHub';

import SidebarInst from '../services/sidebar';
import { updateJWT } from '../services/user';

useHead({
  title: 'Home',
});

const MINUTES = 60;
const SECONDS = 60;
const HOUR = MINUTES * SECONDS * 1000; // MS in an hour

const router = useRouter();
const route = useRoute();
const sidebar = SidebarInst;
let auth_timer: ReturnType<typeof setInterval> | null = null;

const today = () => {
  router.push({ name: 'Home Redirect' });
};

const focusEditor = () => {
  eventHub.emit('focusEditor');
};

onMounted(() => {
  // Get new JWT every hour
  auth_timer = setInterval(() => updateJWT(), HOUR);
});

onBeforeUnmount(() => {
  if (auth_timer) {
    clearInterval(auth_timer);
  }
});
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