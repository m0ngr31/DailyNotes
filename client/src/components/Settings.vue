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
            <b-switch v-model="localVimMode" @input="onVimModeChange">
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

<script lang="ts">
import { Vue, Component } from 'vue-property-decorator';
import sidebar from '../services/sidebar';

@Component
export default class Settings extends Vue {
  public localVimMode: boolean = false;

  mounted() {
    // Initialize with current value from sidebar
    this.localVimMode = sidebar.vimMode;
  }

  public onVimModeChange(value: boolean) {
    // Update the setting immediately
    sidebar.toggleVimMode(value);

    // Show success toast
    this.$buefy.toast.open({
      message: `Vim mode ${value ? 'enabled' : 'disabled'}`,
      type: 'is-success',
      duration: 2000
    });
  }

  public close() {
    this.$emit('close');
  }
}
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
.settings-content >>> .label {
  color: #82aaff;
  font-weight: 600;
  margin-bottom: 12px;
}

.settings-content >>> .field:not(:last-child) {
  margin-bottom: 24px;
}

.settings-content >>> .switch {
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
