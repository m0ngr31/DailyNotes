import Vue from "vue";
import VueRouter from "vue-router";

import Home from "../views/Home.vue";

import PageNotFound from '../views/PageNotFound.vue';
import UnauthorizedPage from '../views/UnauthorizedPage.vue';
import ErrorPage from '../views/ErrorPage.vue';

import Day from '../views/Day.vue';
import Note from '../views/Note.vue';
import NewNote from '../views/NewNote.vue';
import Search from '../views/Search.vue';
import HomeRedirect from '../views/HomeRedirect.vue';

import Auth from '../views/Auth.vue';
import Login from '../views/Login.vue';
import Signup from '../views/Signup.vue';

import {getToken} from '../services/user';


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
        name: 'Home Redirect',
        component: HomeRedirect
      },
      {
        path: 'date/:id',
        name: 'day-id',
        component: Day
      },
      {
        path: 'note/:uuid',
        name: 'note-id',
        component: Note
      },
      {
        path: 'new-note',
        name: 'new-note',
        component: NewNote
      },
      {
        path: 'search',
        name: 'search',
        component: Search
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
  mode: 'history',
  linkActiveClass: 'active',
  base: process.env.BASE_URL,
  routes
});

router.beforeEach(async (to, from, next) => {
  const currentUser = getToken();
  const requiresAuth = to.matched.some(record => record.meta.auth);

  if (requiresAuth && !currentUser) {
    await next({name: 'Login', query: {from: to.path}});
  } else if (!requiresAuth && currentUser) {
    await next({name: 'Home Redirect'});
  } else {
    await next();
  }
});

export default router;
