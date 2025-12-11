<template>
  <div class="nested-tags">
    <!-- Root level: flat tags inline, parent tags with children below -->
    <div v-if="depth === 0" class="root-level">
      <!-- Flat tags (no children) displayed inline -->
      <div v-if="flatNodes.length > 0" class="flat-tags">
        <b-tag
          v-for="node in flatNodes"
          :key="node.fullPath"
          :ellipsis="true"
          type="is-info"
          class="tag-chip"
          @click="handleTagClick(node)"
        >
          {{ node.name }}
        </b-tag>
      </div>

      <!-- Parent tags with collapsible children -->
      <div v-for="node in parentNodes" :key="node.fullPath" class="parent-node">
        <div class="parent-row">
          <span class="toggle-icon" @click="toggleExpanded(node.fullPath)">
            <i :class="isExpanded(node.fullPath) ? 'fas fa-chevron-down' : 'fas fa-chevron-right'"></i>
          </span>
          <b-tag
            :ellipsis="true"
            type="is-info"
            class="tag-chip is-parent"
            @click="handleTagClick(node)"
          >
            {{ node.name }}
          </b-tag>
        </div>

        <!-- Children displayed inline when expanded -->
        <div v-if="isExpanded(node.fullPath)" class="children-inline">
          <NestedTags :nodes="node.children" :depth="depth + 1" @tag-click="$emit('tag-click', $event)" @expanded-change="onChildExpandedChange" />
        </div>
      </div>
    </div>

    <!-- Nested levels: all tags inline with recursive expansion for sub-parents -->
    <div v-else class="nested-level">
      <!-- Flat children inline -->
      <b-tag
        v-for="node in flatNodes"
        :key="node.fullPath"
        :ellipsis="true"
        type="is-info"
        class="tag-chip"
        @click="handleTagClick(node)"
      >
        {{ node.name }}
      </b-tag>

      <!-- Sub-parent nodes (have their own children) -->
      <span v-for="node in parentNodes" :key="node.fullPath" class="sub-parent">
        <span class="toggle-icon-inline" @click="toggleExpanded(node.fullPath)">
          <i :class="isExpanded(node.fullPath) ? 'fas fa-chevron-down' : 'fas fa-chevron-right'"></i>
        </span>
        <b-tag
          :ellipsis="true"
          type="is-info"
          class="tag-chip is-parent"
          @click="handleTagClick(node)"
        >
          {{ node.name }}
        </b-tag>
        <span v-if="isExpanded(node.fullPath)" class="sub-children">
          <NestedTags :nodes="node.children" :depth="depth + 1" @tag-click="$emit('tag-click', $event)" @expanded-change="onChildExpandedChange" />
        </span>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import type { ITagNode } from '../interfaces';
import { getExpandedTags, saveExpandedTags } from '../services/localstorage';

const props = defineProps<{
  nodes: ITagNode[];
  depth?: number;
}>();

const emit = defineEmits<{
  (e: 'tag-click', fullPath: string): void;
  (e: 'expanded-change', expanded: string[]): void;
}>();

const depth = props.depth ?? 0;

// Separate flat nodes (no children) from parent nodes (have children)
const flatNodes = computed(() => props.nodes.filter((n) => n.children.length === 0));
const parentNodes = computed(() => props.nodes.filter((n) => n.children.length > 0));

// Track expanded state for parent nodes
const expandedNodes = ref<Set<string>>(new Set());

// Load saved state from localStorage (only at root level)
if (depth === 0) {
  const saved = getExpandedTags();
  saved.forEach((tag) => expandedNodes.value.add(tag));
}

function isExpanded(fullPath: string): boolean {
  return expandedNodes.value.has(fullPath);
}

function toggleExpanded(fullPath: string): void {
  if (expandedNodes.value.has(fullPath)) {
    expandedNodes.value.delete(fullPath);
  } else {
    expandedNodes.value.add(fullPath);
  }
  // Persist to localStorage (only at root level)
  if (depth === 0) {
    saveExpandedTags(Array.from(expandedNodes.value));
  } else {
    // Emit to parent to save
    emit('expanded-change', Array.from(expandedNodes.value));
  }
}

function handleTagClick(node: ITagNode): void {
  emit('tag-click', node.fullPath);
}

// Handle expanded changes from children
function onChildExpandedChange(childExpanded: string[]) {
  childExpanded.forEach((tag) => expandedNodes.value.add(tag));
  if (depth === 0) {
    saveExpandedTags(Array.from(expandedNodes.value));
  } else {
    emit('expanded-change', Array.from(expandedNodes.value));
  }
}
</script>

<style scoped>
.nested-tags {
  display: flex;
  flex-direction: column;
}

/* Root level layout */
.root-level {
  display: flex;
  flex-direction: column;
  gap: 0.5em;
}

.flat-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35em;
}

.parent-node {
  display: flex;
  flex-direction: column;
  gap: 0.25em;
}

.parent-row {
  display: flex;
  align-items: center;
}

.children-inline {
  padding-left: 20px;
}

/* Nested level: inline layout */
.nested-level {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35em;
  align-items: center;
}

.sub-parent {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
}

.sub-children {
  display: inline-flex;
  margin-left: 0.25em;
}

/* Toggle icons */
.toggle-icon {
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-muted);
  font-size: 0.7em;
  margin-right: 4px;
  flex-shrink: 0;
}

.toggle-icon:hover {
  color: var(--text-primary);
}

.toggle-icon-inline {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-muted);
  font-size: 0.7em;
  margin-right: 2px;
  width: 12px;
}

.toggle-icon-inline:hover {
  color: var(--text-primary);
}

/* Tag chips */
.tag-chip {
  cursor: pointer;
}

.tag-chip.is-parent {
  opacity: 0.85;
}
</style>
