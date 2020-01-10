import formatISO from 'date-fns/formatISO';
import parse from 'date-fns/parse';

import {Requests} from './requests';

export const NoteService = {
  /**
   * Get the note for the active day.
   *
   * @param date Date in 'MM-dd-yyyy' format
   */
  getDate: async (date: string): Promise<INote> => {
    if (!date) {
      Promise.reject();
    }

    try {
      const res = await Requests.get('/date', {
        date: formatISO(parse(date, 'MM-dd-yyyy', new Date())),
      });

      return res.data as INote;
    } catch (e) {
      throw new Error(e);
    }
  },

  /**
   * Get the selected note.
   *
   * @param uuid
   */
  getNote: async (uuid: string): Promise<INote> => {
    if (!uuid) {
      Promise.reject();
    }

    try {
      const res = await Requests.get('/note', {
        uuid,
      });

      return res.data as INote;
    } catch (e) {
      throw new Error(e);
    }
  },

  /**
   * Get a list of all the notes
   */
  getNotes: async (): Promise<INote[]> => {
    try {
      const res = await Requests.get('/notes');

      return res.data as INote[];
    } catch (e) {
      throw new Error(e);
    }
  },
};

export interface INote {
  uuid?: string;
  data: string;
  title?: string;
  is_date?: boolean;
}
