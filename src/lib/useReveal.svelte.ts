export function reveal(el: HTMLElement, options?: { onReveal?: () => void }) {
	let revealed = false;

	const observer = new IntersectionObserver(
		(entries) => {
			for (const entry of entries) {
				if (entry.isIntersecting && !revealed) {
					revealed = true;
					el.dataset.revealed = 'true';
					options?.onReveal?.();
					observer.disconnect();
				}
			}
		},
		{ threshold: 0.2 }
	);

	observer.observe(el);

	return {
		destroy() {
			observer.disconnect();
		}
	};
}

export class Counter {
	value = $state(0);
	private raf = 0;

	run(target: number, startFrom = 0) {
		cancelAnimationFrame(this.raf);
		const span = Math.abs(target - startFrom);
		const duration = Math.min(1800, Math.max(700, Math.log10(span + 1) * 500));
		const start = performance.now();

		const tick = (now: number) => {
			const t = Math.min(1, (now - start) / duration);
			const ease = 1 - (1 - t) ** 3;
			this.value = startFrom + (target - startFrom) * ease;
			if (t < 1) this.raf = requestAnimationFrame(tick);
		};

		this.raf = requestAnimationFrame(tick);
	}

	stop() {
		cancelAnimationFrame(this.raf);
	}
}
