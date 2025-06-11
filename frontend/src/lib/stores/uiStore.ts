/**
 * Global UI store for managing application-wide UI state
 */

interface UIStore {
  // Navigation state
  currentRoute: string;
  sidebarOpen: boolean;
  
  // Loading states
  globalLoading: boolean;
  
  // Modal states
  activeModal: string | null;
  
  // Toast notifications
  toasts: Toast[];
  
  // Theme
  darkMode: boolean;
  
  // Mobile detection
  isMobile: boolean;
}

interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
  persistent?: boolean;
}

class UIStoreClass {
  private store: UIStore = {
    currentRoute: '/',
    sidebarOpen: false,
    globalLoading: false,
    activeModal: null,
    toasts: [],
    darkMode: false,
    isMobile: false,
  };

  // Getters for reactive access
  get currentRoute() { return this.store.currentRoute; }
  get sidebarOpen() { return this.store.sidebarOpen; }
  get globalLoading() { return this.store.globalLoading; }
  get activeModal() { return this.store.activeModal; }
  get toasts() { return this.store.toasts; }
  get darkMode() { return this.store.darkMode; }
  get isMobile() { return this.store.isMobile; }

  // Navigation actions
  setCurrentRoute(route: string) {
    this.store.currentRoute = route;
    // Auto-close sidebar on route change for mobile
    if (this.store.isMobile) {
      this.store.sidebarOpen = false;
    }
  }

  navigateTo(path: string, pushState = true) {
    if (pushState) {
      window.history.pushState({}, '', path);
    }
    this.store.currentRoute = path;
  }

  // Sidebar actions
  toggleSidebar() {
    this.store.sidebarOpen = !this.store.sidebarOpen;
  }

  openSidebar() {
    this.store.sidebarOpen = true;
  }

  closeSidebar() {
    this.store.sidebarOpen = false;
  }

  // Loading actions
  setGlobalLoading(loading: boolean) {
    this.store.globalLoading = loading;
  }

  // Modal actions
  openModal(modalId: string) {
    this.store.activeModal = modalId;
  }

  closeModal() {
    this.store.activeModal = null;
  }

  // Toast actions
  addToast(toast: Omit<Toast, 'id'>) {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const newToast: Toast = {
      id,
      duration: 5000, // 5 seconds default
      ...toast
    };

    this.store.toasts = [...this.store.toasts, newToast];

    // Auto-remove toast after duration (unless persistent)
    if (!newToast.persistent && newToast.duration) {
      setTimeout(() => {
        this.removeToast(id);
      }, newToast.duration);
    }

    return id;
  }

  removeToast(id: string) {
    this.store.toasts = this.store.toasts.filter(toast => toast.id !== id);
  }

  clearAllToasts() {
    this.store.toasts = [];
  }

  // Theme actions
  toggleDarkMode() {
    this.store.darkMode = !this.store.darkMode;
    this.updateTheme();
  }

  setDarkMode(enabled: boolean) {
    this.store.darkMode = enabled;
    this.updateTheme();
  }

  private updateTheme() {
    if (this.store.darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
    localStorage.setItem('darkMode', this.store.darkMode.toString());
  }

  // Mobile detection
  private updateMobileStatus() {
    this.store.isMobile = window.innerWidth < 768;
  }

  // Convenience methods for toasts
  showSuccess(title: string, message?: string) {
    return this.addToast({ type: 'success', title, message });
  }

  showError(title: string, message?: string) {
    return this.addToast({ type: 'error', title, message, persistent: true });
  }

  showWarning(title: string, message?: string) {
    return this.addToast({ type: 'warning', title, message });
  }

  showInfo(title: string, message?: string) {
    return this.addToast({ type: 'info', title, message });
  }

  // Initialize UI store
  initialize() {
    // Set initial route
    this.store.currentRoute = window.location.pathname;

    // Listen for route changes
    window.addEventListener('popstate', () => {
      this.store.currentRoute = window.location.pathname;
    });

    // Load dark mode preference
    const savedDarkMode = localStorage.getItem('darkMode');
    if (savedDarkMode !== null) {
      this.store.darkMode = savedDarkMode === 'true';
    } else {
      // Detect system preference
      this.store.darkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    this.updateTheme();

    // Set up mobile detection
    this.updateMobileStatus();
    window.addEventListener('resize', () => {
      this.updateMobileStatus();
    });

    // Auto-close sidebar on route change for mobile - handled in setCurrentRoute method
  }

  // Computed getters
  get isHomePage() {
    return this.store.currentRoute === '/';
  }

  get isProjectPage() {
    return this.store.currentRoute.startsWith('/project/');
  }

  get currentProjectId() {
    const match = this.store.currentRoute.match(/^\/project\/([^\/]+)/);
    return match ? match[1] : null;
  }

  get currentProjectSection() {
    const match = this.store.currentRoute.match(/^\/project\/[^\/]+\/(.+)/);
    return match ? match[1] : 'overview';
  }
}

// Export singleton instance
export const uiStore = new UIStoreClass();