import { render, screen, waitFor } from '@testing-library/svelte';
import { setVaultParams } from '$tests/helpers';
import { makeContactRelationship, makeRelationshipType, makeContact } from '$tests/fixtures';
import RelationshipsSection from './RelationshipsSection.svelte';

const mockListRelationships = vi.fn();
const mockCreateRelationship = vi.fn();
const mockDeleteRelationship = vi.fn();
const mockListRelTypes = vi.fn();
const mockGetContact = vi.fn();

vi.mock('$api/contacts', () => ({
	contactsApi: {
		listRelationships: (...args: unknown[]) => mockListRelationships(...args),
		createRelationship: (...args: unknown[]) => mockCreateRelationship(...args),
		deleteRelationship: (...args: unknown[]) => mockDeleteRelationship(...args),
		get: (...args: unknown[]) => mockGetContact(...args)
	},
	relationshipTypesApi: {
		list: (...args: unknown[]) => mockListRelTypes(...args)
	}
}));

vi.mock('$api/client', () => ({
	api: { get: vi.fn() }
}));

vi.mock('lucide-svelte', () => ({
	Plus: () => {},
	Trash2: () => {},
	Users: () => {}
}));

vi.mock('$components/ui/Button.svelte', () => ({ default: () => {} }));

beforeEach(() => {
	setVaultParams('vault-1', { contactId: 'contact-1' });
	mockListRelationships.mockReset();
	mockCreateRelationship.mockReset();
	mockDeleteRelationship.mockReset();
	mockListRelTypes.mockReset();
	mockGetContact.mockReset();
});

describe('RelationshipsSection', () => {
	it('renders items from API', async () => {
		const relType = makeRelationshipType({ id: 'rt-1', name: 'Friend' });
		const other = makeContact({ id: 'c-2', first_name: 'Alice', last_name: 'Smith' });
		const rel = makeContactRelationship({
			other_contact_id: 'c-2',
			relationship_type_id: 'rt-1'
		});

		mockListRelationships.mockResolvedValue([rel]);
		mockListRelTypes.mockResolvedValue([relType]);
		mockGetContact.mockResolvedValue(other);

		render(RelationshipsSection, { vaultId: 'vault-1', contactId: 'contact-1' });

		await waitFor(() => {
			expect(screen.getByText('Alice Smith')).toBeInTheDocument();
			expect(screen.getByText('(Friend)')).toBeInTheDocument();
		});
	});

	it('shows empty state when no items', async () => {
		mockListRelationships.mockResolvedValue([]);
		mockListRelTypes.mockResolvedValue([]);

		render(RelationshipsSection, { vaultId: 'vault-1', contactId: 'contact-1' });

		await waitFor(() => {
			expect(screen.getByText('No relationships yet')).toBeInTheDocument();
		});
	});

	it('has add button', async () => {
		mockListRelationships.mockResolvedValue([]);
		mockListRelTypes.mockResolvedValue([]);

		render(RelationshipsSection, { vaultId: 'vault-1', contactId: 'contact-1' });

		await waitFor(() => {
			expect(screen.getByRole('button')).toBeInTheDocument();
		});
	});
});
