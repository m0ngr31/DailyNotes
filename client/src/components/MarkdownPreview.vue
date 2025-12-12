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

<script setup lang="ts">
import { marked } from 'marked';
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue';
import themeService from '@/services/theme';

interface CheckboxInfo {
  lineIndex: number;
  checkboxIndex: number;
}

interface Props {
  value: string;
}

const props = withDefaults(defineProps<Props>(), {
  value: '',
});

const emit = defineEmits<{
  'checkbox-toggled': [value: string];
}>();

const renderedMarkdown = ref('');
const frontmatter = ref<Record<string, string> | null>(null);
const contentLines = ref<string[]>([]);
const frontmatterLineCount = ref(0);

// Mermaid lazy loading
let mermaidInstance: typeof import('mermaid').default | null = null;
let mermaidLoadPromise: Promise<typeof import('mermaid').default> | null = null;
let mermaidIdCounter = 0;

const loadMermaid = async () => {
  if (mermaidInstance) return mermaidInstance;
  if (mermaidLoadPromise) return mermaidLoadPromise;

  mermaidLoadPromise = import('mermaid').then((m) => {
    mermaidInstance = m.default;
    // Initialize with theme based on current app theme
    mermaidInstance.initialize({
      startOnLoad: false,
      theme: themeService.isDark ? 'dark' : 'default',
      securityLevel: 'strict',
      fontFamily: 'Fira Code, monospace',
    });
    return mermaidInstance;
  });

  return mermaidLoadPromise;
};

const renderMermaidDiagrams = async () => {
  // Find all mermaid code blocks in the rendered content
  const container = document.querySelector('.preview-content');
  if (!container) return;

  const mermaidBlocks = container.querySelectorAll('pre > code.language-mermaid');
  if (mermaidBlocks.length === 0) return;

  // Lazy load mermaid
  const mermaid = await loadMermaid();

  // Update mermaid theme based on current app theme
  mermaid.initialize({
    startOnLoad: false,
    theme: themeService.isDark ? 'dark' : 'default',
    securityLevel: 'strict',
    fontFamily: 'Fira Code, monospace',
  });

  for (const block of mermaidBlocks) {
    const code = block.textContent || '';
    const preElement = block.parentElement;

    if (!preElement) continue;

    try {
      // Generate unique ID for this diagram
      const id = `mermaid-diagram-${mermaidIdCounter++}`;

      // Render the diagram
      const { svg } = await mermaid.render(id, code);

      // Create a wrapper div with the rendered SVG
      const wrapper = document.createElement('div');
      wrapper.className = 'mermaid-diagram';
      wrapper.innerHTML = svg;

      // Replace the pre element with the rendered diagram
      preElement.replaceWith(wrapper);
    } catch (error) {
      // Show error message in place of the diagram
      const errorDiv = document.createElement('div');
      errorDiv.className = 'mermaid-error';
      errorDiv.innerHTML = `<strong>Mermaid Error:</strong> ${error instanceof Error ? error.message : 'Failed to render diagram'}`;
      preElement.replaceWith(errorDiv);
    }
  }
};

// Watch for theme changes to re-render mermaid diagrams
const themeWatcherCleanup = watch(
  () => themeService.resolved,
  () => {
    // Re-render to pick up new theme
    updatePreview();
  }
);

onMounted(() => {
  // Configure marked for GitHub Flavored Markdown
  marked.setOptions({
    gfm: true,
    breaks: true,
  });

  updatePreview();
});

onUnmounted(() => {
  // Clean up theme watcher
  themeWatcherCleanup();
});

watch(
  () => props.value,
  () => {
    updatePreview();
  }
);

const parseFrontmatter = (
  text: string
): { frontmatter: Record<string, string> | null; content: string } => {
  // Check if text starts with frontmatter delimiters
  const frontmatterRegex = /^---\s*\n([\s\S]*?)\n---\s*\n([\s\S]*)$/;
  const match = text.match(frontmatterRegex);

  if (!match) {
    frontmatterLineCount.value = 0;
    return { frontmatter: null, content: text };
  }

  const frontmatterText = match[1];
  const content = match[2];
  const fm: Record<string, string> = {};

  // Calculate how many lines the frontmatter takes up (including delimiters)
  frontmatterLineCount.value = frontmatterText.split('\n').length + 2; // +2 for the --- delimiters

  // Parse YAML-like frontmatter (simple key: value pairs)
  const lines = frontmatterText.split('\n');
  lines.forEach((line) => {
    const colonIndex = line.indexOf(':');
    if (colonIndex > 0) {
      const key = line.substring(0, colonIndex).trim();
      const value = line.substring(colonIndex + 1).trim();
      if (key && value) {
        fm[key] = value;
      }
    }
  });

  return { frontmatter: fm, content };
};

const updatePreview = () => {
  try {
    // Parse frontmatter and content
    const parsed = parseFrontmatter(props.value || '');
    frontmatter.value = parsed.frontmatter;
    contentLines.value = parsed.content.split('\n');

    // Parse markdown to HTML
    let html = marked.parse(parsed.content) as string;

    // Replace checkboxes with clickable versions and add data attributes
    // Marked renders checkboxes in various formats, so we need to handle all cases
    let currentCheckboxId = 0;

    // Match: <input disabled="" type="checkbox"> or <input type="checkbox" disabled> or similar
    // We'll replace them all with enabled checkboxes with data attributes
    html = html.replace(/<input[^>]*type="checkbox"[^>]*>/gi, (match) => {
      const isChecked = /checked/i.test(match);
      const dataAttr = `data-checkbox-id="${currentCheckboxId}"`;
      currentCheckboxId++;
      // Return checkbox without disabled attribute
      return `<input type="checkbox" ${isChecked ? 'checked' : ''} ${dataAttr}>`;
    });

    // Ensure task list items have proper class
    html = html.replace(
      /<li>\s*<input type="checkbox"/gi,
      '<li class="task-list-item"><input type="checkbox"'
    );

    // Make all links open in a new tab/window
    html = html.replace(/<a href=/gi, '<a target="_blank" rel="noopener noreferrer" href=');

    renderedMarkdown.value = html;

    // Render mermaid diagrams after DOM update
    nextTick(() => {
      renderMermaidDiagrams();
    });
  } catch (e) {
    console.error('Error rendering markdown:', e);
    renderedMarkdown.value = '<p>Error rendering markdown preview</p>';
  }
};

const handleCheckboxClick = (event: Event) => {
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
  const checkboxInfo = findCheckboxPosition(checkboxId);

  if (checkboxInfo === null) {
    return;
  }

  // Toggle the checkbox in the markdown
  const updatedMarkdown = toggleCheckboxInMarkdown(checkboxInfo);

  // Emit the updated markdown to parent
  emit('checkbox-toggled', updatedMarkdown);
};

const findCheckboxPosition = (checkboxId: number): CheckboxInfo | null => {
  let currentCheckboxId = 0;

  for (let lineIndex = 0; lineIndex < contentLines.value.length; lineIndex++) {
    const line = contentLines.value[lineIndex];
    const checkboxRegex = /- \[([ xX])\]/g;
    let match: RegExpExecArray | null;
    let checkboxIndexOnLine = 0;

    match = checkboxRegex.exec(line);
    while (match !== null) {
      if (currentCheckboxId === checkboxId) {
        return {
          lineIndex,
          checkboxIndex: checkboxIndexOnLine,
        };
      }
      currentCheckboxId++;
      checkboxIndexOnLine++;
      match = checkboxRegex.exec(line);
    }
  }

  return null;
};

const toggleCheckboxInMarkdown = (checkboxInfo: CheckboxInfo): string => {
  const { lineIndex, checkboxIndex } = checkboxInfo;
  const line = contentLines.value[lineIndex];

  // Find the specific checkbox on this line
  const checkboxRegex = /- \[([ xX])\]/g;
  let match: RegExpExecArray | null;
  let currentIndex = 0;
  let updatedLine = line;

  match = checkboxRegex.exec(line);
  while (match !== null) {
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
    match = checkboxRegex.exec(line);
  }

  // Reconstruct the full markdown
  const updatedContentLines = [...contentLines.value];
  updatedContentLines[lineIndex] = updatedLine;

  // Add frontmatter back if it exists
  if (frontmatter.value && Object.keys(frontmatter.value).length > 0) {
    const frontmatterText = Object.entries(frontmatter.value)
      .map(([key, value]) => `${key}: ${value}`)
      .join('\n');
    return `---\n${frontmatterText}\n---\n${updatedContentLines.join('\n')}`;
  }

  return updatedContentLines.join('\n');
};
</script>

<style scoped>
.markdown-preview {
  background-color: var(--editor-bg);
  height: 100%;
  overflow-y: auto;
  padding: 10px 20px;
  font-family: 'Fira Code', monospace;
  color: var(--text-primary);
  transition: background-color 0.2s ease, color 0.2s ease;
}

/* Frontmatter Card */
.frontmatter-card {
  width: 100%;
  margin-bottom: 24px;
  background-color: var(--code-bg);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  overflow: hidden;
}

.frontmatter-header {
  background-color: var(--card-bg);
  padding: 10px 16px;
  font-weight: bold;
  font-size: 0.9em;
  color: var(--text-link);
  border-bottom: 1px solid var(--border-color);
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
  color: var(--syntax-keyword);
  font-weight: 600;
  min-width: 100px;
  margin-inline-end: 12px;
  font-size: 0.9em;
}

.frontmatter-value {
  color: var(--syntax-string);
  flex: 1;
  word-break: break-word;
}

.preview-content {
  width: 100%;
}

/* Headings */
.preview-content :deep(h1) {
  font-size: 2em;
  font-weight: bold;
  margin-top: 0.67em;
  margin-bottom: 0.67em;
  color: var(--syntax-heading);
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0.3em;
}

.preview-content :deep(h2) {
  font-size: 1.5em;
  font-weight: bold;
  margin-top: 0.83em;
  margin-bottom: 0.83em;
  color: var(--syntax-heading);
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 0.3em;
}

.preview-content :deep(h3) {
  font-size: 1.3em;
  font-weight: bold;
  margin-top: 1em;
  margin-bottom: 1em;
  color: var(--syntax-heading);
}

.preview-content :deep(h4) {
  font-size: 1.1em;
  font-weight: bold;
  margin-top: 1.33em;
  margin-bottom: 1.33em;
  color: var(--syntax-heading);
}

.preview-content :deep(h5) {
  font-size: 1em;
  font-weight: bold;
  margin-top: 1.67em;
  margin-bottom: 1.67em;
  color: var(--syntax-heading);
}

.preview-content :deep(h6) {
  font-size: 0.9em;
  font-weight: bold;
  margin-top: 2.33em;
  margin-bottom: 2.33em;
  color: var(--syntax-heading);
}

/* Paragraphs */
.preview-content :deep(p) {
  margin-top: 0;
  margin-bottom: 16px;
  line-height: 1.6;
}

/* Links */
.preview-content :deep(a) {
  color: var(--text-link);
  text-decoration: none;
}

.preview-content :deep(a:hover) {
  text-decoration: underline;
  color: var(--text-link-hover);
}

/* Lists */
.preview-content :deep(ul) {
  padding-inline-start: 2em;
  margin-top: 0;
  margin-bottom: 16px;
  list-style-type: disc;
}

.preview-content :deep(ol) {
  padding-inline-start: 2em;
  margin-top: 0;
  margin-bottom: 16px;
  list-style-type: decimal;
}

.preview-content :deep(ul ul) {
  list-style-type: circle;
  margin-bottom: 0;
}

.preview-content :deep(ul ul ul) {
  list-style-type: square;
}

.preview-content :deep(li) {
  margin-bottom: 0.25em;
  display: list-item;
}

/* Task lists */
.preview-content :deep(.task-list-item) {
  list-style-type: none;
  margin-inline-start: -1.5em;
}

.preview-content :deep(.task-list-item input[type="checkbox"]) {
  margin-inline-end: 0.5em;
  vertical-align: middle;
  cursor: pointer;
  accent-color: var(--accent-primary);
}

.preview-content :deep(.task-list-item input[type="checkbox"]:hover) {
  transform: scale(1.1);
}

/* Code blocks */
.preview-content :deep(pre) {
  background-color: var(--code-bg);
  border: 1px solid var(--border-color);
  border-radius: 3px;
  padding: 16px;
  overflow: auto;
  margin-bottom: 16px;
}

.preview-content :deep(code) {
  background-color: var(--code-bg);
  border-radius: 3px;
  padding: 2px 4px;
  font-family: 'Fira Code', monospace;
  color: var(--syntax-string);
}

.preview-content :deep(pre code) {
  background-color: transparent;
  padding: 0;
  border-radius: 0;
  color: var(--code-text);
}

/* Blockquotes */
.preview-content :deep(blockquote) {
  border-inline-start: 4px solid var(--text-link);
  padding-inline-start: 16px;
  margin-inline-start: 0;
  margin-bottom: 16px;
  color: var(--text-muted);
}

/* Tables */
.preview-content :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin-bottom: 16px;
}

.preview-content :deep(table th),
.preview-content :deep(table td) {
  border: 1px solid var(--border-color);
  padding: 8px 12px;
  text-align: start;
}

.preview-content :deep(table th) {
  background-color: var(--code-bg);
  font-weight: bold;
}

.preview-content :deep(table tr:nth-child(even)) {
  background-color: var(--card-bg);
}

/* Horizontal rule */
.preview-content :deep(hr) {
  border: 0;
  border-top: 2px solid var(--border-color);
  margin: 24px 0;
}

/* Images */
.preview-content :deep(img) {
  max-width: 100%;
  height: auto;
  margin-bottom: 16px;
}

/* Strong/Bold */
.preview-content :deep(strong) {
  font-weight: bold;
  color: var(--syntax-heading);
  font-size: 1.1em;
}

/* Emphasis/Italic */
.preview-content :deep(em) {
  font-style: italic;
}

/* Strikethrough */
.preview-content :deep(del) {
  text-decoration: line-through;
  opacity: 0.7;
}

/* Mobile styles */
@media screen and (max-width: 767px) {
  .markdown-preview {
    padding: 8px 12px;
  }

  .frontmatter-card {
    margin-bottom: 16px;
  }

  .frontmatter-header {
    padding: 8px 12px;
    font-size: 0.85em;
  }

  .frontmatter-content {
    padding: 10px 12px;
  }

  .frontmatter-key {
    min-width: 80px;
    margin-inline-end: 8px;
  }

  .preview-content :deep(pre) {
    padding: 12px;
    font-size: 0.9em;
  }

  .preview-content :deep(table th),
  .preview-content :deep(table td) {
    padding: 6px 8px;
  }
}

/* Mermaid diagrams */
.preview-content :deep(.mermaid-diagram) {
  display: flex;
  justify-content: center;
  margin: 16px 0;
  padding: 16px;
  background-color: var(--code-bg);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  overflow-x: auto;
}

.preview-content :deep(.mermaid-diagram svg) {
  max-width: 100%;
  height: auto;
}

.preview-content :deep(.mermaid-error) {
  margin: 16px 0;
  padding: 16px;
  background-color: rgba(255, 82, 82, 0.1);
  border: 1px solid #ff5252;
  border-radius: 4px;
  color: #ff5252;
  font-family: 'Fira Code', monospace;
  font-size: 0.9em;
}

.preview-content :deep(.mermaid-error strong) {
  color: #ff5252;
}
</style>
