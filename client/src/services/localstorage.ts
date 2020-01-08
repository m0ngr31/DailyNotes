export function getItemOrDefault(key: string, _default: any = null) {
  if (!typeof(Storage)) {
    return _default;
  }

  const value = localStorage.getItem(key);

  if (!value){
    return _default;
  }

  return JSON.parse(value);
}

export function setItem(key: string, data: any) {
  if (!typeof(Storage)) {
    return;
  }

  localStorage.setItem(key, JSON.stringify(data));
}
