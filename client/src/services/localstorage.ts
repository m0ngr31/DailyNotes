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
