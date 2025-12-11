export function getItemOrDefault<T = unknown>(key: string, _default: T | null = null): T | null {
  if (typeof Storage === 'undefined') {
    return _default;
  }

  const value = localStorage.getItem(key);

  if (!value) {
    return _default;
  }

  return JSON.parse(value) as T;
}

export function setItem(key: string, data: unknown) {
  if (typeof Storage === 'undefined') {
    return;
  }

  localStorage.setItem(key, JSON.stringify(data));
}

export interface FoldRange {
  from: number;
  to: number;
}

const FOLD_STATE_PREFIX = 'dn-folds-';

export function saveFoldState(noteId: string, folds: FoldRange[]) {
  if (!noteId) return;
  setItem(`${FOLD_STATE_PREFIX}${noteId}`, folds);
}

export function getFoldState(noteId: string): FoldRange[] {
  if (!noteId) return [];
  return getItemOrDefault<FoldRange[]>(`${FOLD_STATE_PREFIX}${noteId}`, []) || [];
}

export function clearFoldState(noteId: string) {
  if (!noteId || typeof Storage === 'undefined') return;
  localStorage.removeItem(`${FOLD_STATE_PREFIX}${noteId}`);
}
