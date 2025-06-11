interface Toast {
	id: string;
	message: string;
	type: 'info' | 'success' | 'error' | 'warning';
	duration?: number;
}

class ToastStore {
	private toasts: Toast[] = [];
	private subscribers: Array<(toasts: Toast[]) => void> = [];

	subscribe(callback: (toasts: Toast[]) => void) {
		this.subscribers.push(callback);
		callback(this.toasts);
		
		return () => {
			const index = this.subscribers.indexOf(callback);
			if (index > -1) {
				this.subscribers.splice(index, 1);
			}
		};
	}

	private notify() {
		this.subscribers.forEach(callback => callback(this.toasts));
	}

	add(toast: Omit<Toast, 'id'>) {
		const id = Math.random().toString(36).substr(2, 9);
		const newToast: Toast = { ...toast, id };
		
		this.toasts = [...this.toasts, newToast];
		this.notify();
		
		return id;
	}

	remove(id: string) {
		this.toasts = this.toasts.filter(toast => toast.id !== id);
		this.notify();
	}

	clear() {
		this.toasts = [];
		this.notify();
	}

	// Convenience methods
	info(message: string, duration?: number) {
		return this.add({ message, type: 'info', duration });
	}

	success(message: string, duration?: number) {
		return this.add({ message, type: 'success', duration });
	}

	error(message: string, duration?: number) {
		return this.add({ message, type: 'error', duration: duration ?? 6000 });
	}

	warning(message: string, duration?: number) {
		return this.add({ message, type: 'warning', duration });
	}
}

export const toastStore = new ToastStore();

// Helper functions for easy use
export const toast = {
	info: (message: string, duration?: number) => toastStore.info(message, duration),
	success: (message: string, duration?: number) => toastStore.success(message, duration),
	error: (message: string, duration?: number) => toastStore.error(message, duration),
	warning: (message: string, duration?: number) => toastStore.warning(message, duration),
	clear: () => toastStore.clear()
};

export type { Toast };