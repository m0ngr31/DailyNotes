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
            <p class="section-title">Appearance</p>
            <p class="section-hint">Choose your preferred theme.</p>
            <div class="theme-selector">
              <button
                v-for="option in themeOptions"
                :key="option.value"
                class="theme-option"
                :class="{ active: localTheme === option.value }"
                @click="localTheme = option.value as ThemePreference; onThemeChange(option.value as ThemePreference)"
              >
                <i :class="option.icon"></i>
                <span>{{ option.label }}</span>
              </button>
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
          <p class="section-title">Connected calendars</p>
          <p class="section-hint">Pull in events from other ICS feeds and show them on your daily page.</p>

          <div class="connected-form">
            <b-field label="Calendar name">
              <b-input v-model="newCal.name" placeholder="Work, Personal, etc." />
            </b-field>
            <b-field label="ICS URL">
              <b-input v-model="newCal.url" placeholder="https://example.com/calendar.ics" />
            </b-field>
            <b-field label="Color (optional)">
              <b-input type="color" v-model="newCal.color" />
            </b-field>
            <div class="connected-actions">
              <b-button size="is-small" :loading="calListLoading" @click="addCalendar">Add calendar</b-button>
            </div>
          </div>

          <div class="connected-list">
            <div v-if="calListLoading" class="connected-empty">Loading calendars…</div>
            <div v-else-if="!externalCalendars.length" class="connected-empty">No external calendars yet.</div>
            <div v-else>
              <div v-for="cal in externalCalendars" :key="cal.uuid" class="connected-item">
                <div class="connected-item__dot" :style="{ backgroundColor: cal.color || '#8ab4f8' }"></div>
                <div class="connected-item__body">
                  <div class="connected-item__title">
                    <span>{{ cal.name }}</span>
                    <small>{{ cal.url }}</small>
                  </div>
                </div>
                <b-button size="is-small" type="is-text" @click="removeCalendar(cal.uuid)">Remove</b-button>
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

        <div class="settings-card about-card">
          <p class="section-title">About</p>
          <div class="about-info">
            <span class="about-label">Version</span>
            <span class="about-value">{{ appVersion }}</span>
          </div>
          <div class="about-links">
            <a href="https://github.com/djedi/DailyNotes" target="_blank" rel="noopener">GitHub</a>
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
import { getCurrentInstance, onMounted, ref, computed } from 'vue';
import type { IExternalCalendar } from '../interfaces';
import { CalendarService } from '../services/calendars';
import { Requests } from '../services/requests';
import type { BuefyInstance } from '../services/sharedBuefy';
import sidebar from '../services/sidebar';
import themeService, { type ThemePreference } from '../services/theme';

const emit = defineEmits<{
  close: [];
}>();

const instance = getCurrentInstance();
const buefy = (instance?.appContext.config.globalProperties as { $buefy?: BuefyInstance }).$buefy;

const localAutoSave = ref(false);
const localVimMode = ref(false);
const localTheme = ref<ThemePreference>('system');

const themeOptions = [
  { value: 'light', label: 'Light', icon: 'fas fa-sun' },
  { value: 'dark', label: 'Dark', icon: 'fas fa-moon' },
  { value: 'system', label: 'System', icon: 'fas fa-laptop' },
];
const calendarEnabled = ref(false);
const calendarUrl = ref('');
const calendarLoading = ref(false);
const calListLoading = ref(false);
const externalCalendars = ref<IExternalCalendar[]>([]);
const newCal = ref<{ name: string; url: string; color: string | null }>({
  name: '',
  url: '',
  color: '#8ab4f8',
});

onMounted(() => {
  // Initialize with current values from sidebar
  localAutoSave.value = sidebar.autoSave;
  localVimMode.value = sidebar.vimMode;
  localTheme.value = themeService.preference;

  fetchCalendarUrl();
  fetchExternalCalendars();
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

const onThemeChange = (value: ThemePreference) => {
  themeService.preference = value;

  const labels: Record<ThemePreference, string> = {
    light: 'Light theme',
    dark: 'Dark theme',
    system: 'System theme (auto)',
  };

  buefy?.toast.open({
    message: `${labels[value]} activated`,
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

const fetchExternalCalendars = async () => {
  calListLoading.value = true;
  try {
    externalCalendars.value = await CalendarService.list();
  } catch (_e) {
    externalCalendars.value = [];
  } finally {
    calListLoading.value = false;
  }
};

const addCalendar = async () => {
  if (!newCal.value.name || !newCal.value.url) {
    buefy?.toast.open({
      message: 'Name and URL are required.',
      type: 'is-danger',
      duration: 2500,
    });
    return;
  }

  calListLoading.value = true;
  try {
    const created = await CalendarService.add({
      name: newCal.value.name,
      url: newCal.value.url,
      color: newCal.value.color,
    });
    externalCalendars.value = [...externalCalendars.value, created];
    buefy?.toast.open({
      message: 'Calendar added.',
      type: 'is-success',
      duration: 2000,
    });
    newCal.value = { name: '', url: '', color: '#8ab4f8' };
  } catch (e: unknown) {
    const error = e as { response?: { data?: { error?: string } } };
    buefy?.toast.open({
      message: error?.response?.data?.error || 'Unable to add calendar.',
      type: 'is-danger',
      duration: 3000,
    });
  } finally {
    calListLoading.value = false;
  }
};

const removeCalendar = async (uuid: string) => {
  calListLoading.value = true;
  try {
    await CalendarService.remove(uuid);
    externalCalendars.value = externalCalendars.value.filter((c) => c.uuid !== uuid);
    buefy?.toast.open({
      message: 'Calendar removed.',
      type: 'is-success',
      duration: 1500,
    });
  } catch (_e) {
    buefy?.toast.open({
      message: 'Unable to remove calendar.',
      type: 'is-danger',
      duration: 2500,
    });
  } finally {
    calListLoading.value = false;
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

const appVersion = process.env.VUE_APP_VERSION || 'dev';

const close = () => {
  emit('close');
};
</script>

<style scoped>
.settings-modal {
  width: 820px;
}

.modal-card-head {
  background-color: var(--main-bg-color);
  border-bottom: 1px solid var(--border-color);
}

.modal-card-title {
  color: var(--text-primary);
  font-weight: 600;
}

.modal-card-body {
  background-color: var(--main-bg-color);
  color: var(--text-primary);
  min-height: 200px;
}

.settings-content {
  padding: 20px 0;
}

.modal-card-foot {
  background-color: var(--main-bg-color);
  border-top: 1px solid var(--border-color);
  justify-content: flex-end;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 16px;
}

.settings-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 16px;
}

:deep(.input),
:deep(.textarea) {
  background-color: var(--input-bg) !important;
  border-color: var(--border-color) !important;
  color: var(--text-primary) !important;
}

:deep(.input:focus),
:deep(.textarea:focus) {
  border-color: var(--text-link) !important;
  box-shadow: 0 0 0 0.2rem rgba(130, 170, 255, 0.15);
}

:deep(.label) {
  color: var(--text-muted) !important;
}

.section-title {
  color: var(--text-link);
  font-weight: 600;
  margin: 0 0 4px;
}

.section-hint {
  color: var(--text-muted);
  margin: 0 0 12px;
  font-size: 14px;
}

.setting-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.setting-hint {
  color: var(--text-muted);
  font-size: 13px;
  margin: 0;
}

/* Theme selector */
.theme-selector {
  display: flex;
  gap: 8px;
}

.theme-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 12px;
  border: 2px solid var(--border-color);
  border-radius: 8px;
  background: var(--input-bg);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
}

.theme-option:hover {
  border-color: var(--border-color-light);
  background: var(--main-bg-lighter);
}

.theme-option.active {
  border-color: var(--accent-primary);
  background: var(--main-bg-lighter);
  color: var(--text-primary);
}

.theme-option i {
  font-size: 1.5em;
}

.theme-option span {
  font-size: 0.9em;
  font-weight: 500;
}

.calendar-share__controls {
  background: var(--input-bg);
  border: 1px solid var(--border-color);
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
  color: var(--text-secondary);
  font-weight: 600;
}

.pill {
  background: var(--tag-bg);
  color: var(--text-secondary);
  border-radius: 999px;
  padding: 2px 10px;
  font-size: 12px;
}

.pill-success {
  background: #1a3b2f;
  color: #7fddb7;
}

.connected-form {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 10px;
  margin-bottom: 12px;
}

.connected-actions {
  display: flex;
  justify-content: flex-start;
}

.connected-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.connected-item {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--input-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 8px 10px;
}

.connected-item__dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.connected-item__body {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.connected-item__title {
  display: flex;
  flex-direction: column;
  gap: 2px;
  color: var(--text-secondary);
}

.connected-item__title small {
  color: var(--text-muted);
  word-break: break-all;
}

.connected-empty {
  color: var(--text-muted);
  font-size: 14px;
}

/* Delete button styling */
.delete {
  background-color: rgba(255, 255, 255, 0.1);
}

.delete:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

/* About section */
.about-card {
  margin-top: 16px;
}

.about-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.about-label {
  color: var(--text-muted);
}

.about-value {
  color: var(--text-primary);
  font-family: 'Fira Code', monospace;
}

.about-links {
  margin-top: 8px;
}

.about-links a {
  color: var(--text-link);
  text-decoration: none;
}

.about-links a:hover {
  text-decoration: underline;
}
</style>
