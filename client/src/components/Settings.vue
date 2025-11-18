<template>
  <div class="modal-card settings-modal">
    <header class="modal-card-head">
      <p class="modal-card-title">Settings</p>
      <button class="delete" @click="close" aria-label="close" />
    </header>

    <section class="modal-card-body">
      <div class="settings-content">
        <div class="settings-grid">
          <div class="settings-card">
            <p class="section-title">General</p>
            <p class="section-hint">Quick preferences for editing and saving.</p>
            <div class="setting-row">
              <b-switch v-model="localAutoSave" @update:modelValue="onAutoSaveChange">
                Enable Auto-Save
              </b-switch>
            </div>
          </div>

          <div class="settings-card">
            <p class="section-title">Calendar sharing</p>
            <p class="section-hint">Expose daily notes as all-day events via a private ICS link.</p>
            <div class="setting-row">
              <b-switch v-model="calendarEnabled" :disabled="calendarLoading" @update:modelValue="onCalendarToggle">
                Enable calendar share URL
              </b-switch>
              <p class="setting-hint">
                Anyone with the link can see your daily note titles in their calendar. Regenerate to revoke old links.
              </p>
            </div>

            <div class="calendar-share__controls" v-if="calendarEnabled">
              <div class="share-label">
                <span>Share URL</span>
                <span v-if="calendarLoading" class="pill">Refreshing…</span>
                <span v-else class="pill pill-success">Active</span>
              </div>
              <b-input
                v-model="calendarUrl"
                readonly
                expanded
                icon="link"
                @focus="$event.target.select()"
              />
              <div class="calendar-share__actions">
                <b-button size="is-small" @click="copyUrl" :disabled="!calendarUrl">Copy</b-button>
                <b-button size="is-small" :loading="calendarLoading" @click="regenerateUrl">
                  Regenerate
                </b-button>
              </div>
            </div>
          </div>
        </div>

        <div class="settings-card">
          <p class="section-title">Editor</p>
          <p class="section-hint">Choose keyboard behaviors.</p>
          <div class="setting-row">
            <b-switch v-model="localVimMode" @update:modelValue="onVimModeChange">
              Enable Vim keybindings
            </b-switch>
          </div>
        </div>
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
import { Requests } from '../services/requests';

const emit = defineEmits<{
  close: [];
}>();

const instance = getCurrentInstance();
const buefy = (instance?.appContext.config.globalProperties as { $buefy?: BuefyInstance }).$buefy;

const localAutoSave = ref(false);
const localVimMode = ref(false);
const calendarEnabled = ref(false);
const calendarUrl = ref('');
const calendarLoading = ref(false);

onMounted(() => {
  // Initialize with current values from sidebar
  localAutoSave.value = sidebar.autoSave;
  localVimMode.value = sidebar.vimMode;

  fetchCalendarUrl();
});

const onAutoSaveChange = (value: boolean) => {
  // Update the setting immediately
  sidebar.toggleAutoSave(value);

  // Show success toast
  buefy?.toast.open({
    message: `Auto-save ${value ? 'enabled' : 'disabled'}`,
    type: 'is-success',
    duration: 2000,
  });
};

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

const fetchCalendarUrl = async () => {
  calendarLoading.value = true;
  try {
    const res = await Requests.get('/calendar_token');
    const token = res?.data?.token;
    calendarEnabled.value = !!token;
    calendarUrl.value = res?.data?.ics_url || '';
  } catch (_e) {
    calendarEnabled.value = false;
    calendarUrl.value = '';
  } finally {
    calendarLoading.value = false;
  }
};

const onCalendarToggle = async (value: boolean) => {
  calendarLoading.value = true;
  try {
    if (value) {
      const res = await Requests.post('/calendar_token', {});
      calendarUrl.value = res?.data?.ics_url || '';
    } else {
      await Requests.delete('/calendar_token');
      calendarUrl.value = '';
    }
    calendarEnabled.value = value && !!calendarUrl.value;
  } catch (_e) {
    calendarEnabled.value = !value;
    buefy?.toast.open({
      message: 'Unable to update calendar sharing right now.',
      type: 'is-danger',
      duration: 3000,
    });
  } finally {
    calendarLoading.value = false;
  }
};

const regenerateUrl = async () => {
  calendarLoading.value = true;
  try {
    const res = await Requests.post('/calendar_token', {});
    calendarUrl.value = res?.data?.ics_url || '';
    calendarEnabled.value = !!calendarUrl.value;
    buefy?.toast.open({
      message: 'Calendar share link regenerated.',
      type: 'is-success',
      duration: 2000,
    });
  } catch (_e) {
    buefy?.toast.open({
      message: 'Unable to regenerate link right now.',
      type: 'is-danger',
      duration: 3000,
    });
  } finally {
    calendarLoading.value = false;
  }
};

const copyUrl = () => {
  if (!calendarUrl.value) return;
  try {
    navigator.clipboard.writeText(calendarUrl.value);
    buefy?.toast.open({
      message: 'Copied share URL to clipboard.',
      type: 'is-success',
      duration: 1500,
    });
  } catch (_e) {
    buefy?.toast.open({
      message: 'Unable to copy URL. You can copy it manually.',
      type: 'is-warning',
      duration: 3000,
    });
  }
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

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.settings-card {
  background: #1f2733;
  border: 1px solid #304254;
  border-radius: 10px;
  padding: 16px;
}

.section-title {
  color: #82aaff;
  font-weight: 600;
  margin: 0 0 4px;
}

.section-hint {
  color: #9fb3c8;
  margin: 0 0 12px;
  font-size: 14px;
}

.setting-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.setting-hint {
  color: #9fb3c8;
  font-size: 13px;
  margin: 0;
}

.calendar-share__controls {
  background: #141b23;
  border: 1px solid #304254;
  border-radius: 8px;
  padding: 12px;
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.calendar-share__actions {
  display: flex;
  gap: 8px;
}

.share-label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #c8d5e0;
  font-weight: 600;
}

.pill {
  background: #2f3f52;
  color: #c8d5e0;
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 12px;
}

.pill-success {
  background: #1a3b2f;
  color: #7fddb7;
}

/* Delete button styling */
.delete {
  background-color: rgba(255, 255, 255, 0.1);
}

.delete:hover {
  background-color: rgba(255, 255, 255, 0.2);
}
</style>
