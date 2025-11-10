import { createHead } from '@unhead/vue/client';
import Buefy from 'buefy';
import { createApp } from 'vue';

import App from './App.vue';
import router from './router';

const app = createApp(App);
const head = createHead();

app.use(router);
app.use(head);

// Buefy 3.x for Vue 3 - ensure components are properly registered
app.use(Buefy, {
  defaultIconPack: 'fas',
  defaultContainerElement: '#app',
});

app.mount('#app');
