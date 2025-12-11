import type { Ref } from 'vue';

export interface IHeaderOptions {
  title: string;
  showDateNavs?: boolean;
  showDelete?: boolean;
  hideCreate?: boolean;
  saveDisabled?: boolean;
  saveFn?: () => Promise<void>;
  deleteFn?: () => Promise<void>;
  showPreview?: boolean;
  previewMode?: 'none' | 'side' | 'replace';
  togglePreviewFn?: (mode: 'side' | 'replace' | 'none') => void;
}

export interface INote {
  uuid?: string | null;
  data: string;
  title?: string;
  is_date?: boolean;
  tags?: string;
  projects?: string;
  snippet?: string;
  highlights?: string[];
}

export interface IMeta {
  uuid: string;
  name: string;
  note_id: string;
  kind?: string;
  task_column?: string;
}

export interface ITask {
  completed: boolean;
  name: string;
  index: number;
}

export interface IGlobal {
  taskList: Ref<ITask[]>;
}

export interface IExternalCalendar {
  uuid: string;
  name: string;
  url: string;
  color?: string | null;
}

export interface IExternalEvent {
  title: string;
  all_day: boolean;
  start: string;
  end: string;
  source: string;
  color?: string | null;
  location?: string | null;
  url?: string | null;
}
