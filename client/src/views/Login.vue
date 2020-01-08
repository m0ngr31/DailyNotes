<template>
  <div>
    <div class="msgs">{{errMsg}}</div>
    <div class="inputs">
      <b-field :type="usernameErr ? 'is-danger' : ''" :message="usernameErr">
        <b-input placeholder="Username" size="is-medium" icon="user" v-model="username"></b-input>
      </b-field>
      <b-field :type="passwordErr ? 'is-danger' : ''" :message="passwordErr">
        <b-input placeholder="Password" type="password" password-reveal size="is-medium" icon="key" v-model="password"></b-input>
      </b-field>
      <b-button type="is-primary" size="is-medium" expanded class="mt-20" @click="login" :loading="isLoading">Login</b-button>
      <h1 class="mt-20 alt-button" @click="signup">Sign Up</h1>
    </div>
  </div>
</template>

<script lang="ts">
import Vue from 'vue';
import Component from 'vue-class-component';

import {Requests} from '../services/requests';
import {setToken} from '../services/user';


@Component({
  metaInfo: {
    title: 'Login'
  }
})
export default class Login extends Vue {
  public username: string = '';
  public usernameErr: string = '';

  public password: string = '';
  public passwordErr: string = '';

  public errMsg: string = '';

  public isLoading: boolean = false;

  public signup() {
    this.$router.push({name: 'Sign Up'});
  }

  public async login() {
    if (this.isLoading) {
      return;
    }

    this.usernameErr = '';
    this.passwordErr = '';
    this.errMsg = '';

    if (!this.username || !this.username.length) {
      this.usernameErr = 'Username must be filled';
      return;
    }

    if (!this.password || !this.password.length) {
      this.passwordErr = 'Password must be filled.';
      return;
    }

    this.isLoading = true;

    try {
      const res = await Requests.post('/login', {username: this.username, password: this.password});
      if (res.data && res.data.access_token) {
        setToken(res.data.access_token);
        this.$router.push({name: 'day'});
      } else {
        throw Error('Data isn\'t right');
      }
    } catch (e) {
      console.log(e);
      this.errMsg = 'There was an error logging in. Please try again.'
    }

    this.isLoading = false;
  }
}
</script>