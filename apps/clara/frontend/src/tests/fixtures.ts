import type {
  User,
  Vault,
  Contact,
  ContactMethod,
  Address,
  Pet,
  Tag,
  Task,
  Activity,
  ActivityType,
  JournalEntry,
  Reminder,
  Gift,
  Debt,
  Note,
  FileRecord,
  ContactRelationship,
  RelationshipType
} from '$lib/types/models';

let seq = 0;
function uuid(): string {
  seq++;
  return `00000000-0000-0000-0000-${String(seq).padStart(12, '0')}`;
}

const now = '2026-01-15T12:00:00Z';
const VAULT_ID = '00000000-0000-0000-0000-000000000001';

export function makeUser(overrides?: Partial<User>): User {
  const id = uuid();
  return {
    id,
    email: `user-${id.slice(-4)}@test.com`,
    name: 'Test User',
    is_active: true,
    default_vault_id: VAULT_ID,
    created_at: now,
    ...overrides
  };
}

export function makeVault(overrides?: Partial<Vault>): Vault {
  return {
    id: uuid(),
    name: 'Test Vault',
    created_at: now,
    ...overrides
  };
}

export function makeContact(overrides?: Partial<Contact>): Contact {
  const id = uuid();
  return {
    id,
    vault_id: VAULT_ID,
    first_name: 'Jane',
    last_name: 'Doe',
    nickname: null,
    birthdate: null,
    gender: null,
    pronouns: null,
    notes_summary: null,
    favorite: false,
    photo_file_id: null,
    template_id: null,
    contact_methods: [],
    addresses: [],
    tags: [],
    pets: [],
    relationships: [],
    created_at: now,
    updated_at: now,
    ...overrides
  };
}

export function makeTask(overrides?: Partial<Task>): Task {
  const id = uuid();
  return {
    id,
    vault_id: VAULT_ID,
    title: 'Test task',
    description: null,
    due_date: null,
    status: 'pending',
    priority: 1,
    contact_id: null,
    activity_id: null,
    created_by_id: uuid(),
    created_at: now,
    updated_at: now,
    ...overrides
  };
}

export function makeActivity(overrides?: Partial<Activity>): Activity {
  const id = uuid();
  return {
    id,
    vault_id: VAULT_ID,
    activity_type_id: null,
    title: 'Test activity',
    description: null,
    happened_at: now,
    location: null,
    participants: [],
    created_at: now,
    updated_at: now,
    ...overrides
  };
}

export function makeActivityType(overrides?: Partial<ActivityType>): ActivityType {
  const id = uuid();
  return {
    id,
    vault_id: VAULT_ID,
    name: 'Meeting',
    icon: 'calendar',
    color: '#3b82f6',
    created_at: now,
    updated_at: now,
    ...overrides
  };
}

export function makeJournalEntry(overrides?: Partial<JournalEntry>): JournalEntry {
  const id = uuid();
  return {
    id,
    vault_id: VAULT_ID,
    entry_date: '2026-01-15',
    title: 'Test entry',
    body_markdown: 'Some thoughts',
    mood: null,
    created_by_id: uuid(),
    created_at: now,
    updated_at: now,
    ...overrides
  };
}

export function makeReminder(overrides?: Partial<Reminder>): Reminder {
  const id = uuid();
  return {
    id,
    vault_id: VAULT_ID,
    contact_id: null,
    title: 'Test reminder',
    description: null,
    next_expected_date: '2026-02-01',
    frequency_type: 'month',
    frequency_number: 1,
    last_triggered_at: null,
    status: 'active',
    created_at: now,
    updated_at: now,
    ...overrides
  };
}

export function makeGift(overrides?: Partial<Gift>): Gift {
  const id = uuid();
  return {
    id,
    vault_id: VAULT_ID,
    contact_id: uuid(),
    direction: 'given',
    name: 'Test gift',
    description: null,
    amount: null,
    currency: 'USD',
    status: 'given',
    link: null,
    created_at: now,
    updated_at: now,
    ...overrides
  };
}

export function makeDebt(overrides?: Partial<Debt>): Debt {
  const id = uuid();
  return {
    id,
    vault_id: VAULT_ID,
    contact_id: uuid(),
    direction: 'you_owe',
    amount: 50,
    currency: 'USD',
    due_date: null,
    settled: false,
    notes: null,
    created_at: now,
    updated_at: now,
    ...overrides
  };
}

export function makeNote(overrides?: Partial<Note>): Note {
  const id = uuid();
  return {
    id,
    vault_id: VAULT_ID,
    contact_id: null,
    activity_id: null,
    title: 'Test note',
    body_markdown: 'Note body',
    created_by_id: uuid(),
    created_at: now,
    updated_at: now,
    ...overrides
  };
}

export function makeFileRecord(overrides?: Partial<FileRecord>): FileRecord {
  const id = uuid();
  return {
    id,
    vault_id: VAULT_ID,
    uploader_id: uuid(),
    storage_key: `uploads/${id}.pdf`,
    filename: 'document.pdf',
    mime_type: 'application/pdf',
    size_bytes: 1024,
    created_at: now,
    updated_at: now,
    ...overrides
  };
}

export function makeContactMethod(overrides?: Partial<ContactMethod>): ContactMethod {
  return {
    id: uuid(),
    vault_id: VAULT_ID,
    contact_id: uuid(),
    type: 'phone',
    label: 'Mobile',
    value: '+1 555-0100',
    created_at: now,
    updated_at: now,
    ...overrides
  };
}

export function makeAddress(overrides?: Partial<Address>): Address {
  return {
    id: uuid(),
    vault_id: VAULT_ID,
    contact_id: uuid(),
    label: 'Home',
    line1: '123 Main St',
    line2: null,
    city: 'Springfield',
    postal_code: '12345',
    country: 'USA',
    geo_location: null,
    created_at: now,
    updated_at: now,
    ...overrides
  };
}

export function makePet(overrides?: Partial<Pet>): Pet {
  return {
    id: uuid(),
    vault_id: VAULT_ID,
    contact_id: uuid(),
    name: 'Milo',
    species: 'Cat',
    birthdate: null,
    notes: null,
    created_at: now,
    updated_at: now,
    ...overrides
  };
}

export function makeTag(overrides?: Partial<Tag>): Tag {
  return {
    id: uuid(),
    vault_id: VAULT_ID,
    name: 'Family',
    color: '#6366f1',
    created_at: now,
    updated_at: now,
    ...overrides
  };
}

export function makeContactRelationship(overrides?: Partial<ContactRelationship>): ContactRelationship {
  return {
    id: uuid(),
    vault_id: VAULT_ID,
    contact_id: uuid(),
    other_contact_id: uuid(),
    relationship_type_id: uuid(),
    created_at: now,
    updated_at: now,
    ...overrides
  };
}

export function makeRelationshipType(overrides?: Partial<RelationshipType>): RelationshipType {
  return {
    id: uuid(),
    vault_id: VAULT_ID,
    name: 'Friend',
    inverse_type_id: null,
    created_at: now,
    updated_at: now,
    ...overrides
  };
}
