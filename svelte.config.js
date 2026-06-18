import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	compilerOptions: {
		runes: ({ filename }) =>
			filename.split(/[/\\]/).includes('node_modules') ? undefined : true
	},
	kit: {
		adapter: adapter({
			pages: 'build',
			assets: 'build',
			fallback: undefined,
			precompress: true,
			strict: false
		}),
		prerender: { entries: ['*'], handleHttpError: 'warn' },
		paths: { base: process.env.BASE_PATH ?? '/course-2-stades-2026' }
	}
};

export default config;
