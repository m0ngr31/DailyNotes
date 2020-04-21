<template>
  <div class="editor" @click="prevent($event)">
    <textarea ref="editor"></textarea>
  </div>
</template>

<script lang="ts">
import { Vue, Component, Watch } from 'vue-property-decorator';
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

import {newNote, newDay} from '../services/consts';
import eventHub from '../services/eventHub';

@Component({
  props: {
    value: String
  }
})
export default class Editor extends Vue {
  public editor!: CodeMirror.Editor;
  public value!: string;

  public config: CodeMirror.EditorConfiguration = {
    tabSize: 2,
    lineNumbers: false,
    lineWrapping: true,
    mode: {
      name: "yaml-frontmatter",
      tokenTypeOverrides: {
        emoji: "emoji"
      }
    },
    theme: 'material',
    autofocus: true,
    autoCloseBrackets: true,
    extraKeys: {
      'Enter': 'newlineAndIndentContinueMarkdownList',
      'Ctrl-S': () => this.save(),
    },
  };

  mounted() {
    const tagElement = <HTMLTextAreaElement>this.$refs.editor;
    this.editor = CodeMirror.fromTextArea(tagElement, this.config);

    this.editor.on('changes', _.throttle(() => {
      this.$emit('valChanged', this.editor.getValue());
    }, 500, {trailing: true, leading: false}));

    this.handleValueUpdate(true);
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

  @Watch('value')
  onValueChanged() {
    this.handleValueUpdate();
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
}
</script>

<style>
/* CSS Imports */
@import '~codemirror/lib/codemirror.css';
@import '~codemirror/theme/material.css';

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
</style>