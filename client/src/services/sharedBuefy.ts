// Stupid hack to give access to Buefy outside of Vue components
interface BuefyDialog {
  confirm: (options: unknown) => { close: () => void };
}

interface BuefyNotifications {
  open: (options: { duration?: number; message: string; position?: string; type?: string }) => void;
}

export const SharedBuefy = {
  activeDialog: null as { close: () => void } | null,
  dialog: null as BuefyDialog | null,
  notifications: null as BuefyNotifications | null,
  preventDialog: false,
  openConfirmDialog: function (options: unknown = {}) {
    if (this.preventDialog) {
      return;
    }

    if (this.activeDialog) {
      try {
        this.activeDialog.close();
        this.activeDialog = null;
      } catch (_e) {}
    }

    this.activeDialog = this.dialog?.confirm(options) || null;
  },
};
