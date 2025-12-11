<template>
  <div class="modal-card kanban-modal">
    <header class="modal-card-head">
      <p class="modal-card-title">Tasks</p>
      <button class="delete" @click="close" aria-label="close" />
    </header>

    <section class="modal-card-body">
      <div class="kanban-board" v-if="filteredTasks.length > 0">
        <div
          v-for="column in effectiveColumns"
          :key="column"
          class="kanban-column"
          @dragover.prevent
          @dragenter.prevent="onDragEnter(column, $event)"
          @dragleave="onDragLeave(column, $event)"
          @drop="onDrop(column, $event)"
          :class="{ 'drag-over': dragOverColumn === column }"
        >
          <div class="column-header">
            <span class="column-title">{{ column }}</span>
            <span class="column-count">{{ getColumnTasks(column).length }}</span>
          </div>
          <div class="column-tasks">
            <div
              v-for="task in getColumnTasks(column)"
              :key="task.uuid"
              class="kanban-task"
              draggable="true"
              @dragstart="onDragStart(task, $event)"
              @dragend="onDragEnd"
              :class="{ 'is-completed': task.completed, 'is-dragging': draggingTask?.uuid === task.uuid }"
            >
              <div class="task-checkbox">
                <b-checkbox
                  v-model="task.completed"
                  @update:modelValue="toggleTaskCompletion(task)"
                  size="is-small"
                />
              </div>
              <div class="task-content">
                <span class="task-text">{{ task.displayText }}</span>
                <span class="task-note" v-if="!props.noteId && task.noteTitle">{{ task.noteTitle }}</span>
              </div>
            </div>
            <div v-if="getColumnTasks(column).length === 0" class="empty-column">
              No tasks
            </div>
          </div>
        </div>
      </div>
      <div v-else class="no-tasks">
        <p>No tasks found.</p>
        <p class="hint">Add tasks using <code>- [ ] Task text</code> in your notes.</p>
        <p class="hint">Assign columns with <code>- [ ] Task text &gt;&gt;column</code></p>
      </div>
    </section>

    <footer class="modal-card-foot">
      <b-button @click="close">Close</b-button>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, getCurrentInstance, ref } from 'vue';
import type { IMeta } from '../interfaces';
import eventHub from '../services/eventHub';
import type { BuefyInstance } from '../services/sharedBuefy';
import sidebar from '../services/sidebar';
import { markNoteUpdatedLocally } from '../services/sse';

interface Props {
  noteId?: string; // Optional: filter to show only tasks from this note
  columns?: string[]; // Optional: override columns (e.g., from frontmatter)
}

const props = withDefaults(defineProps<Props>(), {
  noteId: undefined,
  columns: undefined,
});

const emit = defineEmits<{
  close: [];
}>();

const instance = getCurrentInstance();
const buefy = (instance?.appContext.config.globalProperties as { $buefy?: BuefyInstance }).$buefy;

// Drag state
const draggingTask = ref<KanbanTask | null>(null);
const dragOverColumn = ref<string | null>(null);

interface KanbanTask {
  uuid: string;
  name: string;
  note_id: string;
  task_column?: string;
  completed: boolean;
  displayText: string;
  noteTitle?: string;
}

// Parse task to extract completion status and display text
const parseTask = (meta: IMeta): KanbanTask => {
  const name = meta.name;
  // Task name format: "- [ ] Task text" or "- [x] Task text" or with >>column
  const match = name.match(/^- \[([x ])\] (.+?)(?:\s*>>([a-zA-Z0-9-]+))?\s*$/);

  let completed = false;
  let displayText = name;
  const explicitColumn = meta.task_column;

  if (match) {
    completed = match[1] === 'x';
    displayText = match[2].trim();
  }

  // Determine effective column
  let effectiveColumn = explicitColumn;
  if (!effectiveColumn) {
    effectiveColumn = completed ? 'done' : 'todo';
  }

  // Find note title
  const note = sidebar.notes.find((n) => n.uuid === meta.note_id);
  const noteTitle = note?.title;

  return {
    uuid: meta.uuid,
    name: meta.name,
    note_id: meta.note_id,
    task_column: effectiveColumn,
    completed,
    displayText,
    noteTitle,
  };
};

// Get the effective note ID (props override > sidebar current note)
const effectiveNoteId = computed(() => {
  return props.noteId || sidebar.currentNoteId;
});

// Filter tasks by noteId if available
const filteredTasks = computed(() => {
  if (effectiveNoteId.value) {
    return sidebar.tasks.filter((t) => t.note_id === effectiveNoteId.value);
  }
  return sidebar.tasks;
});

// Get effective columns (props override > user default)
const effectiveColumns = computed(() => {
  // Use provided columns (e.g., from frontmatter) or fall back to user's default
  const columns = props.columns ? [...props.columns] : [...sidebar.kanbanColumns];

  // Also include any columns that tasks are assigned to but aren't in the column list
  const taskColumns = new Set<string>();
  filteredTasks.value.forEach((task) => {
    const parsed = parseTask(task);
    if (parsed.task_column) {
      taskColumns.add(parsed.task_column);
    }
  });

  // Add missing columns before 'done'
  taskColumns.forEach((col) => {
    if (!columns.includes(col)) {
      const doneIndex = columns.indexOf('done');
      if (doneIndex >= 0) {
        columns.splice(doneIndex, 0, col);
      } else {
        columns.push(col);
      }
    }
  });

  return columns;
});

// Group tasks by column
const tasksByColumn = computed(() => {
  const map = new Map<string, KanbanTask[]>();

  // Initialize all columns
  effectiveColumns.value.forEach((col) => {
    map.set(col, []);
  });

  // Group filtered tasks
  filteredTasks.value.forEach((task) => {
    const parsed = parseTask(task);
    const column = parsed.task_column || 'todo';
    const list = map.get(column) || [];
    list.push(parsed);
    map.set(column, list);
  });

  return map;
});

const getColumnTasks = (column: string): KanbanTask[] => {
  return tasksByColumn.value.get(column) || [];
};

// Drag and drop handlers
const onDragStart = (task: KanbanTask, event: DragEvent) => {
  draggingTask.value = task;
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', task.uuid);
  }
};

const onDragEnd = () => {
  draggingTask.value = null;
  dragOverColumn.value = null;
};

const onDragEnter = (column: string, _event: DragEvent) => {
  if (draggingTask.value && draggingTask.value.task_column !== column) {
    dragOverColumn.value = column;
  }
};

const onDragLeave = (column: string, event: DragEvent) => {
  // Only clear if leaving the column entirely
  const relatedTarget = event.relatedTarget as HTMLElement;
  const currentTarget = event.currentTarget as HTMLElement;
  if (!currentTarget.contains(relatedTarget)) {
    if (dragOverColumn.value === column) {
      dragOverColumn.value = null;
    }
  }
};

const onDrop = async (column: string, event: DragEvent) => {
  event.preventDefault();
  dragOverColumn.value = null;

  if (!draggingTask.value) return;

  const task = draggingTask.value;
  if (task.task_column === column) {
    draggingTask.value = null;
    return;
  }

  // Update task column via API
  try {
    const result = await sidebar.updateTaskColumn(task.uuid, column);

    // Mark note as locally updated to prevent SSE duplicate processing
    if (result.note_uuid) {
      markNoteUpdatedLocally(result.note_uuid);
    }

    // Emit event to update the editor view using the backend's response
    // (backend handles checkbox changes when moving to todo/done)
    eventHub.emit('taskColumnUpdated', {
      note_id: task.note_id,
      old_task: result.old_task,
      new_task: result.new_task,
    });

    buefy?.toast.open({
      message: `Task moved to ${column}`,
      type: 'is-success',
      duration: 1500,
    });
  } catch (error) {
    console.error('Failed to update task column:', error);
    buefy?.toast.open({
      message: 'Failed to move task',
      type: 'is-danger',
      duration: 2000,
    });
  }

  draggingTask.value = null;
};

const toggleTaskCompletion = async (task: KanbanTask) => {
  // Update the task name with new completion status
  const newCheckbox = task.completed ? '[x]' : '[ ]';
  const oldCheckbox = task.completed ? '[ ]' : '[x]';

  // Replace the checkbox in the original task name
  const newName = task.name.replace(`- ${oldCheckbox}`, `- ${newCheckbox}`);

  try {
    await sidebar.saveTaskProgress(newName, task.uuid);
    // Emit event to update the editor view
    eventHub.emit('taskUpdated', {
      note_id: task.note_id,
      task: newName,
      completed: task.completed,
    });
  } catch (_e) {
    // Revert on error
    task.completed = !task.completed;
    buefy?.toast.open({
      message: 'Failed to update task',
      type: 'is-danger',
      duration: 2000,
    });
  }
};

const close = () => {
  emit('close');
};
</script>

<style scoped>
.kanban-modal {
  width: auto;
  min-width: 500px;
  max-width: 90vw;
  max-height: 80vh;
}

.modal-card-head {
  background-color: var(--main-bg-color);
  border-bottom: 1px solid var(--border-color);
}

.modal-card-title {
  color: var(--text-primary);
  font-weight: 600;
}

.modal-card-body {
  background-color: var(--main-bg-color);
  color: var(--text-primary);
  padding: 16px;
  overflow-x: auto;
}

.modal-card-foot {
  background-color: var(--main-bg-color);
  border-top: 1px solid var(--border-color);
  justify-content: flex-end;
}

.kanban-board {
  display: flex;
  gap: 16px;
  min-height: 400px;
  justify-content: center;
}

.kanban-column {
  flex: 1;
  min-width: 200px;
  max-width: 300px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.kanban-column.drag-over {
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 2px rgba(130, 170, 255, 0.2);
}

.column-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  border-bottom: 1px solid var(--border-color);
  background: var(--main-bg-lighter);
  border-radius: 8px 8px 0 0;
}

.column-title {
  font-weight: 600;
  color: var(--text-primary);
  text-transform: capitalize;
}

.column-count {
  background: var(--tag-bg);
  color: var(--text-secondary);
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.85em;
}

.column-tasks {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.kanban-task {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px;
  background: var(--input-bg);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  cursor: grab;
  transition: transform 0.15s, box-shadow 0.15s, opacity 0.15s;
}

.kanban-task:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.kanban-task:active {
  cursor: grabbing;
}

.kanban-task.is-dragging {
  opacity: 0.5;
  transform: scale(0.98);
}

.kanban-task.is-completed .task-text {
  text-decoration: line-through;
  color: var(--text-muted);
}

.task-checkbox {
  flex-shrink: 0;
  padding-top: 2px;
}

.task-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.task-text {
  color: var(--text-primary);
  word-break: break-word;
}

.task-note {
  font-size: 0.8em;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.empty-column {
  color: var(--text-muted);
  text-align: center;
  padding: 20px;
  font-size: 0.9em;
}

.no-tasks {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}

.no-tasks p {
  margin-bottom: 8px;
}

.no-tasks .hint {
  font-size: 0.9em;
}

.no-tasks code {
  background: var(--code-bg);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Fira Code', monospace;
  font-size: 0.9em;
}

/* Delete button styling */
.delete {
  background-color: rgba(255, 255, 255, 0.1);
}

.delete:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

/* Responsive */
@media screen and (max-width: 768px) {
  .kanban-modal {
    width: 95vw;
  }

  .kanban-board {
    flex-direction: column;
  }

  .kanban-column {
    max-width: none;
    min-height: auto;
  }

  .column-tasks {
    max-height: 200px;
  }
}
</style>
