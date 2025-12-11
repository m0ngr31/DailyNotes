import { reactive, watch } from 'vue';
import { getItemOrDefault, setItem } from './localstorage';

export type ThemePreference = 'light' | 'dark' | 'system';
export type ResolvedTheme = 'light' | 'dark';

const THEME_STORAGE_KEY = 'dn-theme-preference';

interface ThemeState {
  preference: ThemePreference;
  resolved: ResolvedTheme;
}

class ThemeService {
  private state: ThemeState;
  private mediaQuery: MediaQueryList | null = null;

  constructor() {
    // Initialize with stored preference or default to 'system'
    const stored = getItemOrDefault<ThemePreference>(THEME_STORAGE_KEY, 'system');
    const preference = stored || 'system';

    this.state = reactive({
      preference,
      resolved: this.resolveTheme(preference),
    });

    // Set up system preference listener
    if (typeof window !== 'undefined' && window.matchMedia) {
      this.mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      this.mediaQuery.addEventListener('change', this.handleSystemChange);
    }

    // Apply theme on initialization
    this.applyTheme();

    // Watch for preference changes
    watch(
      () => this.state.preference,
      (newPref) => {
        this.state.resolved = this.resolveTheme(newPref);
        setItem(THEME_STORAGE_KEY, newPref);
        this.applyTheme();
      }
    );
  }

  /**
   * Get the current theme preference (light/dark/system)
   */
  get preference(): ThemePreference {
    return this.state.preference;
  }

  /**
   * Set the theme preference
   */
  set preference(value: ThemePreference) {
    this.state.preference = value;
  }

  /**
   * Get the resolved theme (light or dark)
   */
  get resolved(): ResolvedTheme {
    return this.state.resolved;
  }

  /**
   * Check if the current resolved theme is dark
   */
  get isDark(): boolean {
    return this.state.resolved === 'dark';
  }

  /**
   * Check if the current resolved theme is light
   */
  get isLight(): boolean {
    return this.state.resolved === 'light';
  }

  /**
   * Resolve the theme preference to actual light/dark
   */
  private resolveTheme(preference: ThemePreference): ResolvedTheme {
    if (preference === 'system') {
      return this.getSystemPreference();
    }
    return preference;
  }

  /**
   * Get the system color scheme preference
   */
  private getSystemPreference(): ResolvedTheme {
    if (typeof window !== 'undefined' && window.matchMedia) {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return 'dark'; // Default to dark if can't detect
  }

  /**
   * Handle system preference changes
   */
  private handleSystemChange = () => {
    if (this.state.preference === 'system') {
      this.state.resolved = this.getSystemPreference();
      this.applyTheme();
    }
  };

  /**
   * Apply the current theme to the document
   */
  private applyTheme() {
    if (typeof document === 'undefined') return;

    const root = document.documentElement;
    const body = document.body;

    // Remove existing theme classes
    root.classList.remove('theme-light', 'theme-dark');
    body.classList.remove('theme-light', 'theme-dark');

    // Add current theme class
    const themeClass = `theme-${this.state.resolved}`;
    root.classList.add(themeClass);
    body.classList.add(themeClass);

    // Update color-scheme for native elements
    root.style.colorScheme = this.state.resolved;
  }

  /**
   * Toggle between light and dark (ignores system)
   */
  public toggle() {
    if (this.state.resolved === 'dark') {
      this.preference = 'light';
    } else {
      this.preference = 'dark';
    }
  }

  /**
   * Cycle through themes: light -> dark -> system -> light
   */
  public cycle() {
    const order: ThemePreference[] = ['light', 'dark', 'system'];
    const currentIndex = order.indexOf(this.state.preference);
    const nextIndex = (currentIndex + 1) % order.length;
    this.preference = order[nextIndex];
  }

  /**
   * Clean up event listeners
   */
  public destroy() {
    if (this.mediaQuery) {
      this.mediaQuery.removeEventListener('change', this.handleSystemChange);
    }
  }
}

// Export singleton instance
const themeService = new ThemeService();
export default themeService;
