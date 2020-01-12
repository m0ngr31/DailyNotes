// Stupid hack to give access to Buefy outside of Vue components
export const SharedBuefy = {
  activeDialog: null,
  dialog: null,
  notifications: null,
  preventDialog: false,
  openConfirmDialog: function(options: any = {}) {
    if (this.preventDialog) {
      return;
    }

    if (this.activeDialog) {
      try {
        (this.activeDialog as any).close();
        this.activeDialog = null;
      } catch (e) {}
    }

    this.activeDialog = (this.dialog as any).confirm(options);
  }
};
