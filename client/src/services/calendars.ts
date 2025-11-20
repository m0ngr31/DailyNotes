import type { IExternalCalendar, IExternalEvent } from '../interfaces';
import { Requests } from './requests';

export const CalendarService = {
  async list(): Promise<IExternalCalendar[]> {
    const res = await Requests.get('/external_calendars');
    return (res.data?.calendars || []) as IExternalCalendar[];
  },

  async add(payload: {
    name: string;
    url: string;
    color?: string | null;
  }): Promise<IExternalCalendar> {
    const res = await Requests.post('/external_calendars', payload);
    return res.data?.calendar as IExternalCalendar;
  },

  async remove(uuid: string): Promise<void> {
    await Requests.delete(`/external_calendars/${uuid}`);
  },

  async eventsForDate(date: string): Promise<IExternalEvent[]> {
    const res = await Requests.get('/external_events', { date });
    return (res.data?.events || []) as IExternalEvent[];
  },
};
