import mitt from 'mitt';
import type { SSEEventData } from './sse';

type Events = {
  taskUpdated: { note_id: string; task: string; completed: boolean };
  taskColumnUpdated: { note_id: string; old_task: string; new_task: string };
  focusEditor: undefined;
  // SSE events for real-time sync
  sseNoteUpdated: SSEEventData;
  sseTaskUpdated: SSEEventData;
  sseTaskColumnUpdated: SSEEventData;
};

const eventHub = mitt<Events>();

export default eventHub;
