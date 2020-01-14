<template>
  <div>
    <div class="msgs">{{errMsg}}</div>
    <div class="inputs">
      <b-field :type="usernameErr ? 'is-danger' : ''" :message="usernameErr">
        <b-input placeholder="Username" size="is-medium" icon="user" v-model="username" @keyup.native.enter="signup"></b-input>
      </b-field>
      <b-field :type="passwordErr ? 'is-danger' : ''" :message="passwordErr">
        <b-input placeholder="Password" type="password" password-reveal size="is-medium" icon="key" v-model="password" @keyup.native.enter="signup"></b-input>
      </b-field>
      <b-field :type="passConfirmErr ? 'is-danger' : ''" :message="passConfirmErr">
        <b-input placeholder="Confirm Password" type="password" password-reveal size="is-medium" icon="key" v-model="passwordConfirm" @keyup.native.enter="signup"></b-input>
      </b-field>
      <b-button type="is-primary" size="is-medium" expanded class="mt-20" @click="signup" :loading="isLoading">Sign Up</b-button>
      <h1 class="mt-20 alt-button" @click="login">Login</h1>
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
    title: 'Sign Up'
  }
})
export default class Signup extends Vue {
  public username: string = '';
  public usernameErr: string = '';

  public password: string = '';
  public passwordErr: string = '';

  public passwordConfirm: string = '';
  public passConfirmErr: string = '';

  public errMsg: string = '';

  public isLoading: boolean = false;

  public login() {
    this.$router.push({name: 'Login'});
  }

  public async signup() {
    if (this.isLoading) {
      return;
    }

    this.usernameErr = '';
    this.passwordErr = '';
    this.passConfirmErr = '';
    this.errMsg = '';

    if (!this.username || !this.username.length) {
      this.usernameErr = 'Username must be filled';
      return;
    }

    if (!this.password || !this.password.length) {
      this.passwordErr = 'Password must be filled.';
      return;
    }

    if (this.password !== this.passwordConfirm) {
      this.passConfirmErr = 'Passwords must match.';
      return;
    }

    this.isLoading = true;

    try {
      const res = await Requests.post('/sign-up', {username: this.username, password: this.password});
      if (res.data && res.data.access_token) {
        setToken(res.data.access_token);

        if (this.$route.query && this.$route.query.from) {
          this.$router.push({path: (this.$route.query as any).from});
        } else {
          this.$router.push({name: 'Home Redirect'});
        }
      } else {
        throw Error('Data isn\'t right');
      }
    } catch (e) {
      console.log(e);

      this.errMsg = 'There was an error creating your account. Please try again.';
      this.$buefy.toast.open({
        duration: 5000,
        message: this.errMsg,
        position: 'is-top',
        type: 'is-danger'
      });
    }

    this.isLoading = false;
  }
}
</script>