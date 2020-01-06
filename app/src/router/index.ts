import Vue from "vue";
import VueRouter from "vue-router";
import Meta from 'vue-meta';

import Home from "../views/Home.vue";

import PageNotFound from '../views/PageNotFound.vue';
import UnauthorizedPage from '../views/UnauthorizedPage.vue';
import ErrorPage from '../views/ErrorPage.vue';

import Day from '../views/Day.vue';

Vue.use(VueRouter);

const routes = [
  {
    path: "/",
    component: Home,
    meta: { auth: true },
    children: [
      {
        path: '',
        name: 'day',
        component: Day
      },
      {
        path: ':id',
        name: 'day-id',
        component: Day
      }
    ]
  },
  // {
  //   path: '/auth',
  //   component: Auth,
  //   meta: { auth: false },
  //   children: [
  //     {
  //       path: '',
  //       alias: 'login',
  //       name: 'Login',
  //       component: Login
  //     },
  //     {
  //       path: 'create-account',
  //       name: 'Create Account',
  //       component: CreateAccount
  //     }
  //   ]
  // },
  {
    path: '/page-not-found',
    name: '404',
    component: PageNotFound
  },
  {
    path: '/not-authorized',
    name: '401',
    component: UnauthorizedPage
  },
  {
    path: '/error',
    name: 'Error',
    component: ErrorPage
  },
  {
    path: '*',
    redirect: '/page-not-found'
  }
  // {
  //   path: "/about",
  //   name: "about",
  //   // route level code-splitting
  //   // this generates a separate chunk (about.[hash].js) for this route
  //   // which is lazy-loaded when the route is visited.
  //   // component: () =>
  //   //   import(/* webpackChunkName: "about" */ "../views/About.vue")
  //   component: About
  // }

];

const router = new VueRouter({
  mode: "history",
  linkActiveClass: 'active',
  base: process.env.BASE_URL,
  routes
});

export default router;
