<template>
  <div>
    <div class="msgs">{{errMsg}}</div>
    <div class="inputs">
      <b-field :type="usernameErr ? 'is-danger' : ''" :message="usernameErr">
        <b-input placeholder="Username" size="is-medium" icon="user" v-model="username" @keyup.enter="login"></b-input>
      </b-field>
      <b-field :type="passwordErr ? 'is-danger' : ''" :message="passwordErr">
        <b-input placeholder="Password" type="password" password-reveal size="is-medium" icon="key" v-model="password" @keyup.enter="login"></b-input>
      </b-field>
      <b-button type="is-primary" size="is-medium" expanded class="mt-20" @click="login" :loading="isLoading">Login</b-button>
      <h1 class="mt-20 alt-button" @click="signup" v-if="!hideSignup">Sign Up</h1>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useHead } from '@unhead/vue';
import { getCurrentInstance, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Requests } from '../services/requests';
import { setToken } from '../services/user';

useHead({
  title: 'Login',
});

const router = useRouter();
const route = useRoute();
const instance = getCurrentInstance();
const buefy = (instance?.appContext.config.globalProperties as any).$buefy;

const username = ref('');
const usernameErr = ref('');
const password = ref('');
const passwordErr = ref('');
const errMsg = ref('');
const isLoading = ref(false);
const hideSignup = !!process.env.VUE_APP_PREVENT_SIGNUPS;

const signup = () => {
  router.push({ name: 'Sign Up' });
};

const login = async () => {
  if (isLoading.value) {
    return;
  }

  usernameErr.value = '';
  passwordErr.value = '';
  errMsg.value = '';

  if (!username.value || !username.value.length) {
    usernameErr.value = 'Username must be filled';
    return;
  }

  if (!password.value || !password.value.length) {
    passwordErr.value = 'Password must be filled.';
    return;
  }

  isLoading.value = true;

  try {
    const res = await Requests.post('/login', {
      username: username.value,
      password: password.value,
    });
    if (res.data?.access_token) {
      setToken(res.data.access_token);

      if (route.query?.from) {
        router.push({ path: String(route.query.from) });
      } else {
        router.push({ name: 'Home Redirect' });
      }
    } else {
      throw Error("Data isn't right");
    }
  } catch (e) {
    console.log(e);

    errMsg.value = 'There was an error logging in. Please try again.';
    buefy?.toast.open({
      duration: 5000,
      message: errMsg.value,
      position: 'is-top',
      type: 'is-danger',
    });
  }

  isLoading.value = false;
};
</script>
