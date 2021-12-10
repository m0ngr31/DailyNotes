<template>
  <transition>
    <div v-if="isActive" class="dialog modal is-active">
      <div class="modal-background" @click="cancel('outside')" />
      <div class="modal-card animation-content">
        <header class="modal-card-head">
          <p class="modal-card-title">Unsaved Content</p>
        </header>

        <section class="modal-card-body is-flex">
          <div class="media">
            <div class="media-left">
              <b-icon
                icon="alert"
                type="is-warning"
                :both="true"
                size="is-large"
              />
            </div>
            <div class="media-content">
              <p>
                <template>
                  <div>
                    You have unsaved changes changes. What would you like to do?
                  </div>
                </template>
              </p>
            </div>
          </div>
        </section>

        <footer class="modal-card-foot">
          <b-button ref="cancelButton" @click="cancel('button')"
            >Cancel</b-button
          >
          <b-button type="is-warning" ref="discardButton" @click="discard"
            >Discard</b-button
          >
          <b-button
            type="is-primary"
            ref="saveButton"
            class="is-focused"
            @click="save"
            >Save &amp; Continue</b-button
          >
        </footer>
      </div>
    </div>
  </transition>
</template>

<script lang="ts">
import Vue from "vue";
import Component from "vue-class-component";

@Component
export default class UnsavedForm extends Vue {
  public isActive: boolean = false;

  mounted() {
    this.isActive = true;
    if (typeof window !== "undefined") {
      document.addEventListener("keyup", this.keyPress);
    }
  }

  beforeDestroy() {
    if (typeof window !== "undefined") {
      document.removeEventListener("keyup", this.keyPress);
    }
  }

  keyPress({ key }: any) {
    if (key == "Enter") {
      this.save();
    }
  }

  cancel() {
    this.$emit("cancel");
    this.$emit("close");
  }

  discard() {
    this.$emit("close");
    this.$emit("discard");
  }

  save() {
    this.$emit("close");
    this.$emit("save");
  }
}
</script>
