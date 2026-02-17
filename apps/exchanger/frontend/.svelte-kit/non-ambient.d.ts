
// this file is generated — do not edit it


declare module "svelte/elements" {
	export interface HTMLAttributes<T> {
		'data-sveltekit-keepfocus'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-noscroll'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-preload-code'?:
			| true
			| ''
			| 'eager'
			| 'viewport'
			| 'hover'
			| 'tap'
			| 'off'
			| undefined
			| null;
		'data-sveltekit-preload-data'?: true | '' | 'hover' | 'tap' | 'off' | undefined | null;
		'data-sveltekit-reload'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-replacestate'?: true | '' | 'off' | undefined | null;
	}
}

export {};


declare module "$app/types" {
	export interface AppTypes {
		RouteId(): "/" | "/admin" | "/compare" | "/converter" | "/converter/multi" | "/market" | "/rates" | "/symbols";
		RouteParams(): {
			
		};
		LayoutParams(): {
			"/": Record<string, never>;
			"/admin": Record<string, never>;
			"/compare": Record<string, never>;
			"/converter": Record<string, never>;
			"/converter/multi": Record<string, never>;
			"/market": Record<string, never>;
			"/rates": Record<string, never>;
			"/symbols": Record<string, never>
		};
		Pathname(): "/" | "/admin" | "/admin/" | "/compare" | "/compare/" | "/converter" | "/converter/" | "/converter/multi" | "/converter/multi/" | "/market" | "/market/" | "/rates" | "/rates/" | "/symbols" | "/symbols/";
		ResolvedPathname(): `${"" | `/${string}`}${ReturnType<AppTypes['Pathname']>}`;
		Asset(): "/robots.txt" | string & {};
	}
}