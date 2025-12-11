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
}

export interface IMeta {
  uuid: string;
  name: string;
  note_id: string;
}

export interface ITask {
  completed: boolean;
  name: string;
  index: number;
}

export interface IGlobal {
  taskList: ITask[];
}
