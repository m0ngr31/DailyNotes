<template>
  <div>
    <div class="msgs">{{errMsg}}</div>
    <div class="inputs">
      <b-field :type="usernameErr ? 'is-danger' : ''" :message="usernameErr">
        <b-input placeholder="Username" size="is-medium" icon="user" v-model="username" @keyup.enter="signup"></b-input>
      </b-field>
      <b-field :type="passwordErr ? 'is-danger' : ''" :message="passwordErr">
        <b-input placeholder="Password" type="password" password-reveal size="is-medium" icon="key" v-model="password" @keyup.enter="signup"></b-input>
      </b-field>
      <b-field :type="passConfirmErr ? 'is-danger' : ''" :message="passConfirmErr">
        <b-input placeholder="Confirm Password" type="password" password-reveal size="is-medium" icon="key" v-model="passwordConfirm" @keyup.enter="signup"></b-input>
      </b-field>
      <b-button type="is-primary" size="is-medium" expanded class="mt-20" @click="signup" :loading="isLoading">Sign Up</b-button>
      <h1 class="mt-20 alt-button" @click="login">Login</h1>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useHead } from '@unhead/vue';
import { getCurrentInstance, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { Requests } from '../services/requests';
import { setToken } from '../services/user';

useHead({
  title: 'Sign Up',
});

const router = useRouter();
const route = useRoute();
const instance = getCurrentInstance();
const buefy = (instance?.appContext.config.globalProperties as any).$buefy;

const username = ref('');
const usernameErr = ref('');
const password = ref('');
const passwordErr = ref('');
const passwordConfirm = ref('');
const passConfirmErr = ref('');
const errMsg = ref('');
const isLoading = ref(false);
const hideSignup = !!process.env.VUE_APP_PREVENT_SIGNUPS;

onMounted(() => {
  if (hideSignup) {
    router.push({ name: 'Login' });
  }
});

const login = () => {
  router.push({ name: 'Login' });
};

const signup = async () => {
  if (isLoading.value) {
    return;
  }

  usernameErr.value = '';
  passwordErr.value = '';
  passConfirmErr.value = '';
  errMsg.value = '';

  if (!username.value || !username.value.length) {
    usernameErr.value = 'Username must be filled';
    return;
  }

  if (!password.value || !password.value.length) {
    passwordErr.value = 'Password must be filled.';
    return;
  }

  if (password.value !== passwordConfirm.value) {
    passConfirmErr.value = 'Passwords must match.';
    return;
  }

  isLoading.value = true;

  try {
    const res = await Requests.post('/sign-up', {
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

    errMsg.value = 'There was an error creating your account. Please try again.';
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
