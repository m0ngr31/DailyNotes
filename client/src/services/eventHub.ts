import mitt from 'mitt';

type Events = {
  taskUpdated: { note_id: string; task: string; completed: boolean };
  focusEditor: undefined;
};

const eventHub = mitt<Events>();

export default eventHub;
