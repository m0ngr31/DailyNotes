import { reactive, watch } from 'vue';
import { getItemOrDefault, setItem } from './localstorage';

export type DirectionPreference = 'ltr' | 'rtl' | 'auto';
export type ResolvedDirection = 'ltr' | 'rtl';

const DIRECTION_STORAGE_KEY = 'dn-direction-preference';

interface DirectionState {
  preference: DirectionPreference;
  resolved: ResolvedDirection;
  autoDetectedDirection: ResolvedDirection;
}

class DirectionService {
  private state: DirectionState;

  constructor() {
    const stored = getItemOrDefault<DirectionPreference>(DIRECTION_STORAGE_KEY, 'ltr');
    const preference = stored || 'ltr';

    this.state = reactive({
      preference,
      resolved: preference === 'auto' ? 'ltr' : (preference as ResolvedDirection),
      autoDetectedDirection: 'ltr',
    });

    this.applyDirection();

    watch(
      () => this.state.preference,
      (newPref) => {
        this.state.resolved = this.resolveDirection(newPref);
        setItem(DIRECTION_STORAGE_KEY, newPref);
        this.applyDirection();
      }
    );
  }

  /**
   * Get the current direction preference (ltr/rtl/auto)
   */
  get preference(): DirectionPreference {
    return this.state.preference;
  }

  /**
   * Set the direction preference
   */
  set preference(value: DirectionPreference) {
    this.state.preference = value;
  }

  /**
   * Get the resolved direction (ltr or rtl)
   */
  get resolved(): ResolvedDirection {
    return this.state.resolved;
  }

  /**
   * Check if the current resolved direction is RTL
   */
  get isRTL(): boolean {
    return this.state.resolved === 'rtl';
  }

  /**
   * Check if the current resolved direction is LTR
   */
  get isLTR(): boolean {
    return this.state.resolved === 'ltr';
  }

  /**
   * Resolve the direction preference to actual ltr/rtl
   */
  private resolveDirection(preference: DirectionPreference): ResolvedDirection {
    if (preference === 'auto') {
      return this.state.autoDetectedDirection;
    }
    return preference;
  }

  /**
   * Update auto-detected direction based on content.
   * Call this when editor content changes.
   */
  public updateAutoDirection(content: string): void {
    const detected = this.detectDirection(content);
    this.state.autoDetectedDirection = detected;

    if (this.state.preference === 'auto') {
      this.state.resolved = detected;
      this.applyDirection();
    }
  }

  /**
   * Detect direction from text content using RTL Unicode ranges
   */
  private detectDirection(text: string): ResolvedDirection {
    // Strip frontmatter (between --- delimiters)
    const contentWithoutFrontmatter = this.stripFrontmatter(text);

    // Get first 200 characters of actual content
    const sample = contentWithoutFrontmatter.slice(0, 200);

    // RTL Unicode ranges:
    // - Arabic: \u0600-\u06FF, \u0750-\u077F, \u08A0-\u08FF
    // - Hebrew: \u0590-\u05FF
    // - Persian/Farsi Extended: \uFB50-\uFDFF, \uFE70-\uFEFF
    // - Syriac: \u0700-\u074F
    const rtlPattern =
      /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\u0590-\u05FF\uFB50-\uFDFF\uFE70-\uFEFF\u0700-\u074F]/g;
    const ltrPattern = /[A-Za-z\u00C0-\u024F]/g; // Latin characters

    const rtlMatches = (sample.match(rtlPattern) || []).length;
    const ltrMatches = (sample.match(ltrPattern) || []).length;

    // Return RTL if RTL characters are majority
    if (rtlMatches > 0 && rtlMatches >= ltrMatches) {
      return 'rtl';
    }
    return 'ltr';
  }

  /**
   * Strip YAML frontmatter from text
   */
  private stripFrontmatter(text: string): string {
    const frontmatterRegex = /^---\s*\n[\s\S]*?\n---\s*\n/;
    return text.replace(frontmatterRegex, '');
  }

  /**
   * Apply the current direction to the document
   */
  private applyDirection(): void {
    if (typeof document === 'undefined') return;

    const root = document.documentElement;
    const body = document.body;

    // Remove existing direction classes
    root.classList.remove('dir-ltr', 'dir-rtl');
    body.classList.remove('dir-ltr', 'dir-rtl');

    // Add current direction class
    const dirClass = `dir-${this.state.resolved}`;
    root.classList.add(dirClass);
    body.classList.add(dirClass);

    // Set dir attribute for native browser RTL support
    root.setAttribute('dir', this.state.resolved);
  }
}

// Export singleton instance
const directionService = new DirectionService();
export default directionService;
