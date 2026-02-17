
// this file is generated — do not edit it


/// <reference types="@sveltejs/kit" />

/**
 * Environment variables [loaded by Vite](https://vitejs.dev/guide/env-and-mode.html#env-files) from `.env` files and `process.env`. Like [`$env/dynamic/private`](https://svelte.dev/docs/kit/$env-dynamic-private), this module cannot be imported into client-side code. This module only includes variables that _do not_ begin with [`config.kit.env.publicPrefix`](https://svelte.dev/docs/kit/configuration#env) _and do_ start with [`config.kit.env.privatePrefix`](https://svelte.dev/docs/kit/configuration#env) (if configured).
 * 
 * _Unlike_ [`$env/dynamic/private`](https://svelte.dev/docs/kit/$env-dynamic-private), the values exported from this module are statically injected into your bundle at build time, enabling optimisations like dead code elimination.
 * 
 * ```ts
 * import { API_KEY } from '$env/static/private';
 * ```
 * 
 * Note that all environment variables referenced in your code should be declared (for example in an `.env` file), even if they don't have a value until the app is deployed:
 * 
 * ```
 * MY_FEATURE_FLAG=""
 * ```
 * 
 * You can override `.env` values from the command line like so:
 * 
 * ```sh
 * MY_FEATURE_FLAG="enabled" npm run dev
 * ```
 */
declare module '$env/static/private' {
	export const MANPATH: string;
	export const __MISE_DIFF: string;
	export const POETRY_VERSION: string;
	export const TERM_PROGRAM: string;
	export const NODE: string;
	export const INIT_CWD: string;
	export const DOTFILES_ROOT: string;
	export const TERM: string;
	export const FZF_CTRL_R_OPTS: string;
	export const SHELL: string;
	export const SYMBOLS: string;
	export const _printf_cmd: string;
	export const HISTSIZE: string;
	export const HOMEBREW_REPOSITORY: string;
	export const TMPDIR: string;
	export const npm_config_global_prefix: string;
	export const AUTOPEP8_HOME: string;
	export const TERM_PROGRAM_VERSION: string;
	export const YT_DLP_VERSION: string;
	export const GIT_HOSTING: string;
	export const PROVIDER_FCS_API_KEY: string;
	export const COLOR: string;
	export const npm_config_noproxy: string;
	export const npm_config_local_prefix: string;
	export const GIT_EDITOR: string;
	export const HISTFILESIZE: string;
	export const BLACK_HOME: string;
	export const USER: string;
	export const AUTO_BACKFILL_TIME: string;
	export const PYNVIM_VERSION: string;
	export const LS_COLORS: string;
	export const COMMAND_MODE: string;
	export const POWERLINE_PROMPT_USER_INFO_MODE: string;
	export const npm_config_globalconfig: string;
	export const BASH_IT_THEME: string;
	export const LLM_VERSION: string;
	export const BASH_IT_AUTOMATIC_RELOAD_AFTER_CONFIG_CHANGE: string;
	export const SCM_CHECK: string;
	export const SSH_AUTH_SOCK: string;
	export const __CF_USER_TEXT_ENCODING: string;
	export const RUFF_HOME: string;
	export const DENO_INSTALL_ROOT: string;
	export const npm_execpath: string;
	export const DB_PATH: string;
	export const FZF_DEFAULT_OPTS: string;
	export const DOO_CFG: string;
	export const YAPF_VERSION: string;
	export const BEETS_VERSION: string;
	export const BASH_IT: string;
	export const WEZTERM_EXECUTABLE_DIR: string;
	export const PATH: string;
	export const LLM_HOME: string;
	export const AUTOPEP8_VERSION: string;
	export const CARGO_HOME: string;
	export const npm_package_json: string;
	export const npm_config_engine_strict: string;
	export const LaunchInstanceID: string;
	export const npm_config_userconfig: string;
	export const npm_config_init_module: string;
	export const __CFBundleIdentifier: string;
	export const npm_command: string;
	export const GITA_HOME: string;
	export const PWD: string;
	export const DOOGAT_CFG: string;
	export const npm_lifecycle_event: string;
	export const EDITOR: string;
	export const npm_package_name: string;
	export const LANG: string;
	export const WEZTERM_PANE: string;
	export const YAPF_HOME: string;
	export const npm_config_npm_version: string;
	export const POETRY_HOME: string;
	export const XPC_FLAGS: string;
	export const IS_MAC: string;
	export const BLACK_VERSION: string;
	export const RUSTUP_TOOLCHAIN: string;
	export const npm_config_node_gyp: string;
	export const npm_package_version: string;
	export const XPC_SERVICE_NAME: string;
	export const WEZTERM_UNIX_SOCKET: string;
	export const HISTCONTROL: string;
	export const YT_DLP_HOME: string;
	export const GPG_TTY: string;
	export const SHLVL: string;
	export const HOME: string;
	export const __MISE_ORIG_PATH: string;
	export const BEETS_HOME: string;
	export const BASH_IT_CUSTOM: string;
	export const AUTO_BACKFILL_DAYS: string;
	export const HOMEBREW_PREFIX: string;
	export const MISE_SHELL: string;
	export const RUSTUP_HOME: string;
	export const WEZTERM_CONFIG_DIR: string;
	export const RUFF_VERSION: string;
	export const npm_config_cache: string;
	export const LOGNAME: string;
	export const npm_lifecycle_script: string;
	export const SHORT_TERM_LINE: string;
	export const FZF_DEFAULT_COMMAND: string;
	export const PYNVIM_HOME: string;
	export const BREW_PREFIX: string;
	export const npm_config_user_agent: string;
	export const TODO: string;
	export const GITA_VERSION: string;
	export const __MISE_SESSION: string;
	export const HOMEBREW_CELLAR: string;
	export const OPENFAAS_URL: string;
	export const INFOPATH: string;
	export const IRC_CLIENT: string;
	export const WEZTERM_EXECUTABLE: string;
	export const OSLogRateLimit: string;
	export const SECURITYSESSIONID: string;
	export const WEZTERM_CONFIG_FILE: string;
	export const npm_node_execpath: string;
	export const npm_config_prefix: string;
	export const COLORTERM: string;
	export const _: string;
	export const NODE_ENV: string;
}

/**
 * Similar to [`$env/static/private`](https://svelte.dev/docs/kit/$env-static-private), except that it only includes environment variables that begin with [`config.kit.env.publicPrefix`](https://svelte.dev/docs/kit/configuration#env) (which defaults to `PUBLIC_`), and can therefore safely be exposed to client-side code.
 * 
 * Values are replaced statically at build time.
 * 
 * ```ts
 * import { PUBLIC_BASE_URL } from '$env/static/public';
 * ```
 */
declare module '$env/static/public' {
	
}

/**
 * This module provides access to runtime environment variables, as defined by the platform you're running on. For example if you're using [`adapter-node`](https://github.com/sveltejs/kit/tree/main/packages/adapter-node) (or running [`vite preview`](https://svelte.dev/docs/kit/cli)), this is equivalent to `process.env`. This module only includes variables that _do not_ begin with [`config.kit.env.publicPrefix`](https://svelte.dev/docs/kit/configuration#env) _and do_ start with [`config.kit.env.privatePrefix`](https://svelte.dev/docs/kit/configuration#env) (if configured).
 * 
 * This module cannot be imported into client-side code.
 * 
 * ```ts
 * import { env } from '$env/dynamic/private';
 * console.log(env.DEPLOYMENT_SPECIFIC_VARIABLE);
 * ```
 * 
 * > [!NOTE] In `dev`, `$env/dynamic` always includes environment variables from `.env`. In `prod`, this behavior will depend on your adapter.
 */
declare module '$env/dynamic/private' {
	export const env: {
		MANPATH: string;
		__MISE_DIFF: string;
		POETRY_VERSION: string;
		TERM_PROGRAM: string;
		NODE: string;
		INIT_CWD: string;
		DOTFILES_ROOT: string;
		TERM: string;
		FZF_CTRL_R_OPTS: string;
		SHELL: string;
		SYMBOLS: string;
		_printf_cmd: string;
		HISTSIZE: string;
		HOMEBREW_REPOSITORY: string;
		TMPDIR: string;
		npm_config_global_prefix: string;
		AUTOPEP8_HOME: string;
		TERM_PROGRAM_VERSION: string;
		YT_DLP_VERSION: string;
		GIT_HOSTING: string;
		PROVIDER_FCS_API_KEY: string;
		COLOR: string;
		npm_config_noproxy: string;
		npm_config_local_prefix: string;
		GIT_EDITOR: string;
		HISTFILESIZE: string;
		BLACK_HOME: string;
		USER: string;
		AUTO_BACKFILL_TIME: string;
		PYNVIM_VERSION: string;
		LS_COLORS: string;
		COMMAND_MODE: string;
		POWERLINE_PROMPT_USER_INFO_MODE: string;
		npm_config_globalconfig: string;
		BASH_IT_THEME: string;
		LLM_VERSION: string;
		BASH_IT_AUTOMATIC_RELOAD_AFTER_CONFIG_CHANGE: string;
		SCM_CHECK: string;
		SSH_AUTH_SOCK: string;
		__CF_USER_TEXT_ENCODING: string;
		RUFF_HOME: string;
		DENO_INSTALL_ROOT: string;
		npm_execpath: string;
		DB_PATH: string;
		FZF_DEFAULT_OPTS: string;
		DOO_CFG: string;
		YAPF_VERSION: string;
		BEETS_VERSION: string;
		BASH_IT: string;
		WEZTERM_EXECUTABLE_DIR: string;
		PATH: string;
		LLM_HOME: string;
		AUTOPEP8_VERSION: string;
		CARGO_HOME: string;
		npm_package_json: string;
		npm_config_engine_strict: string;
		LaunchInstanceID: string;
		npm_config_userconfig: string;
		npm_config_init_module: string;
		__CFBundleIdentifier: string;
		npm_command: string;
		GITA_HOME: string;
		PWD: string;
		DOOGAT_CFG: string;
		npm_lifecycle_event: string;
		EDITOR: string;
		npm_package_name: string;
		LANG: string;
		WEZTERM_PANE: string;
		YAPF_HOME: string;
		npm_config_npm_version: string;
		POETRY_HOME: string;
		XPC_FLAGS: string;
		IS_MAC: string;
		BLACK_VERSION: string;
		RUSTUP_TOOLCHAIN: string;
		npm_config_node_gyp: string;
		npm_package_version: string;
		XPC_SERVICE_NAME: string;
		WEZTERM_UNIX_SOCKET: string;
		HISTCONTROL: string;
		YT_DLP_HOME: string;
		GPG_TTY: string;
		SHLVL: string;
		HOME: string;
		__MISE_ORIG_PATH: string;
		BEETS_HOME: string;
		BASH_IT_CUSTOM: string;
		AUTO_BACKFILL_DAYS: string;
		HOMEBREW_PREFIX: string;
		MISE_SHELL: string;
		RUSTUP_HOME: string;
		WEZTERM_CONFIG_DIR: string;
		RUFF_VERSION: string;
		npm_config_cache: string;
		LOGNAME: string;
		npm_lifecycle_script: string;
		SHORT_TERM_LINE: string;
		FZF_DEFAULT_COMMAND: string;
		PYNVIM_HOME: string;
		BREW_PREFIX: string;
		npm_config_user_agent: string;
		TODO: string;
		GITA_VERSION: string;
		__MISE_SESSION: string;
		HOMEBREW_CELLAR: string;
		OPENFAAS_URL: string;
		INFOPATH: string;
		IRC_CLIENT: string;
		WEZTERM_EXECUTABLE: string;
		OSLogRateLimit: string;
		SECURITYSESSIONID: string;
		WEZTERM_CONFIG_FILE: string;
		npm_node_execpath: string;
		npm_config_prefix: string;
		COLORTERM: string;
		_: string;
		NODE_ENV: string;
		[key: `PUBLIC_${string}`]: undefined;
		[key: `${string}`]: string | undefined;
	}
}

/**
 * Similar to [`$env/dynamic/private`](https://svelte.dev/docs/kit/$env-dynamic-private), but only includes variables that begin with [`config.kit.env.publicPrefix`](https://svelte.dev/docs/kit/configuration#env) (which defaults to `PUBLIC_`), and can therefore safely be exposed to client-side code.
 * 
 * Note that public dynamic environment variables must all be sent from the server to the client, causing larger network requests — when possible, use `$env/static/public` instead.
 * 
 * ```ts
 * import { env } from '$env/dynamic/public';
 * console.log(env.PUBLIC_DEPLOYMENT_SPECIFIC_VARIABLE);
 * ```
 */
declare module '$env/dynamic/public' {
	export const env: {
		[key: `PUBLIC_${string}`]: string | undefined;
	}
}
