export interface IHeaderOptions {
  title: string;
  showDateNavs?: boolean;
  showDelete?: boolean;
  hideCreate?: boolean;
  saveDisabled?: boolean;
  saveFn?: () => Promise<any>;
  deleteFn?: () => Promise<any>;
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
