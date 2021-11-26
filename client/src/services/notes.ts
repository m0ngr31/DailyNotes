import {Requests} from './requests';

import {INote} from '../interfaces';

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
        date
      });

      if (res.data && res.data.day) {
        return res.data.day as INote;
      }

      throw new Error('no matching data');
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

      return res.data.note as INote;
    } catch (e) {
      throw new Error(e);
    }
  },

  createNote: async (noteData: INote): Promise<INote> => {
    const res = await Requests.post('/create_note', noteData);
    return res.data.note;
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

  /**
   * Save an individual date
   * 
   * @param noteData INote object
   */
  saveDay: async (noteData: INote): Promise<INote> => {
    const res = await Requests.put('/save_day', noteData);
    return res.data.note;
  },

  /**
   * Save an individual note
   * 
   * @param noteData INote object
   */
  saveNote: async (noteData: INote): Promise<INote> => {
    const res = await Requests.put('/save_note', noteData);
    return res.data.note;
  },

  /**
   * Delete an individual note
   */
  deleteNote: async (uuid: string): Promise<void> => {
    await Requests.delete(`/delete_note/${uuid}`);
  },

  /**
   * Exports all notes to a zip file and downloads
   */
  exportNotes: async (): Promise<void> => {
    Requests.download("/export", "export.zip");
  }
};
