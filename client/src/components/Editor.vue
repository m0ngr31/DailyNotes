<template>
  <div class="editor">
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

@Component({
  props: {
    value: String
  }
})
export default class Editor extends Vue {
  public editor!: CodeMirror.Editor;
  public value!: string;

  public config: CodeMirror.EditorConfiguration = {
    tabSize: 4,
    lineNumbers: false,
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
      "Enter": "newlineAndIndentContinueMarkdownList"
    },
  };

  mounted() {
    const tagElement = <HTMLTextAreaElement>this.$refs.editor;
    this.editor = CodeMirror.fromTextArea(tagElement, this.config);

    this.editor.on('changes', _.throttle(() => {
      this.$emit('valChanged', this.editor.getValue());
    }, 500, {trailing: true, leading: false}));

    this.handleValueUpdate();
  }

  @Watch('value')
  onValueChanged() {
    this.handleValueUpdate();
  }

  public handleValueUpdate() {
    _.defer(() => {
      this.editor.setValue(this.value || '');
      this.editor.setCursor(this.editor.lineCount(), 0);
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