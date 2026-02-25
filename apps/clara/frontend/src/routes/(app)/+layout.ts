import { redirect } from '@sveltejs/kit';
import { auth } from '$state/auth.svelte';
import type { LayoutLoad } from './$types';

export const load: LayoutLoad = async () => {
  if (auth.loading) {
    await auth.fetchMe();
  }

  if (!auth.isAuthenticated) {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('clara_redirect', window.location.pathname);
    }
    redirect(302, '/auth/login');
  }
};
