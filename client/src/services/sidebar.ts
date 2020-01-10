import parse from 'date-fns/parse';
import formatISO from 'date-fns/formatISO';
import { Route } from 'vue-router';
import _ from 'lodash';

import {Requests} from './requests';
import { INote } from './notes';

class SidebarSerivce {
  events: any[] = [];
  tags: string[] = [];
  projects: string[] = [];
  notes: INote[] = [];
  calLoading: boolean = false;
  date: any = null;
  sidebarLoading: boolean = false;

  /**
   * Updates the active date on the calendar picker. This is throttled
   * so that it doesn't get overwhelmed.
   *
   * @param $route A VueRouter Route object
   */
  public updateDate = _.throttle(($route: Route) => {
    if (!$route.params || !$route.params.id) {
      this.date = null;
      return;
    }

    try {
      this.date = parse($route.params.id, 'MM-dd-yyyy', new Date());
    } catch (e) {
      // Reset date
      this.date = null;
    }
  }, 250, {trailing: true, leading: false});

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

      if (res && res.data && res.data.events) {
        this.events = _.map(res.data.events, event => {
          return {
            date: new Date(event),
          };
        });
      }
    } catch (e) {}

    this.calLoading = false;
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
      
      if (res && res.data) {
        this.tags = res.data.tags;
        this.projects = res.data.projects;
        this.notes = res.data.notes;
      }
    } catch (e) {}

    this.calLoading = false;
  }
}

// Make it a singleton
const SidebarInst = new SidebarSerivce();

export default SidebarInst;
