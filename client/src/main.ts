import Buefy from 'buefy';
import Vue from 'vue';
import VueMasonry from 'vue-masonry-css';
import VueMeta from 'vue-meta';

import App from './App.vue';
import router from './router';

Vue.config.productionTip = false;

Vue.use(Buefy, {
  defaultIconPack: 'fas',
});
Vue.use(VueMeta);
Vue.use(VueMasonry);

new Vue({
  router,
  render: (h) => h(App),
}).$mount('#app');
