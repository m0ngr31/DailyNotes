<template>
  <div class="editor" @click="prevent($event)">
    <textarea ref="editor"></textarea>
  </div>
</template>

<script lang="ts">
import { Vue, Component, Watch, Inject } from 'vue-property-decorator';
import * as CodeMirror from 'codemirror';
import _ from 'lodash';

// Modes
import 'codemirror/mode/gfm/gfm.js';
import 'codemirror/mode/clike/clike.js';
import 'codemirror/mode/css/css.js';
import 'codemirror/mode/go/go.js';
import 'codemirror/mode/lua/lua.js';
import 'codemirror/mode/php/php.js';
import 'codemirror/mode/perl/perl.js';
import 'codemirror/mode/r/r.js';
import 'codemirror/mode/ruby/ruby.js';
import 'codemirror/mode/rust/rust.js';
import 'codemirror/mode/sass/sass.js';
import 'codemirror/mode/vb/vb.js';
import 'codemirror/mode/xml/xml.js';
import 'codemirror/mode/vbscript/vbscript.js';
import 'codemirror/mode/htmlmixed/htmlmixed.js';
import 'codemirror/mode/shell/shell.js';
import 'codemirror/mode/python/python.js';
import 'codemirror/mode/javascript/javascript.js';
import 'codemirror/mode/yaml-frontmatter/yaml-frontmatter.js';
import 'codemirror/mode/sql/sql.js';

// Addons
import 'codemirror/addon/edit/continuelist.js';
import 'codemirror/addon/edit/closebrackets.js';

// Folding
import 'codemirror/addon/fold/foldcode.js';
import 'codemirror/addon/fold/foldgutter.js';
import 'codemirror/addon/fold/brace-fold.js';
import 'codemirror/addon/fold/xml-fold.js';
import 'codemirror/addon/fold/indent-fold.js';
import 'codemirror/addon/fold/markdown-fold.js';
import 'codemirror/addon/fold/comment-fold.js';

// Vim keymap
import 'codemirror/keymap/vim.js';

import {newNote, newDay} from '../services/consts';
import eventHub from '../services/eventHub';

@Component({
  props: {
    value: String,
    useVimMode: Boolean
  }
})
export default class Editor extends Vue {
  @Inject()
  private global: any;
  public editor!: CodeMirror.Editor;
  public value!: string;
  public useVimMode!: boolean;

  public get config(): CodeMirror.EditorConfiguration {
    return {
      tabSize: 2,
      lineNumbers: false,
      lineWrapping: true,
      mode: {
        name: "yaml-frontmatter",
        tokenTypeOverrides: {
          emoji: "emoji"
        }
      },
      foldGutter: true,
      gutters: ['CodeMirror-foldgutter'],
      theme: 'material',
      autofocus: true,
      autoCloseBrackets: true,
      keyMap: this.useVimMode ? 'vim' : 'default',
      extraKeys: {
        'Enter': 'newlineAndIndentContinueMarkdownList',
        'Ctrl-S': () => this.save(),
        'Cmd-S': () => this.save(),
      },
    };
  }

  mounted() {
    const tagElement = <HTMLTextAreaElement>this.$refs.editor;
    this.editor = CodeMirror.fromTextArea(tagElement, this.config);

    this.editor.on('changes', _.throttle(() => {
      this.generateTaskList();
      this.$emit('valChanged', this.editor.getValue());
    }, 500, {trailing: true, leading: false}));

    // Add Cmd+click to open links
    this.editor.on('mousedown', (cm: CodeMirror.Editor, event: MouseEvent) => {
      // Check for Cmd (Mac) or Ctrl (Windows/Linux)
      if (event.metaKey || event.ctrlKey) {
        const pos = cm.coordsChar({ left: event.clientX, top: event.clientY });
        const token = cm.getTokenAt(pos);

        // Check if the token is a link
        if (token.type && token.type.includes('link')) {
          event.preventDefault();
          const url = this.extractUrl(cm, pos);
          if (url) {
            window.open(url, '_blank');
          }
        }
      }
    });

    // Add hover effect for links when Cmd/Ctrl is pressed using native DOM events
    const wrapper = this.editor.getWrapperElement();

    wrapper.addEventListener('mousemove', (event: MouseEvent) => {
      if (event.metaKey || event.ctrlKey) {
        const pos = this.editor.coordsChar({ left: event.clientX, top: event.clientY });
        const token = this.editor.getTokenAt(pos);

        // If hovering over a link, add cursor pointer and highlight
        if (token.type && token.type.includes('link')) {
          wrapper.style.cursor = 'pointer';
          wrapper.classList.add('link-hover');
        } else {
          wrapper.style.cursor = '';
          wrapper.classList.remove('link-hover');
        }
      } else {
        wrapper.style.cursor = '';
        wrapper.classList.remove('link-hover');
      }
    });

    // Clean up cursor when mouse leaves
    wrapper.addEventListener('mouseout', () => {
      wrapper.style.cursor = '';
      wrapper.classList.remove('link-hover');
    });

    this.handleValueUpdate(true);
  }

  generateTaskList() {
    // Get task list for today
    const data = this.editor.getValue();
    const regex = /- \[( |x)\] (.+)/gm;
    let m: any;
    let completed = false;
    this.global.taskList.splice(0)
    while ((m = regex.exec(data)) !== null) {
      // This is necessary to avoid infinite loops with zero-width matches
      if (m.index === regex.lastIndex) {
        regex.lastIndex++;
      }
      completed = m[1] === "x";
      this.global.taskList.push({ completed, name: m[2], index: m['index'] });
    }
  }

  created() {
    eventHub.$on('focusEditor', this.focus);
  }

  beforeDestroy() {
    eventHub.$off('focusEditor', this.focus);
  }

  prevent($event: any) {
    $event.stopPropagation();
  }

  save() {
    this.$emit('saveShortcut');
  }

  focus() {
    _.defer(() => {
      if (!this.editor.state.focused) {
        this.editor.setCursor(this.editor.lineCount(), 0);
        this.editor.focus();
      }
    });
  }

  refresh() {
    _.defer(() => {
      if (this.editor) {
        this.editor.refresh();
      }
    });
  }

  extractUrl(cm: CodeMirror.Editor, pos: CodeMirror.Position): string | null {
    const line = cm.getLine(pos.line);

    // Regex patterns for different link formats
    // Markdown links: [text](url)
    const mdLinkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
    // Bare URLs: http(s)://...
    const urlRegex = /https?:\/\/[^\s)]+/g;

    let match;

    // Check for markdown links
    while ((match = mdLinkRegex.exec(line)) !== null) {
      const start = match.index;
      const end = match.index + match[0].length;
      if (pos.ch >= start && pos.ch <= end) {
        return match[2]; // Return the URL part
      }
    }

    // Check for bare URLs
    while ((match = urlRegex.exec(line)) !== null) {
      const start = match.index;
      const end = match.index + match[0].length;
      if (pos.ch >= start && pos.ch <= end) {
        return match[0];
      }
    }

    return null;
  }

  @Watch('value')
  onValueChanged() {
    this.handleValueUpdate();
  }

  @Watch('useVimMode')
  onVimModeChanged() {
    if (this.editor) {
      this.editor.setOption('keyMap', this.useVimMode ? 'vim' : 'default');
    }
  }

  public handleValueUpdate(firstMount?: boolean) {
    _.defer(() => {
      const cursor = this.editor.getCursor();

      this.editor.setValue(this.value || '');

      if (this.value === newNote) {
        this.editor.setCursor(1, 7)
        return;
      }

      if (this.value === newDay) {
        this.editor.setCursor(1, 6)
        return;
      }

      if (firstMount) {
        this.editor.setCursor(this.editor.lineCount(), 0);
        return
      }

      this.editor.setCursor(cursor);
    });
  }

  @Watch('global.taskList')
  onTaskListChanged() {
    const data = this.editor.getValue();
    let newData = data
    this.global.taskList.forEach((task: any) => {
      let c = task.completed ? 'x' : ' ';
      newData = newData.substr(0, task.index + 3) + c + newData.substr(task.index + 4);
    })
    if (newData !== data) {
      this.editor.setValue(newData);
    }
  }
}
</script>

<style>
/* CSS Imports */
@import '~codemirror/lib/codemirror.css';
@import '~codemirror/theme/material.css';
@import '~codemirror/addon/fold/foldgutter.css';

.CodeMirror {
  padding: 10px 0px 10px 20px;
  height: 100%;
  font-family: 'Fira Code', monospace;
}

.editor {
  background-color: #263238;
  height: 100%;
}

.cm-strong { font-size: 140%; }
.cm-header-1 { font-size: 150%; }
.cm-header-2 { font-size: 130%; }
.cm-header-3 { font-size: 120%; }
.cm-header-4 { font-size: 110%; }
.cm-header-5 { font-size: 100%; }
.cm-header-6 { font-size: 90%; }

.cm-strong, .cm-header-1, .cm-header-2, .cm-header-3, .cm-header-4, .cm-header-5, .cm-header-6 {
  color: #aaa;
}

/* Link hover effect when Cmd/Ctrl is pressed */
.CodeMirror.link-hover {
  cursor: pointer !important;
}

.CodeMirror.link-hover .cm-link {
  color: #42a5f5 !important;
  text-decoration: underline;
  cursor: pointer !important;
}

.CodeMirror.link-hover .cm-url {
  color: #42a5f5 !important;
  text-decoration: underline;
  cursor: pointer !important;
}
</style>