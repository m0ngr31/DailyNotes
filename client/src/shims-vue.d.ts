declare module '*.vue' {
  import type { DefineComponent } from 'vue';
  // biome-ignore lint/suspicious/noExplicitAny: Vue shim requires any for component definition
  const component: DefineComponent<{}, {}, any>;
  export default component;
}
