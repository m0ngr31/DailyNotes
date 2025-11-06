<template>
  <div class="markdown-preview">
    <div v-if="frontmatter" class="frontmatter-card">
      <div class="frontmatter-header">Document Metadata</div>
      <div class="frontmatter-content">
        <div v-for="(value, key) in frontmatter" :key="key" class="frontmatter-item">
          <span class="frontmatter-key">{{ key }}:</span>
          <span class="frontmatter-value">{{ value }}</span>
        </div>
      </div>
    </div>
    <div class="preview-content" v-html="renderedMarkdown"></div>
  </div>
</template>

<script lang="ts">
import { Vue, Component, Prop, Watch } from 'vue-property-decorator';
import { marked } from 'marked';

@Component
export default class MarkdownPreview extends Vue {
  @Prop({ type: String, default: '' })
  public value!: string;

  public renderedMarkdown: string = '';
  public frontmatter: Record<string, string> | null = null;

  created() {
    // Configure marked for GitHub Flavored Markdown
    marked.setOptions({
      gfm: true,
      breaks: true,
    });

    this.updatePreview();
  }

  @Watch('value')
  onValueChanged() {
    this.updatePreview();
  }

  parseFrontmatter(text: string): { frontmatter: Record<string, string> | null; content: string } {
    // Check if text starts with frontmatter delimiters
    const frontmatterRegex = /^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$/;
    const match = text.match(frontmatterRegex);

    if (!match) {
      return { frontmatter: null, content: text };
    }

    const frontmatterText = match[1];
    const content = match[2];
    const frontmatter: Record<string, string> = {};

    // Parse YAML-like frontmatter (simple key: value pairs)
    const lines = frontmatterText.split('\n');
    lines.forEach(line => {
      const colonIndex = line.indexOf(':');
      if (colonIndex > 0) {
        const key = line.substring(0, colonIndex).trim();
        const value = line.substring(colonIndex + 1).trim();
        if (key && value) {
          frontmatter[key] = value;
        }
      }
    });

    return { frontmatter, content };
  }

  updatePreview() {
    try {
      // Parse frontmatter and content
      const { frontmatter, content } = this.parseFrontmatter(this.value || '');
      this.frontmatter = frontmatter;

      // Parse markdown to HTML
      let html = marked.parse(content) as string;

      // Add classes to task list items for styling
      html = html.replace(
        /<li><input (checked|disabled)? type="checkbox">/gi,
        '<li class="task-list-item"><input $1 type="checkbox">'
      );

      this.renderedMarkdown = html;
    } catch (e) {
      console.error('Error rendering markdown:', e);
      this.renderedMarkdown = '<p>Error rendering markdown preview</p>';
    }
  }
}
</script>

<style scoped>
.markdown-preview {
  background-color: #263238;
  height: 100%;
  overflow-y: auto;
  padding: 10px 20px;
  font-family: 'Fira Code', monospace;
  color: #eeffff;
}

/* Frontmatter Card */
.frontmatter-card {
  width: 100%;
  margin-bottom: 24px;
  background-color: #1e272e;
  border: 1px solid #404854;
  border-radius: 4px;
  overflow: hidden;
}

.frontmatter-header {
  background-color: #2a3642;
  padding: 10px 16px;
  font-weight: bold;
  font-size: 0.9em;
  color: #82aaff;
  border-bottom: 1px solid #404854;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.frontmatter-content {
  padding: 12px 16px;
}

.frontmatter-item {
  margin-bottom: 8px;
  display: flex;
  align-items: baseline;
}

.frontmatter-item:last-child {
  margin-bottom: 0;
}

.frontmatter-key {
  color: #c792ea;
  font-weight: 600;
  min-width: 100px;
  margin-right: 12px;
  font-size: 0.9em;
}

.frontmatter-value {
  color: #c3e88d;
  flex: 1;
  word-break: break-word;
}

.preview-content {
  width: 100%;
}

/* Headings */
.preview-content >>> h1 {
  font-size: 2em;
  font-weight: bold;
  margin-top: 0.67em;
  margin-bottom: 0.67em;
  color: #aaa;
  border-bottom: 1px solid #404854;
  padding-bottom: 0.3em;
}

.preview-content >>> h2 {
  font-size: 1.5em;
  font-weight: bold;
  margin-top: 0.83em;
  margin-bottom: 0.83em;
  color: #aaa;
  border-bottom: 1px solid #404854;
  padding-bottom: 0.3em;
}

.preview-content >>> h3 {
  font-size: 1.3em;
  font-weight: bold;
  margin-top: 1em;
  margin-bottom: 1em;
  color: #aaa;
}

.preview-content >>> h4 {
  font-size: 1.1em;
  font-weight: bold;
  margin-top: 1.33em;
  margin-bottom: 1.33em;
  color: #aaa;
}

.preview-content >>> h5 {
  font-size: 1em;
  font-weight: bold;
  margin-top: 1.67em;
  margin-bottom: 1.67em;
  color: #aaa;
}

.preview-content >>> h6 {
  font-size: 0.9em;
  font-weight: bold;
  margin-top: 2.33em;
  margin-bottom: 2.33em;
  color: #aaa;
}

/* Paragraphs */
.preview-content >>> p {
  margin-top: 0;
  margin-bottom: 16px;
  line-height: 1.6;
}

/* Links */
.preview-content >>> a {
  color: #82aaff;
  text-decoration: none;
}

.preview-content >>> a:hover {
  text-decoration: underline;
}

/* Lists */
.preview-content >>> ul {
  padding-left: 2em;
  margin-top: 0;
  margin-bottom: 16px;
  list-style-type: disc;
}

.preview-content >>> ol {
  padding-left: 2em;
  margin-top: 0;
  margin-bottom: 16px;
  list-style-type: decimal;
}

.preview-content >>> ul ul {
  list-style-type: circle;
  margin-bottom: 0;
}

.preview-content >>> ul ul ul {
  list-style-type: square;
}

.preview-content >>> li {
  margin-bottom: 0.25em;
  display: list-item;
}

/* Task lists */
.preview-content >>> .task-list-item {
  list-style-type: none;
  margin-left: -1.5em;
}

.preview-content >>> .task-list-item input[type="checkbox"] {
  margin-right: 0.5em;
  vertical-align: middle;
}

/* Code blocks */
.preview-content >>> pre {
  background-color: #1e272e;
  border: 1px solid #404854;
  border-radius: 3px;
  padding: 16px;
  overflow: auto;
  margin-bottom: 16px;
}

.preview-content >>> code {
  background-color: #1e272e;
  border-radius: 3px;
  padding: 2px 4px;
  font-family: 'Fira Code', monospace;
  color: #c3e88d;
}

.preview-content >>> pre code {
  background-color: transparent;
  padding: 0;
  border-radius: 0;
}

/* Blockquotes */
.preview-content >>> blockquote {
  border-left: 4px solid #82aaff;
  padding-left: 16px;
  margin-left: 0;
  margin-bottom: 16px;
  color: #b0bec5;
}

/* Tables */
.preview-content >>> table {
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 16px;
}

.preview-content >>> table th,
.preview-content >>> table td {
  border: 1px solid #404854;
  padding: 8px 12px;
  text-align: left;
}

.preview-content >>> table th {
  background-color: #1e272e;
  font-weight: bold;
}

.preview-content >>> table tr:nth-child(even) {
  background-color: #2a3642;
}

/* Horizontal rule */
.preview-content >>> hr {
  border: 0;
  border-top: 2px solid #404854;
  margin: 24px 0;
}

/* Images */
.preview-content >>> img {
  max-width: 100%;
  height: auto;
  margin-bottom: 16px;
}

/* Strong/Bold */
.preview-content >>> strong {
  font-weight: bold;
  color: #aaa;
  font-size: 1.1em;
}

/* Emphasis/Italic */
.preview-content >>> em {
  font-style: italic;
}

/* Strikethrough */
.preview-content >>> del {
  text-decoration: line-through;
  opacity: 0.7;
}
</style>
