import parse from 'date-fns/parse';
import format from 'date-fns/format';
import { Route } from 'vue-router';
import _ from 'lodash';

import {Requests} from './requests';

export class CalendarService {
  date: any = null;
  loading: boolean = false;
  noteLoading: boolean = false;
  activity: any[] = [];

  public updateDate = _.throttle(($route: Route) => {
    if (!$route.params || !$route.params.id) {
      this.date = null;
      return;
    }

    try {
      this.date = parse($route.params.id, 'MM-dd-yyyy', new Date());
      this.getActivity();
    } catch (e) {
      // Reset date
      this.date = null;
    }
  }, 250, {trailing: true, leading: false});

  public async getActivity() {
    if (!this.date) {
      return;
    }

    if (this.loading) {
      return;
    }

    this.loading = true;

    try {
      const res = await Requests.post('/activity', {
        date: format(this.date, 'MM-dd-yyyy'),
      });
    } catch (e) {}

    this.loading = false;
  }

  public async getDate() {
    console.log('eyy lmao');
    if (!this.date) {
      return;
    }
    console.log('eyy lmao 2');

    if (this.noteLoading) {
      return;
    }

    this.noteLoading = true;

    let res = null;

    try {
      res = await Requests.post('/note', {
        date: format(this.date, 'MM-dd-yyyy'),
      });
    } catch (e) {
      throw new Error(e);
    }

    this.noteLoading = false;
    return res;
  }
}

// Make it a singleton
const CalendarInst = new CalendarService();

export default CalendarInst;
