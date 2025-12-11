import { formatISO } from 'date-fns/formatISO';
import { parse } from 'date-fns/parse';
import _ from 'lodash';
import { reactive } from 'vue';
import type { RouteLocationNormalizedLoaded } from 'vue-router';
import type { IExternalEvent, IMeta, INote } from '../interfaces';

import router from '../router';
import { CalendarService } from './calendars';
import { Requests } from './requests';

interface CalendarEvent {
  date: Date;
}

class SidebarSerivce {
  public hide: boolean = false;
  public events: CalendarEvent[] = [];
  public tags: string[] = [];
  public tasks: IMeta[] = [];
  public projects: string[] = [];
  public notes: INote[] = [];
  public calLoading: boolean = false;
  public externalEvents: IExternalEvent[] = [];
  public externalEventsLoading: boolean = false;
  public autoSave: boolean = false;
  public vimMode: boolean = false;
  public kanbanEnabled: boolean = false;
  public kanbanColumns: string[] = ['todo', 'done'];
  public currentNoteId: string | null = null;
  public date: Date | null = null;
  public sidebarLoading: boolean = false;
  public searchLoading: boolean = false;
  public selectedSearch: string = '';
  public searchString: string = '';
  public searchQuery: string = '';
  public filteredNotes: INote[] = [];

  /**
   * Updates the active date on the calendar picker. This is throttled
   * so that it doesn't get overwhelmed.
   *
   * @param $route A VueRouter Route object
   */
  public updateDate = _.throttle(
    ($route: RouteLocationNormalizedLoaded) => {
      if (!$route.params || !$route.params.id) {
        this.date = null;
        return;
      }

      try {
        const id = Array.isArray($route.params.id) ? $route.params.id[0] : $route.params.id;
        this.date = parse(id, 'MM-dd-yyyy', new Date());
        this.getExternalEvents(this.date);
      } catch (_e) {
        // Reset date
        this.date = null;
      }
    },
    250,
    { trailing: true, leading: true }
  );

  /**
   * Get the event indicators for the calendar
   */
  public async getEvents(): Promise<void> {
    if (this.calLoading) {
      return;
    }

    let date = new Date();

    if (this.date) {
      date = this.date;
    }

    this.calLoading = true;

    try {
      const res = await Requests.get('/events', {
        date: formatISO(date),
      });

      if (res?.data?.events) {
        this.events = _.map(res.data.events, (event: string) => {
          return {
            date: parse(event, 'MM-dd-yyyy', new Date()),
          };
        });
      }
    } catch (_e) {}

    this.calLoading = false;
  }

  /**
   * Get external events for the current date.
   */
  public async getExternalEvents(date?: Date | null): Promise<void> {
    const target = date || this.date || new Date();
    this.externalEventsLoading = true;
    try {
      const openDate = target
        ? `${String(target.getMonth() + 1).padStart(2, '0')}-${String(target.getDate()).padStart(2, '0')}-${target.getFullYear()}`
        : '';
      this.externalEvents = openDate ? await CalendarService.eventsForDate(openDate) : [];
    } catch (_e) {
      this.externalEvents = [];
    } finally {
      this.externalEventsLoading = false;
    }
  }

  /**
   * Gets the tags, projects, and notes information loaded into the sidebar.
   *
   * @param showLoad Boolean to show the loading indicator or not
   */
  public async getSidebarInfo(showLoad = false): Promise<void> {
    if (this.sidebarLoading) {
      return;
    }

    if (showLoad) {
      this.sidebarLoading = true;
    }

    try {
      const res = await Requests.get('/sidebar');

      if (res?.data) {
        this.tags = res.data.tags;
        this.tasks = res.data.tasks;
        this.projects = res.data.projects;
        this.notes = res.data.notes;
        this.autoSave = res.data.auto_save;
        this.vimMode = res.data.vim_mode;
        this.kanbanEnabled = res.data.kanban_enabled || false;
        this.kanbanColumns = res.data.kanban_columns || ['todo', 'done'];
      }

      if (this.selectedSearch.length && this.searchString.length) {
        this.searchNotes();
      }
    } catch (_e) {}

    this.sidebarLoading = false;
  }

  public async searchNotes() {
    if (this.searchLoading) {
      return;
    }

    this.searchLoading = true;

    try {
      let res;

      // Use new query-based search if searchQuery is set, otherwise use legacy
      if (this.searchQuery) {
        res = await Requests.post('/search', {
          query: this.searchQuery,
        });
      } else {
        res = await Requests.post('/search', {
          selected: this.selectedSearch,
          search: this.searchString,
        });
      }

      if (res?.data) {
        this.filteredNotes = res.data.notes || [];
      }
    } catch (_e) {}

    this.searchLoading = false;

    // Update URL - use q param for new syntax, legacy params for old
    if (this.searchQuery) {
      router.push({ name: 'search', query: { q: this.searchQuery } }).catch((_err) => {});
    } else {
      router
        .push({ name: 'search', query: { [this.selectedSearch]: this.searchString } })
        .catch((_err) => {});
    }
  }

  public async saveTaskProgress(name: string, uuid: string) {
    try {
      await Requests.put('/save_task', { name, uuid });
      this.getSidebarInfo();
    } catch (_e) {}
  }

  public async toggleAutoSave(autoSave: boolean) {
    try {
      await Requests.post('/toggle_auto_save', { auto_save: autoSave });
      this.getSidebarInfo();
    } catch (_e) {}
  }

  public async toggleVimMode(vimMode: boolean) {
    try {
      await Requests.post('/toggle_vim_mode', { vim_mode: vimMode });
      this.getSidebarInfo();
    } catch (_e) {}
  }

  public async toggleKanban(enabled: boolean) {
    try {
      await Requests.put('/settings', { kanban_enabled: enabled });
      this.kanbanEnabled = enabled;
    } catch (_e) {}
  }

  public async updateKanbanColumns(columns: string[]) {
    try {
      await Requests.put('/settings', { kanban_columns: columns });
      this.kanbanColumns = columns;
    } catch (_e) {}
  }

  public async updateTaskColumn(
    taskUuid: string,
    column: string
  ): Promise<{ note_uuid: string; old_task: string; new_task: string }> {
    const res = await Requests.put('/task_column', { uuid: taskUuid, column });
    this.getSidebarInfo();
    return {
      note_uuid: res.data.note_uuid,
      old_task: res.data.old_task,
      new_task: res.data.new_task,
    };
  }
}

// Make it a singleton and wrap with reactive for Vue 3 reactivity
const SidebarInst = reactive(new SidebarSerivce());

export default SidebarInst;
