<template>
  <div class="modal-card settings-modal">
    <header class="modal-card-head">
      <p class="modal-card-title">Settings</p>
      <button class="delete" @click="close" aria-label="close" />
    </header>

    <section class="modal-card-body">
      <div class="settings-content">
        <b-field label="Editor">
          <b-field>
            <b-switch v-model="localVimMode" @update:modelValue="onVimModeChange">
              Enable Vim keybindings
            </b-switch>
          </b-field>
        </b-field>
      </div>
    </section>

    <footer class="modal-card-foot">
      <b-button @click="close">Close</b-button>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { getCurrentInstance, onMounted, ref } from 'vue';
import type { BuefyInstance } from '../services/sharedBuefy';
import sidebar from '../services/sidebar';

const emit = defineEmits<{
  close: [];
}>();

const instance = getCurrentInstance();
const buefy = (instance?.appContext.config.globalProperties as { $buefy?: BuefyInstance }).$buefy;

const localVimMode = ref(false);

onMounted(() => {
  // Initialize with current value from sidebar
  localVimMode.value = sidebar.vimMode;
});

const onVimModeChange = (value: boolean) => {
  // Update the setting immediately
  sidebar.toggleVimMode(value);

  // Show success toast
  buefy?.toast.open({
    message: `Vim mode ${value ? 'enabled' : 'disabled'}`,
    type: 'is-success',
    duration: 2000,
  });
};

const close = () => {
  emit('close');
};
</script>

<style scoped>
.settings-modal {
  width: 500px;
}

.modal-card-head {
  background-color: var(--main-bg-color);
  border-bottom: 1px solid #404854;
}

.modal-card-title {
  color: #eeffff;
  font-weight: 600;
}

.modal-card-body {
  background-color: #263238;
  color: #eeffff;
  min-height: 200px;
}

.settings-content {
  padding: 20px 0;
}

.modal-card-foot {
  background-color: var(--main-bg-color);
  border-top: 1px solid #404854;
  justify-content: flex-end;
}

/* Override Buefy field label color */
.settings-content :deep(.label) {
  color: #82aaff;
  font-weight: 600;
  margin-bottom: 12px;
}

.settings-content :deep(.field:not(:last-child)) {
  margin-bottom: 24px;
}

.settings-content :deep(.switch) {
  margin-top: 8px;
}

/* Delete button styling */
.delete {
  background-color: rgba(255, 255, 255, 0.1);
}

.delete:hover {
  background-color: rgba(255, 255, 255, 0.2);
}
</style>
