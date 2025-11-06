import Vue from "vue";
import VueRouter from "vue-router";

import {getToken} from '../services/user';
import SidebarInst from '../services/sidebar';

// Lazy-load route components for better code splitting
const Home = () => import(/* webpackChunkName: "home" */ "../views/Home.vue");
const PageNotFound = () => import(/* webpackChunkName: "errors" */ '../views/PageNotFound.vue');
const UnauthorizedPage = () => import(/* webpackChunkName: "errors" */ '../views/UnauthorizedPage.vue');
const ErrorPage = () => import(/* webpackChunkName: "errors" */ '../views/ErrorPage.vue');

const Day = () => import(/* webpackChunkName: "editor" */ '../views/Day.vue');
const Note = () => import(/* webpackChunkName: "editor" */ '../views/Note.vue');
const NewNote = () => import(/* webpackChunkName: "editor" */ '../views/NewNote.vue');
const Search = () => import(/* webpackChunkName: "search" */ '../views/Search.vue');
const HomeRedirect = () => import(/* webpackChunkName: "home" */ '../views/HomeRedirect.vue');

const Auth = () => import(/* webpackChunkName: "auth" */ '../views/Auth.vue');
const Login = () => import(/* webpackChunkName: "auth" */ '../views/Login.vue');
const Signup = () => import(/* webpackChunkName: "auth" */ '../views/Signup.vue');


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
    if (requiresAuth && to.name !== 'day-id') {
      SidebarInst.date = null;
    }
    
    if (requiresAuth && to.name !== 'search') {
      SidebarInst.searchString = '';
      SidebarInst.selectedSearch = '';
    }

    await next();
  }
});

export default router;
