<template>
  <div class="home-layout">
    <!-- Mobile sidebar overlay -->
    <div
      class="sidebar-overlay"
      v-show="!sidebar.hide && isMobile"
      @click="closeSidebar"
    ></div>

    <div
      class="sidebar"
      :class="{ 'sidebar-visible': !sidebar.hide, 'sidebar-mobile': isMobile }"
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
    <div class="main-area" @click="handleMainAreaClick">
      <router-view :key="$route.path"></router-view>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useHead } from '@unhead/vue';
import { onBeforeUnmount, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

import Calendar from '@/components/Calendar.vue';
import Tags from '@/components/Tags.vue';
import eventHub from '../services/eventHub';

import SidebarInst from '../services/sidebar';
import { sseService } from '../services/sse';
import { updateJWT } from '../services/user';

useHead({
  title: 'Home',
});

const MINUTES = 60;
const SECONDS = 60;
const HOUR = MINUTES * SECONDS * 1000; // MS in an hour
const MOBILE_BREAKPOINT = 768;

const router = useRouter();
const sidebar = SidebarInst;
let auth_timer: ReturnType<typeof setInterval> | null = null;
const isMobile = ref(false);

const checkMobile = () => {
  isMobile.value = window.innerWidth < MOBILE_BREAKPOINT;
  // Auto-hide sidebar on mobile
  if (isMobile.value && !sidebar.hide) {
    sidebar.hide = true;
  }
};

const today = () => {
  router.push({ name: 'Home Redirect' });
  // Close sidebar on mobile after navigation
  if (isMobile.value) {
    sidebar.hide = true;
  }
};

const closeSidebar = () => {
  sidebar.hide = true;
};

const handleMainAreaClick = () => {
  eventHub.emit('focusEditor');
  // Close sidebar on mobile when clicking main area
  if (isMobile.value && !sidebar.hide) {
    sidebar.hide = true;
  }
};

onMounted(() => {
  // Get new JWT every hour
  auth_timer = setInterval(() => updateJWT(), HOUR);

  // Check initial mobile state
  checkMobile();
  window.addEventListener('resize', checkMobile);

  // Connect to SSE for real-time updates
  sseService.connect();
});

onBeforeUnmount(() => {
  if (auth_timer) {
    clearInterval(auth_timer);
  }
  window.removeEventListener('resize', checkMobile);

  // Disconnect SSE
  sseService.disconnect();
});
</script>

<style scoped>
.home-layout {
  display: flex;
  height: 100vh;
  width: 100%;
  overflow: hidden;
}

.center-columns {
  margin-left: auto;
  margin-right: auto;
}

.sidebar {
  width: 320px;
  min-width: 320px;
  max-width: 320px;
  overflow-y: auto;
  overflow-x: hidden;
  background-color: var(--main-bg-darker);
  height: 100%;
  transition: transform 0.3s ease, opacity 0.3s ease;
  flex-shrink: 0;
}

/* When sidebar is hidden on desktop */
.sidebar:not(.sidebar-visible) {
  display: none;
}

/* Mobile sidebar - slides in from left */
.sidebar.sidebar-mobile {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 100;
  transform: translateX(-100%);
  display: block;
  width: min(320px, 85vw);
  min-width: min(320px, 85vw);
  max-width: min(320px, 85vw);
}

.sidebar.sidebar-mobile.sidebar-visible {
  transform: translateX(0);
}

/* Overlay for mobile sidebar */
.sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 99;
}

.main-area {
  flex: 1;
  background-color: var(--main-bg-color);
  overflow-y: auto;
  overflow-x: hidden;
  height: 100%;
  min-width: 0; /* Prevents flex item from overflowing */
}

/* Wider sidebar on large screens */
@media screen and (min-width: 1408px) {
  .sidebar {
    width: 360px;
    min-width: 360px;
    max-width: 360px;
  }
}
</style>
