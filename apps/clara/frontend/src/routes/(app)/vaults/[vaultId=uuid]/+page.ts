import { redirect } from '@sveltejs/kit';

export const load = ({ params }: { params: { vaultId: string } }) => {
	redirect(302, `/vaults/${params.vaultId}/dashboard`);
};
