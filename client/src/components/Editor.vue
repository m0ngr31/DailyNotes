<template>
  <div class="editor" ref="editorContainer"></div>
</template>

<script setup lang="ts">
import { defaultKeymap, history, historyKeymap, indentWithTab } from '@codemirror/commands';
import { markdown, markdownLanguage } from '@codemirror/lang-markdown';
import {
  foldEffect,
  foldedRanges,
  foldGutter,
  foldKeymap,
  HighlightStyle,
  syntaxHighlighting,
} from '@codemirror/language';
import { languages } from '@codemirror/language-data';
import {
  EditorState,
  type Extension,
  type Range,
  StateEffect,
  StateField,
} from '@codemirror/state';
import {
  Decoration,
  type DecorationSet,
  EditorView,
  keymap,
  type ViewUpdate,
} from '@codemirror/view';
import { tags as t } from '@lezer/highlight';
import { vim } from '@replit/codemirror-vim';
import _ from 'lodash';
import { computed, inject, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import type { IGlobal } from '../interfaces';

import { newDay, newNote } from '../services/consts';
import directionService from '../services/direction';
import eventHub from '../services/eventHub';
import { SharedBuefy } from '../services/sharedBuefy';
import themeService from '../services/theme';
import { UploadService } from '../services/uploads';

interface Props {
  value: string;
  useVimMode: boolean;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  valChanged: [value: string];
  saveShortcut: [];
}>();

const global = inject<IGlobal>('global');
if (!global) {
  throw new Error('Global context not provided');
}

const editorContainer = ref<HTMLDivElement>();
let editorView: EditorView;
const MAX_UPLOAD_SIZE = 10 * 1024 * 1024; // Keep in sync with backend limit

// Theme-aware CodeMirror 6 theme using CSS variables
// The actual colors are defined in App.vue and switch based on .theme-light/.theme-dark class
const customTheme = EditorView.theme({
  '&': {
    backgroundColor: 'var(--editor-bg)',
    height: '100%',
    width: '100%',
    fontFamily: "'Fira Code', monospace",
    fontSize: '16px',
    fontWeight: '400',
    overflowX: 'hidden',
    border: 'none',
  },
  '.cm-scroller': {
    overflowX: 'hidden',
    width: '100%',
  },
  '.cm-content': {
    padding: '10px 0px 10px 20px',
    caretColor: 'var(--editor-cursor)',
    fontSize: '16px',
    fontWeight: '400',
    color: 'var(--text-primary)',
    width: '100%',
    maxWidth: 'none',
  },
  '.cm-line': {
    color: 'var(--text-primary)',
  },
  '&.cm-focused .cm-cursor': {
    borderLeftColor: 'var(--editor-cursor)',
  },
  '&.cm-focused .cm-selectionBackground, .cm-selectionBackground, .cm-content ::selection': {
    backgroundColor: 'var(--editor-selection)',
  },
  '.cm-gutters': {
    backgroundColor: 'var(--editor-gutter-bg)',
    color: 'var(--editor-gutter-text)',
    border: 'none',
  },
  '.cm-activeLine': {
    backgroundColor: 'var(--editor-line-highlight)',
  },
  '.cm-foldPlaceholder': {
    backgroundColor: 'var(--tag-bg)',
    border: 'none',
    color: 'var(--accent-primary)',
  },
  '.cm-foldGutter': {
    width: '20px',
  },
  '.cm-foldGutter span': {
    fontSize: '16px !important',
    color: 'var(--accent-primary) !important',
    cursor: 'pointer',
    padding: '0 4px',
  },
  '.cm-foldGutter .cm-gutterElement': {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  // Syntax highlighting using CSS variables
  '.cm-header': {
    color: 'var(--syntax-heading)',
  },
  '.cm-strong': {
    color: 'var(--syntax-string)',
    fontSize: '140%',
  },
  '.cm-em': {
    fontStyle: 'italic',
  },
  '.cm-link': {
    color: 'var(--syntax-link)',
    textDecoration: 'none',
  },
  '.cm-url': {
    color: 'var(--syntax-keyword)',
  },
  '.cm-strikethrough': {
    textDecoration: 'line-through',
  },
  '.cm-keyword': {
    color: 'var(--syntax-keyword)',
  },
  '.cm-atom': {
    color: 'var(--syntax-number)',
  },
  '.cm-number': {
    color: 'var(--syntax-number)',
  },
  '.cm-comment': {
    color: 'var(--syntax-comment)',
  },
  '.cm-meta': {
    color: 'var(--syntax-meta)',
  },
  '.cm-variable-2': {
    color: 'var(--syntax-variable)',
  },
  '.cm-variable-3': {
    color: 'var(--syntax-attribute)',
  },
  '.cm-string': {
    color: 'var(--syntax-string)',
  },
  '.cm-quote': {
    color: 'var(--syntax-comment)',
  },
  // Front matter - force normal size and weight
  '.cm-processingInstruction': {
    color: 'var(--syntax-operator)',
    fontSize: '16px !important',
    fontWeight: '400 !important',
  },
  '.cm-propertyName': {
    color: 'var(--syntax-number)',
    fontSize: '16px !important',
    fontWeight: '400 !important',
  },
  // Custom markdown styling
  '.cm-frontmatter-delimiter': {
    color: 'var(--syntax-operator) !important',
    fontSize: '14px !important',
    fontWeight: '400 !important',
  },
  '.cm-frontmatter-key': {
    color: 'var(--syntax-tag) !important',
    fontSize: '14px !important',
    fontWeight: '400 !important',
  },
  '.cm-frontmatter-value': {
    color: 'var(--syntax-string) !important',
    fontSize: '12px !important',
    fontWeight: '400 !important',
  },
  '.cm-heading-mark': {
    color: 'var(--syntax-meta) !important',
    fontSize: '1.4em !important',
    fontWeight: '700 !important',
    lineHeight: '1.5em !important',
  },
  '.cm-heading-text': {
    color: 'var(--syntax-meta) !important',
    fontSize: '1.4em !important',
    fontWeight: '700 !important',
    lineHeight: '1.5em !important',
  },
  '.cm-task-unchecked': {
    color: 'var(--syntax-meta) !important',
    fontWeight: '400 !important',
  },
  '.cm-task-checked': {
    color: 'var(--syntax-keyword) !important',
    fontWeight: '400 !important',
  },
  '.cm-kanban-column': {
    color: 'var(--syntax-string) !important',
    fontWeight: '500 !important',
  },
  '.cm-url-link': {
    color: 'var(--syntax-keyword) !important',
    textDecoration: 'none !important',
  },
  // Link hover effect when Cmd/Ctrl is pressed
  '&.link-hover': {
    cursor: 'pointer !important',
  },
  '&.link-hover .cm-url-link': {
    color: 'var(--text-link) !important',
    textDecoration: 'underline !important',
    cursor: 'pointer !important',
  },
  '&.link-hover .cm-link': {
    color: 'var(--text-link) !important',
    textDecoration: 'underline',
    cursor: 'pointer !important',
  },
  '&.link-hover .cm-url': {
    color: 'var(--text-link) !important',
    textDecoration: 'underline',
    cursor: 'pointer !important',
  },
  // Code block styling
  '.cm-line.cm-codeblock': {
    backgroundColor: 'var(--code-bg)',
    fontFamily: "'Fira Code', monospace",
  },
  '.cm-codeInfo': {
    color: 'var(--syntax-comment)',
    fontStyle: 'italic',
  },
  '.tok-keyword': {
    color: 'var(--syntax-keyword)',
  },
  '.tok-string': {
    color: 'var(--syntax-string)',
  },
  '.tok-comment': {
    color: 'var(--syntax-comment)',
    fontStyle: 'italic',
  },
  '.tok-variableName': {
    color: 'var(--syntax-variable)',
  },
  '.tok-typeName': {
    color: 'var(--syntax-meta)',
  },
  '.tok-function': {
    color: 'var(--syntax-function)',
  },
  '.tok-number': {
    color: 'var(--syntax-number)',
  },
  '.tok-operator': {
    color: 'var(--syntax-operator)',
  },
  '.tok-punctuation': {
    color: 'var(--syntax-operator)',
  },
  '.tok-propertyName': {
    color: 'var(--syntax-tag)',
  },
  '.tok-bool': {
    color: 'var(--accent-error)',
  },
  '.tok-constant': {
    color: 'var(--syntax-number)',
  },
  '.tok-className': {
    color: 'var(--syntax-meta)',
  },
});

// Syntax highlighting theme for code blocks only
// We don't style markdown elements here since we use custom decorators
// Note: HighlightStyle doesn't support CSS variables, so we keep these
// hardcoded for now. The main theme colors are handled by customTheme above.
const markdownHighlightingDark = HighlightStyle.define([
  { tag: t.strong, color: '#C3E88D', fontWeight: 'bold' },
  { tag: t.emphasis, color: '#82AAFF', fontStyle: 'italic' },
  { tag: t.strikethrough, textDecoration: 'line-through', color: '#546E7A' },
  { tag: t.link, color: '#82AAFF', textDecoration: 'underline' },
  { tag: t.url, color: '#C792EA' },
  { tag: t.quote, color: '#546E7A', fontStyle: 'italic' },
  { tag: t.list, color: '#F78C6C' },
  { tag: t.monospace, color: '#C3E88D', fontFamily: "'Fira Code', monospace" },
  { tag: t.comment, color: '#546E7A', fontStyle: 'italic' },
  { tag: t.keyword, color: '#C792EA' },
  { tag: t.string, color: '#C3E88D' },
  { tag: t.number, color: '#F78C6C' },
  { tag: t.operator, color: '#89DDFF' },
  { tag: t.punctuation, color: '#89DDFF' },
  { tag: t.bracket, color: '#EEFFFF' },
  { tag: t.variableName, color: '#EEFFFF' },
  { tag: t.typeName, color: '#FFCB6B' },
  { tag: t.function(t.variableName), color: '#82AAFF' },
  { tag: t.propertyName, color: '#F07178' },
  { tag: t.bool, color: '#FF5370' },
  { tag: t.constant(t.variableName), color: '#F78C6C' },
  { tag: t.className, color: '#FFCB6B' },
]);

const markdownHighlightingLight = HighlightStyle.define([
  { tag: t.strong, color: '#718c00', fontWeight: 'bold' },
  { tag: t.emphasis, color: '#4271ae', fontStyle: 'italic' },
  { tag: t.strikethrough, textDecoration: 'line-through', color: '#8e908c' },
  { tag: t.link, color: '#4271ae', textDecoration: 'underline' },
  { tag: t.url, color: '#8959a8' },
  { tag: t.quote, color: '#8e908c', fontStyle: 'italic' },
  { tag: t.list, color: '#f5871f' },
  { tag: t.monospace, color: '#718c00', fontFamily: "'Fira Code', monospace" },
  { tag: t.comment, color: '#8e908c', fontStyle: 'italic' },
  { tag: t.keyword, color: '#8959a8' },
  { tag: t.string, color: '#718c00' },
  { tag: t.number, color: '#f5871f' },
  { tag: t.operator, color: '#3e999f' },
  { tag: t.punctuation, color: '#3e999f' },
  { tag: t.bracket, color: '#4d4d4c' },
  { tag: t.variableName, color: '#4d4d4c' },
  { tag: t.typeName, color: '#c99e00' },
  { tag: t.function(t.variableName), color: '#4271ae' },
  { tag: t.propertyName, color: '#c82829' },
  { tag: t.bool, color: '#c82829' },
  { tag: t.constant(t.variableName), color: '#f5871f' },
  { tag: t.className, color: '#c99e00' },
]);

// Get the appropriate highlighting based on current theme
const getMarkdownHighlighting = () => {
  return themeService.isDark ? markdownHighlightingDark : markdownHighlightingLight;
};

// Decorator for checkbox styling
const checkboxDecorator = StateField.define<DecorationSet>({
  create(state) {
    return decorateCheckboxes(state);
  },
  update(decorations, tr) {
    if (tr.docChanged) {
      return decorateCheckboxes(tr.state);
    }
    return decorations;
  },
  provide: (f) => EditorView.decorations.from(f),
});

function decorateCheckboxes(state: EditorState): DecorationSet {
  const decorations: Range<Decoration>[] = [];
  const text = state.doc.toString();
  const lines = text.split('\n');
  let pos = 0;
  let inFrontmatter = false;
  let frontmatterDelimiterCount = 0;

  for (const line of lines) {
    // Front matter delimiters (---)
    if (line.trim() === '---') {
      frontmatterDelimiterCount++;
      decorations.push(
        Decoration.mark({ class: 'cm-frontmatter-delimiter' }).range(pos, pos + line.length)
      );

      // Toggle frontmatter state
      if (frontmatterDelimiterCount === 1) {
        inFrontmatter = true;
      } else if (frontmatterDelimiterCount === 2) {
        inFrontmatter = false;
      }
    }
    // Front matter content (key: value) - only if inside frontmatter
    else if (inFrontmatter && frontmatterDelimiterCount === 1) {
      const frontmatterMatch = line.match(/^([a-zA-Z_-]+):\s*(.*)$/);
      if (frontmatterMatch) {
        const keyEnd = pos + frontmatterMatch[1].length;
        const colonEnd = keyEnd + 1; // Include the colon
        decorations.push(Decoration.mark({ class: 'cm-frontmatter-key' }).range(pos, colonEnd));
        if (frontmatterMatch[2]) {
          decorations.push(
            Decoration.mark({ class: 'cm-frontmatter-value' }).range(colonEnd, pos + line.length)
          );
        }
      }
    }
    // Headings (##) - only if NOT in frontmatter
    else if (!inFrontmatter) {
      const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
      if (headingMatch) {
        const hashesEnd = pos + headingMatch[1].length;
        decorations.push(Decoration.mark({ class: 'cm-heading-mark' }).range(pos, hashesEnd));
        decorations.push(
          Decoration.mark({ class: 'cm-heading-text' }).range(hashesEnd, pos + line.length)
        );
      }

      // Checkboxes
      const checkboxMatch = line.match(/- \[( |x)\]/);
      if (checkboxMatch) {
        const checkboxStart = pos + line.indexOf('[');
        const isChecked = checkboxMatch[1] === 'x';
        decorations.push(
          Decoration.mark({
            class: isChecked ? 'cm-task-checked' : 'cm-task-unchecked',
          }).range(checkboxStart, checkboxStart + 3)
        );

        // Kanban column syntax >>column-name at end of task line
        const columnMatch = line.match(/>>([a-zA-Z0-9-]+)\s*$/);
        if (columnMatch) {
          const columnStart = pos + line.lastIndexOf('>>' + columnMatch[1]);
          const columnEnd = columnStart + columnMatch[0].trimEnd().length;
          decorations.push(
            Decoration.mark({ class: 'cm-kanban-column' }).range(columnStart, columnEnd)
          );
        }
      }

      // URLs
      const urlRegex = /https?:\/\/[^\s]+/g;
      let urlMatch;
      while ((urlMatch = urlRegex.exec(line)) !== null) {
        const urlStart = pos + urlMatch.index;
        decorations.push(
          Decoration.mark({ class: 'cm-url-link' }).range(urlStart, urlStart + urlMatch[0].length)
        );
      }
    }

    pos += line.length + 1; // +1 for newline
  }

  return Decoration.set(decorations, true);
}

const generateTaskList = (text: string) => {
  if (!global) return;

  const regex = /- \[( |x)\] (.+)/gm;
  let m: RegExpExecArray | null;
  let completed = false;
  global.taskList.value.splice(0);
  m = regex.exec(text);
  while (m !== null) {
    if (m.index === regex.lastIndex) {
      regex.lastIndex++;
    }
    completed = m[1] === 'x';
    global.taskList.value.push({ completed, name: m[2], index: m.index });
    m = regex.exec(text);
  }
};

const notify = (message: string, type: 'is-success' | 'is-danger' | 'is-info' = 'is-info') => {
  SharedBuefy.notifications?.open({
    duration: 4000,
    message,
    position: 'is-top',
    type,
  });
};

const insertImageMarkdown = (url: string, filename: string, position?: number): number => {
  if (!editorView) {
    return 0;
  }

  const altText = filename ? filename.replace(/\.[^/.]+$/, '') || 'image' : 'image';
  const state = editorView.state;
  const insertPos = typeof position === 'number' ? position : state.selection.main.from;
  const needsLeadingNewline =
    insertPos > 0 && state.doc.sliceString(insertPos - 1, insertPos) !== '\n';
  const needsTrailingNewline = state.doc.sliceString(insertPos, insertPos + 1) !== '\n';
  const markdown = `${needsLeadingNewline ? '\n' : ''}![${altText}](${url})${
    needsTrailingNewline ? '\n' : ''
  }`;

  editorView.dispatch({
    changes: {
      from: insertPos,
      to: insertPos,
      insert: markdown,
    },
    selection: {
      anchor: insertPos + markdown.length,
      head: insertPos + markdown.length,
    },
  });
  editorView.focus();

  return editorView.state.selection.main.head;
};

const extractFilesFromClipboard = (event: ClipboardEvent): File[] => {
  if (!event.clipboardData) {
    return [];
  }

  const directFiles = Array.from(event.clipboardData.files || []);
  const itemFiles = Array.from(event.clipboardData.items || [])
    .filter((item) => item.kind === 'file' && item.type.startsWith('image/'))
    .map((item) => item.getAsFile())
    .filter((file): file is File => !!file);

  return [...directFiles, ...itemFiles].filter((file) => file.type.startsWith('image/'));
};

const dedupeFiles = (files: File[]): File[] => {
  const seen = new Set<string>();
  const unique: File[] = [];

  files.forEach((file) => {
    const key = `${file.name}-${file.size}-${file.lastModified}`;
    if (!seen.has(key)) {
      seen.add(key);
      unique.push(file);
    }
  });

  return unique;
};

const handleUploads = async (files: File[], position?: number) => {
  const uniqueFiles = dedupeFiles(files);

  if (!uniqueFiles.length) {
    return;
  }

  let insertPosition = position;

  for (const file of uniqueFiles) {
    if (!file || !file.type.startsWith('image/')) {
      continue;
    }

    if (file.size > MAX_UPLOAD_SIZE) {
      notify(`"${file.name}" exceeds the 10MB upload limit.`, 'is-danger');
      continue;
    }

    try {
      const res = await UploadService.uploadImage(file);
      insertPosition = insertImageMarkdown(res.url || res.path, file.name, insertPosition);
      notify(`Uploaded ${file.name}`, 'is-success');
    } catch (err: any) {
      const errorMsg =
        (err?.response?.data && (err.response.data.error || err.response.data.message)) ||
        'Failed to upload image';
      notify(errorMsg, 'is-danger');
    }
  }
};

const handlePasteEvent = (event: ClipboardEvent): boolean => {
  const imageFiles = extractFilesFromClipboard(event);

  if (!imageFiles.length) {
    return false;
  }

  event.preventDefault();
  void handleUploads(imageFiles);
  return true;
};

const handleDropEvent = (event: DragEvent, view: EditorView): boolean => {
  const files = Array.from(event.dataTransfer?.files || []);
  const imageFiles = files.filter((file) => file.type.startsWith('image/'));

  if (!imageFiles.length) {
    if (files.length) {
      event.preventDefault();
    }
    return false;
  }

  event.preventDefault();
  const dropPos = view.posAtCoords({ x: event.clientX, y: event.clientY });
  void handleUploads(imageFiles, dropPos === null ? undefined : dropPos);
  return true;
};

const save = () => {
  emit('saveShortcut');
  return true;
};

const focus = () => {
  _.defer(() => {
    if (editorView && !editorView.hasFocus) {
      const lastPos = editorView.state.doc.length;
      editorView.dispatch({
        selection: { anchor: lastPos, head: lastPos },
      });
      editorView.focus();
    }
  });
};

const refresh = () => {
  _.defer(() => {
    if (editorView) {
      editorView.requestMeasure();
    }
  });
};

const getFoldState = (): { from: number; to: number }[] => {
  if (!editorView) return [];

  const folds: { from: number; to: number }[] = [];
  const ranges = foldedRanges(editorView.state);

  // Use between() to iterate over all folded ranges in the document
  const docLength = editorView.state.doc.length;
  ranges.between(0, docLength, (from, to) => {
    folds.push({ from, to });
  });

  return folds;
};

const setFoldState = (folds: { from: number; to: number }[]) => {
  if (!editorView || !folds.length) return;

  _.defer(() => {
    if (!editorView) return;

    const docLength = editorView.state.doc.length;
    const validFolds = folds.filter((f) => f.from >= 0 && f.to <= docLength && f.from < f.to);

    if (!validFolds.length) return;

    const effects = validFolds.map((f) => foldEffect.of({ from: f.from, to: f.to }));

    editorView.dispatch({ effects });
  });
};

const extractUrl = (text: string, pos: number): string | null => {
  // Find the line containing the position
  const lines = text.split('\n');
  let currentPos = 0;
  let line = '';

  for (const l of lines) {
    if (pos >= currentPos && pos <= currentPos + l.length) {
      line = l;
      pos = pos - currentPos;
      break;
    }
    currentPos += l.length + 1; // +1 for newline
  }

  // Regex patterns for different link formats
  // Markdown links: [text](url)
  const mdLinkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
  // Bare URLs: http(s)://...
  const urlRegex = /https?:\/\/[^\s)]+/g;

  let match: RegExpExecArray | null;

  // Check for markdown links
  match = mdLinkRegex.exec(line);
  while (match !== null) {
    const start = match.index;
    const end = match.index + match[0].length;
    if (pos >= start && pos <= end) {
      return match[2]; // Return the URL part
    }
    match = mdLinkRegex.exec(line);
  }

  // Check for bare URLs
  match = urlRegex.exec(line);
  while (match !== null) {
    const start = match.index;
    const end = match.index + match[0].length;
    if (pos >= start && pos <= end) {
      return match[0];
    }
    match = urlRegex.exec(line);
  }

  return null;
};

const handleMouseDown = (event: MouseEvent, view: EditorView) => {
  // Check for Cmd (Mac) or Ctrl (Windows/Linux)
  if (event.metaKey || event.ctrlKey) {
    const pos = view.posAtCoords({ x: event.clientX, y: event.clientY });
    if (pos !== null) {
      const url = extractUrl(view.state.doc.toString(), pos);
      if (url) {
        event.preventDefault();
        window.open(url, '_blank');
      }
    }
  }
};

const handleMouseMove = (event: MouseEvent, view: EditorView) => {
  const wrapper = view.dom;
  if (event.metaKey || event.ctrlKey) {
    const pos = view.posAtCoords({ x: event.clientX, y: event.clientY });
    if (pos !== null) {
      const url = extractUrl(view.state.doc.toString(), pos);
      if (url) {
        wrapper.style.cursor = 'pointer';
        wrapper.classList.add('link-hover');
      } else {
        wrapper.style.cursor = '';
        wrapper.classList.remove('link-hover');
      }
    }
  } else {
    wrapper.style.cursor = '';
    wrapper.classList.remove('link-hover');
  }
};

const handleMouseOut = (view: EditorView) => {
  const wrapper = view.dom;
  wrapper.style.cursor = '';
  wrapper.classList.remove('link-hover');
};

const handleValueUpdate = (firstMount?: boolean) => {
  _.defer(() => {
    if (!editorView) return;

    const currentDoc = editorView.state.doc.toString();
    const newValue = props.value || '';

    if (currentDoc === newValue) return;

    // Don't update if editor has focus and user is actively typing (unless it's first mount)
    if (!firstMount && editorView.hasFocus) {
      return;
    }

    const currentSelection = editorView.state.selection.main;

    editorView.dispatch({
      changes: {
        from: 0,
        to: editorView.state.doc.length,
        insert: newValue,
      },
      selection: (() => {
        if (props.value === newNote) {
          return { anchor: 8, head: 8 }; // Position after "title: "
        }
        if (props.value === newDay) {
          return { anchor: 7, head: 7 }; // Position after "date: "
        }
        if (firstMount) {
          return { anchor: newValue.length, head: newValue.length };
        }
        // Try to restore cursor position
        const newPos = Math.min(currentSelection.head, newValue.length);
        return { anchor: newPos, head: newPos };
      })(),
    });
  });
};

const getExtensions = (): Extension[] => {
  const extensions: Extension[] = [
    history(),
    markdown({
      base: markdownLanguage,
      codeLanguages: languages,
      addKeymap: true,
    }),
    syntaxHighlighting(getMarkdownHighlighting()),
    foldGutter(),
    checkboxDecorator, // Apply custom decorations after syntax highlighting
    customTheme, // Apply custom theme last to override any default styles
    EditorView.lineWrapping,
    keymap.of([
      ...defaultKeymap,
      ...historyKeymap,
      ...foldKeymap,
      indentWithTab,
      { key: 'Mod-s', run: save, preventDefault: true },
    ]),
    EditorView.updateListener.of((update: ViewUpdate) => {
      if (update.docChanged) {
        const newValue = update.state.doc.toString();
        generateTaskList(newValue);
        throttledEmit(newValue);
        // Update auto-direction if in auto mode
        if (directionService.preference === 'auto') {
          debouncedDirectionUpdate(newValue);
        }
      }
    }),
    EditorView.domEventHandlers({
      mousedown: (event, view) => {
        handleMouseDown(event, view);
        return false;
      },
      paste: (event) => {
        return handlePasteEvent(event as ClipboardEvent);
      },
      drop: (event, view) => {
        return handleDropEvent(event as DragEvent, view);
      },
      dragover: (event) => {
        if (Array.from((event as DragEvent).dataTransfer?.types || []).includes('Files')) {
          event.preventDefault();
          return true;
        }
        return false;
      },
      mousemove: (event, view) => {
        handleMouseMove(event, view);
        return false;
      },
      mouseout: (event, view) => {
        handleMouseOut(view);
        return false;
      },
    }),
  ];

  if (props.useVimMode) {
    extensions.push(vim());
  }

  return extensions;
};

const throttledEmit = _.throttle(
  (value: string) => {
    emit('valChanged', value);
  },
  500,
  { trailing: true, leading: false }
);

// Debounced direction update for auto-detection
const debouncedDirectionUpdate = _.debounce(
  (value: string) => {
    directionService.updateAutoDirection(value);
  },
  300,
  { trailing: true, leading: false }
);

onMounted(() => {
  if (!editorContainer.value) return;

  editorView = new EditorView({
    state: EditorState.create({
      doc: props.value || '',
      extensions: getExtensions(),
    }),
    parent: editorContainer.value,
  });

  handleValueUpdate(true);
  // Generate task list on initial mount
  generateTaskList(props.value || '');
  // Trigger auto-direction on initial content
  if (directionService.preference === 'auto') {
    directionService.updateAutoDirection(props.value || '');
  }
  eventHub.on('focusEditor', focus);
});

onBeforeUnmount(() => {
  eventHub.off('focusEditor', focus);
  if (editorView) {
    editorView.destroy();
  }
});

watch(
  () => props.value,
  () => {
    handleValueUpdate();
    // Regenerate task list when content changes
    generateTaskList(props.value || '');
  }
);

watch(
  () => props.useVimMode,
  () => {
    if (editorView) {
      // Recreate the editor with new extensions
      const currentDoc = editorView.state.doc.toString();
      const currentSelection = editorView.state.selection;

      editorView.setState(
        EditorState.create({
          doc: currentDoc,
          selection: currentSelection,
          extensions: getExtensions(),
        })
      );
    }
  }
);

watch(
  () => global?.taskList.value,
  () => {
    if (!editorView || !global) return;

    const data = editorView.state.doc.toString();
    let newData = data;
    global.taskList.value.forEach((task) => {
      const c = task.completed ? 'x' : ' ';
      newData = newData.substr(0, task.index + 3) + c + newData.substr(task.index + 4);
    });
    if (newData !== data) {
      editorView.dispatch({
        changes: {
          from: 0,
          to: editorView.state.doc.length,
          insert: newData,
        },
      });
    }
  },
  { deep: true }
);

defineExpose({
  refresh,
  focus,
  getFoldState,
  setFoldState,
});
</script>

<style scoped>
.editor {
  background-color: var(--editor-bg);
  height: 100%;
  width: 100%;
  border: none;
  outline: none;
  transition: background-color 0.2s ease;
}

.editor :deep(.cm-editor) {
  width: 100%;
  border: none;
  outline: none;
}

.editor :deep(.cm-scroller) {
  width: 100%;
  border: none;
  outline: none;
}

/* Mobile styles for editor */
@media screen and (max-width: 767px) {
  .editor :deep(.cm-content) {
    padding: 8px 8px 8px 12px;
    font-size: 16px; /* Prevents iOS zoom on focus */
  }

  .editor :deep(.cm-foldGutter) {
    width: 16px;
  }

  .editor :deep(.cm-gutters) {
    padding-inline-start: 4px;
  }
}
</style>
