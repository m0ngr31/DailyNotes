import Vue from "vue";
import VueRouter from "vue-router";
import Meta from 'vue-meta';

import Home from "../views/Home.vue";

import PageNotFound from '../views/PageNotFound.vue';
import UnauthorizedPage from '../views/UnauthorizedPage.vue';
import ErrorPage from '../views/ErrorPage.vue';

import Day from '../views/Day.vue';

import Auth from '../views/Auth.vue';
import Login from '../views/Login.vue';
import Signup from '../views/Signup.vue';


Vue.use(VueRouter);

const routes = [
  {
    path: '/auth',
    component: Auth,
    meta: { auth: false },
    children: [
      {
        path: '',
        alias: 'login',
        name: 'Login',
        component: Login
      },
      {
        path: 'sign-up',
        name: 'Sign Up',
        component: Signup
      }
    ]
  },
  {
    path: '/',
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

];

const router = new VueRouter({
  mode: "history",
  linkActiveClass: 'active',
  base: process.env.BASE_URL,
  routes
});

export default router;
