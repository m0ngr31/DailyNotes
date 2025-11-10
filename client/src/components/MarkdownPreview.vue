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
    <div class="preview-content" v-html="renderedMarkdown" @click="handleCheckboxClick"></div>
  </div>
</template>

<script lang="ts">
import { Vue, Component, Prop, Watch } from 'vue-property-decorator';
import { marked } from 'marked';

interface CheckboxInfo {
  lineIndex: number;
  checkboxIndex: number;
}

@Component
export default class MarkdownPreview extends Vue {
  @Prop({ type: String, default: '' })
  public value!: string;

  public renderedMarkdown: string = '';
  public frontmatter: Record<string, string> | null = null;
  private contentLines: string[] = [];
  private frontmatterLineCount: number = 0;

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
      this.frontmatterLineCount = 0;
      return { frontmatter: null, content: text };
    }

    const frontmatterText = match[1];
    const content = match[2];
    const frontmatter: Record<string, string> = {};

    // Calculate how many lines the frontmatter takes up (including delimiters)
    this.frontmatterLineCount = frontmatterText.split('\n').length + 2; // +2 for the --- delimiters

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
      this.contentLines = content.split('\n');

      // Parse markdown to HTML
      let html = marked.parse(content) as string;

      // Replace checkboxes with clickable versions and add data attributes
      // Marked renders checkboxes in various formats, so we need to handle all cases
      let currentCheckboxId = 0;

      // Match: <input disabled="" type="checkbox"> or <input type="checkbox" disabled> or similar
      // We'll replace them all with enabled checkboxes with data attributes
      html = html.replace(
        /<input[^>]*type="checkbox"[^>]*>/gi,
        (match) => {
          const isChecked = /checked/i.test(match);
          const dataAttr = `data-checkbox-id="${currentCheckboxId}"`;
          currentCheckboxId++;
          // Return checkbox without disabled attribute
          return `<input type="checkbox" ${isChecked ? 'checked' : ''} ${dataAttr}>`;
        }
      );

      // Ensure task list items have proper class
      html = html.replace(
        /<li>\s*<input type="checkbox"/gi,
        '<li class="task-list-item"><input type="checkbox"'
      );

      // Make all links open in a new tab/window
      html = html.replace(
        /<a href=/gi,
        '<a target="_blank" rel="noopener noreferrer" href='
      );

      this.renderedMarkdown = html;
    } catch (e) {
      console.error('Error rendering markdown:', e);
      this.renderedMarkdown = '<p>Error rendering markdown preview</p>';
    }
  }

  handleCheckboxClick(event: Event) {
    const target = event.target as HTMLElement;

    // Check if the clicked element is a checkbox
    if (target.tagName !== 'INPUT' || (target as HTMLInputElement).type !== 'checkbox') {
      return;
    }

    event.preventDefault();
    event.stopPropagation();

    const checkbox = target as HTMLInputElement;
    const checkboxId = parseInt(checkbox.getAttribute('data-checkbox-id') || '-1', 10);

    if (checkboxId === -1) {
      return;
    }

    // Find which line and position this checkbox is on
    const checkboxInfo = this.findCheckboxPosition(checkboxId);

    if (checkboxInfo === null) {
      return;
    }

    // Toggle the checkbox in the markdown
    const updatedMarkdown = this.toggleCheckboxInMarkdown(checkboxInfo);

    // Emit the updated markdown to parent
    this.$emit('checkbox-toggled', updatedMarkdown);
  }

  findCheckboxPosition(checkboxId: number): CheckboxInfo | null {
    let currentCheckboxId = 0;

    for (let lineIndex = 0; lineIndex < this.contentLines.length; lineIndex++) {
      const line = this.contentLines[lineIndex];
      const checkboxRegex = /- \[([ xX])\]/g;
      let match;
      let checkboxIndexOnLine = 0;

      while ((match = checkboxRegex.exec(line)) !== null) {
        if (currentCheckboxId === checkboxId) {
          return {
            lineIndex,
            checkboxIndex: checkboxIndexOnLine
          };
        }
        currentCheckboxId++;
        checkboxIndexOnLine++;
      }
    }

    return null;
  }

  toggleCheckboxInMarkdown(checkboxInfo: CheckboxInfo): string {
    const { lineIndex, checkboxIndex } = checkboxInfo;
    const line = this.contentLines[lineIndex];

    // Find the specific checkbox on this line
    const checkboxRegex = /- \[([ xX])\]/g;
    let match;
    let currentIndex = 0;
    let updatedLine = line;

    while ((match = checkboxRegex.exec(line)) !== null) {
      if (currentIndex === checkboxIndex) {
        // Toggle the checkbox
        const currentState = match[1].toLowerCase();
        const newState = currentState === 'x' ? ' ' : 'x';
        const before = line.substring(0, match.index);
        const after = line.substring(match.index + match[0].length);
        updatedLine = `${before}- [${newState}]${after}`;
        break;
      }
      currentIndex++;
    }

    // Reconstruct the full markdown
    const updatedContentLines = [...this.contentLines];
    updatedContentLines[lineIndex] = updatedLine;

    // Add frontmatter back if it exists
    if (this.frontmatter && Object.keys(this.frontmatter).length > 0) {
      const frontmatterText = Object.entries(this.frontmatter)
        .map(([key, value]) => `${key}: ${value}`)
        .join('\n');
      return `---\n${frontmatterText}\n---\n${updatedContentLines.join('\n')}`;
    }

    return updatedContentLines.join('\n');
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
  cursor: pointer;
}

.preview-content >>> .task-list-item input[type="checkbox"]:hover {
  transform: scale(1.1);
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
