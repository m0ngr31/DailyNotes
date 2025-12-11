<template>
  <transition>
    <div v-if="isActive" class="dialog modal is-active">
      <div class="modal-background" @click="cancel('outside')" />
      <div class="modal-card animation-content">
        <header class="modal-card-head">
          <p class="modal-card-title">Unsaved Content</p>
        </header>

        <section class="modal-card-body">
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
              <p>You have unsaved changes. What would you like to do?</p>
            </div>
          </div>
        </section>

        <footer class="modal-card-foot" style="justify-content: flex-end;">
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

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue';

const emit = defineEmits<{
  cancel: [];
  close: [];
  discard: [];
  save: [];
}>();

const isActive = ref(false);

const keyPress = ({ key }: { key: string }) => {
  if (key === 'Enter') {
    save();
  }
};

onMounted(() => {
  isActive.value = true;
  if (typeof window !== 'undefined') {
    document.addEventListener('keyup', keyPress);
  }
});

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    document.removeEventListener('keyup', keyPress);
  }
});

const cancel = () => {
  emit('cancel');
  emit('close');
};

const discard = () => {
  emit('discard');
  emit('close');
};

const save = () => {
  emit('save');
  emit('close');
};
</script>
