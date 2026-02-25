// --- Auth ---

export interface User {
  id: string;
  email: string;
  name: string;
  is_active: boolean;
  default_vault_id: string | null;
  created_at: string;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  vault_id: string | null;
}

export interface TwoFactorChallengeResponse {
  requires_2fa: boolean;
  temp_token: string;
}

export type LoginResponse = AuthResponse | TwoFactorChallengeResponse;

export interface TwoFactorSetupResponse {
  provisioning_uri: string;
  qr_data_url: string;
  recovery_codes: string[];
}

export interface TwoFactorVerifyRequest {
  temp_token: string;
  code: string;
}

export interface TwoFactorConfirmRequest {
  code: string;
}

// --- Vaults ---

export interface Vault {
  id: string;
  name: string;
  created_at: string;
}

// --- Contacts ---

export interface Contact {
  id: string;
  vault_id: string;
  first_name: string;
  last_name: string;
  nickname: string | null;
  birthdate: string | null;
  gender: string | null;
  pronouns: string | null;
  notes_summary: string | null;
  favorite: boolean;
  photo_file_id: string | null;
  template_id: string | null;
  contact_methods: ContactMethod[];
  addresses: Address[];
  tags: Tag[];
  pets: Pet[];
  relationships: ContactRelationship[];
  created_at: string;
  updated_at: string;
}

// --- Activities ---

export interface ActivityType {
  id: string;
  vault_id: string;
  name: string;
  icon: string;
  color: string;
  created_at: string;
  updated_at: string;
}

export interface ActivityParticipant {
  id: string;
  contact_id: string;
  role: string;
}

export interface Activity {
  id: string;
  vault_id: string;
  activity_type_id: string | null;
  title: string;
  description: string | null;
  happened_at: string;
  location: string | null;
  participants: ActivityParticipant[];
  created_at: string;
  updated_at: string;
}

// --- Notes ---

export interface Note {
  id: string;
  vault_id: string;
  contact_id: string | null;
  activity_id: string | null;
  title: string;
  body_markdown: string;
  created_by_id: string;
  created_at: string;
  updated_at: string;
}

// --- Reminders ---

export type FrequencyType = 'one_time' | 'week' | 'month' | 'year';

export interface Reminder {
  id: string;
  vault_id: string;
  contact_id: string | null;
  title: string;
  description: string | null;
  next_expected_date: string;
  frequency_type: FrequencyType;
  frequency_number: number;
  last_triggered_at: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

// --- Tasks ---

export interface Task {
  id: string;
  vault_id: string;
  title: string;
  description: string | null;
  due_date: string | null;
  status: string;
  priority: number;
  contact_id: string | null;
  activity_id: string | null;
  created_by_id: string;
  created_at: string;
  updated_at: string;
}

// --- Journal ---

export interface JournalEntry {
  id: string;
  vault_id: string;
  entry_date: string;
  title: string;
  body_markdown: string;
  mood: number | null;
  created_by_id: string;
  created_at: string;
  updated_at: string;
}

// --- Finance ---

export type GiftDirection = 'given' | 'received' | 'idea';
export type GiftStatus = 'idea' | 'planned' | 'purchased' | 'given';

export interface Gift {
  id: string;
  vault_id: string;
  contact_id: string;
  direction: GiftDirection;
  name: string;
  description: string | null;
  amount: number | null;
  currency: string;
  status: GiftStatus;
  link: string | null;
  created_at: string;
  updated_at: string;
}

export type DebtDirection = 'you_owe' | 'owed_to_you';

export interface Debt {
  id: string;
  vault_id: string;
  contact_id: string;
  direction: DebtDirection;
  amount: number;
  currency: string;
  due_date: string | null;
  settled: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

// --- Files ---

export interface FileRecord {
  id: string;
  vault_id: string;
  uploader_id: string;
  storage_key: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  created_at: string;
  updated_at: string;
}

// --- Notifications ---

export interface Notification {
  id: string;
  user_id: string;
  vault_id: string;
  title: string;
  body: string;
  link: string | null;
  read: boolean;
  created_at: string;
}

// --- Vault Settings ---

export interface VaultSettings {
  vault_id: string;
  language: string;
  date_format: string;
  time_format: string;
  timezone: string;
  feature_flags: string;
}

// --- Templates ---

export interface TemplateModule {
  id: string;
  page_id: string;
  module_type: string;
  order: number;
  config_json: string | null;
  created_at: string;
  updated_at: string;
}

export interface TemplatePage {
  id: string;
  template_id: string;
  slug: string;
  name: string;
  order: number;
  modules: TemplateModule[];
  created_at: string;
  updated_at: string;
}

export interface Template {
  id: string;
  vault_id: string;
  name: string;
  description: string | null;
  pages: TemplatePage[];
  created_at: string;
  updated_at: string;
}

// --- Custom Fields ---

export interface CustomField {
  id: string;
  vault_id: string;
  scope: string;
  name: string;
  slug: string;
  data_type: string;
  config_json: string | null;
  created_at: string;
  updated_at: string;
}

export interface CustomFieldValue {
  id: string;
  vault_id: string;
  definition_id: string;
  entity_type: string;
  entity_id: string;
  value_json: string;
  created_at: string;
  updated_at: string;
}

// --- Members ---

export interface Member {
  user_id: string;
  email: string;
  name: string;
  role: string;
  joined_at: string;
}

// --- Contact Sub-resources ---

export interface ContactMethod {
  id: string;
  vault_id: string;
  contact_id: string;
  type: string;
  label: string;
  value: string;
  created_at: string;
  updated_at: string;
}

export interface Address {
  id: string;
  vault_id: string;
  contact_id: string;
  label: string;
  line1: string;
  line2: string | null;
  city: string;
  postal_code: string;
  country: string;
  geo_location: string | null;
  created_at: string;
  updated_at: string;
}

export interface Pet {
  id: string;
  vault_id: string;
  contact_id: string;
  name: string;
  species: string;
  birthdate: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Tag {
  id: string;
  vault_id: string;
  name: string;
  color: string;
  created_at: string;
  updated_at: string;
}

export interface ContactRelationship {
  id: string;
  vault_id: string;
  contact_id: string;
  other_contact_id: string;
  relationship_type_id: string;
  created_at: string;
  updated_at: string;
}

// --- Relationship Types ---

export interface RelationshipType {
  id: string;
  vault_id: string;
  name: string;
  inverse_type_id: string | null;
  created_at: string;
  updated_at: string;
}

// --- PATs ---

export interface PersonalAccessToken {
  id: string;
  name: string;
  token_prefix: string;
  scopes: string[];
  expires_at: string | null;
  last_used_at: string | null;
  created_at: string;
}
