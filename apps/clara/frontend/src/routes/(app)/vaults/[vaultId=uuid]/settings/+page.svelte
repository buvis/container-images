<script lang="ts">
  import { page } from '$app/state';
  import { authApi } from '$api/auth';
  import { vaultsApi } from '$api/vaults';
  import { importExportApi } from '$api/importExport';
  import { customizationApi } from '$api/customization';
  import type { TemplateCreateInput, CustomFieldCreateInput, TemplatePageCreateInput, TemplateModuleCreateInput } from '$api/customization';
  import type { TemplatePage, TemplateModule } from '$lib/types/models';
  import { relationshipTypesApi } from '$api/contacts';
  import { activitiesApi } from '$api/activities';
  import { tokensApi } from '$api/tokens';
  import type { PatCreateInput, PatCreateResponse } from '$api/tokens';
  import type { TwoFactorSetupResponse } from '$api/types';
  import type { Member, Template, CustomField, RelationshipType, ActivityType, PersonalAccessToken } from '$lib/types/models';
  import Button from '$components/ui/Button.svelte';
  import Badge from '$components/ui/Badge.svelte';
  import Input from '$components/ui/Input.svelte';
  import Modal from '$components/ui/Modal.svelte';
  import { Pencil, Trash2, Copy, Check, ChevronRight, ChevronDown } from 'lucide-svelte';

  const vaultId = $derived(page.params.vaultId!);

  const tabs = ['General', 'Members', 'Templates', 'Custom Fields', 'Relationship Types', 'Activity Types', 'Security', 'Import/Export'] as const;
  type Tab = (typeof tabs)[number];
  let activeTab = $state<Tab>('General');

  let settingsLoading = $state(true);
  let settingsSaving = $state(false);
  let settingsMessage = $state('');
  let settingsError = $state('');
  let settingsForm = $state({
    language: 'en',
    date_format: 'YYYY-MM-DD',
    time_format: '24h',
    timezone: 'UTC',
    debts: true,
    gifts: true,
    pets: true,
    journal: true
  });

  let members = $state<Member[]>([]);
  let membersLoading = $state(true);
  let inviteEmail = $state('');
  let inviteRole = $state('member');
  let inviting = $state(false);

  let templates = $state<Template[]>([]);
  let templatesLoading = $state(true);
  let showTemplateModal = $state(false);
  let editTemplateId = $state<string | null>(null);
  let templateForm = $state<TemplateCreateInput>({ name: '' });
  let templateSaving = $state(false);
  let templateDeleteId = $state<string | null>(null);
  let expandedTemplateId = $state<string | null>(null);
  let expandedPageId = $state<string | null>(null);
  let showPageModal = $state(false);
  let editPageId = $state<string | null>(null);
  let pageForm = $state<{ slug: string; name: string; order: number }>({ slug: '', name: '', order: 0 });
  let pageSaving = $state(false);
  let showModuleModal = $state(false);
  let editModuleId = $state<string | null>(null);
  let moduleForm = $state<{ module_type: string; order: number; config_json: string }>({ module_type: '', order: 0, config_json: '' });
  let moduleSaving = $state(false);
  let pageDeleteId = $state<string | null>(null);
  let moduleDeleteId = $state<string | null>(null);
  let activeTemplateForPage = $state<string | null>(null);
  let activePageForModule = $state<string | null>(null);

  let customFields = $state<CustomField[]>([]);
  let customFieldsLoading = $state(true);
  let showFieldModal = $state(false);
  let editFieldId = $state<string | null>(null);
  let fieldForm = $state<CustomFieldCreateInput>({ scope: 'contact', name: '', slug: '', data_type: 'text' });
  let fieldSaving = $state(false);
  let fieldDeleteId = $state<string | null>(null);

  let relTypes = $state<RelationshipType[]>([]);
  let relTypesLoading = $state(true);
  let showRelTypeModal = $state(false);
  let editRelTypeId = $state<string | null>(null);
  let relTypeForm = $state({ name: '', inverse_type_id: '' });
  let relTypeSaving = $state(false);

  let activityTypes = $state<ActivityType[]>([]);
  let activityTypesLoading = $state(true);
  let showActivityTypeModal = $state(false);
  let editActivityTypeId = $state<string | null>(null);
  let activityTypeForm = $state<{ name: string; icon: string; color: string }>({ name: '', icon: '', color: '#6b7280' });
  let activityTypeSaving = $state(false);
  let activityTypeDeleteId = $state<string | null>(null);

  let tokens = $state<PersonalAccessToken[]>([]);
  let tokensLoading = $state(true);
  let showTokenModal = $state(false);
  let tokenForm = $state<PatCreateInput>({ name: '', scopes: ['read'] });
  let tokenSaving = $state(false);
  let newToken = $state<PatCreateResponse | null>(null);
  let tokenCopied = $state(false);
  let revokeConfirmId = $state<string | null>(null);

  let importLoading = $state(false);
  let importMessage = $state('');
  let importError = $state('');

  let setup = $state<TwoFactorSetupResponse | null>(null);
  let setupLoading = $state(false);
  let setupError = $state('');
  let confirmCode = $state('');
  let confirmLoading = $state(false);
  let confirmError = $state('');
  let confirmSuccess = $state(false);
  let disableLoading = $state(false);
  let disableMessage = $state('');
  let disableError = $state('');

  function parseFeatureFlags(raw: string): { debts: boolean; gifts: boolean; pets: boolean; journal: boolean } {
    try {
      const parsed = JSON.parse(raw || '{}');
      return {
        debts: parsed.debts !== false,
        gifts: parsed.gifts !== false,
        pets: parsed.pets !== false,
        journal: parsed.journal !== false
      };
    } catch {
      return { debts: true, gifts: true, pets: true, journal: true };
    }
  }

  function toFeatureFlags() {
    return JSON.stringify({
      debts: settingsForm.debts,
      gifts: settingsForm.gifts,
      pets: settingsForm.pets,
      journal: settingsForm.journal
    });
  }

  async function loadSettings() {
    settingsLoading = true;
    settingsError = '';
    try {
      const settings = await vaultsApi.getSettings(vaultId);
      const flags = parseFeatureFlags(settings.feature_flags);
      settingsForm = {
        language: settings.language,
        date_format: settings.date_format,
        time_format: settings.time_format,
        timezone: settings.timezone,
        debts: flags.debts,
        gifts: flags.gifts,
        pets: flags.pets,
        journal: flags.journal
      };
    } catch (err: any) {
      settingsError = err.detail ?? 'Failed to load settings';
    } finally {
      settingsLoading = false;
    }
  }

  async function saveSettings() {
    settingsSaving = true;
    settingsMessage = '';
    settingsError = '';
    try {
      await vaultsApi.updateSettings(vaultId, {
        language: settingsForm.language,
        date_format: settingsForm.date_format,
        time_format: settingsForm.time_format,
        timezone: settingsForm.timezone,
        feature_flags: toFeatureFlags()
      });
      settingsMessage = 'Settings saved.';
    } catch (err: any) {
      settingsError = err.detail ?? 'Failed to save settings';
    } finally {
      settingsSaving = false;
    }
  }

  async function loadMembers() {
    membersLoading = true;
    try {
      members = await vaultsApi.listMembers(vaultId);
    } finally {
      membersLoading = false;
    }
  }

  async function handleInvite() {
    if (!inviteEmail.trim()) return;
    inviting = true;
    try {
      await vaultsApi.inviteMember(vaultId, { email: inviteEmail, role: inviteRole });
      inviteEmail = '';
      inviteRole = 'member';
      await loadMembers();
    } finally {
      inviting = false;
    }
  }

  async function handleRoleChange(member: Member, role: string) {
    await vaultsApi.updateMemberRole(vaultId, member.user_id, role);
    await loadMembers();
  }

  async function handleRemove(member: Member) {
    await vaultsApi.removeMember(vaultId, member.user_id);
    await loadMembers();
  }

  async function handleImportVcard(e: Event) {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    importLoading = true;
    importMessage = '';
    importError = '';
    try {
      await importExportApi.importVcard(vaultId, file);
      importMessage = 'vCard import completed.';
    } catch (err: any) {
      importError = err.message ?? 'Import failed';
    } finally {
      importLoading = false;
      input.value = '';
    }
  }

  async function handleImportCsv(e: Event) {
    const input = e.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    importLoading = true;
    importMessage = '';
    importError = '';
    try {
      await importExportApi.importCsv(vaultId, file);
      importMessage = 'CSV import completed.';
    } catch (err: any) {
      importError = err.message ?? 'Import failed';
    } finally {
      importLoading = false;
      input.value = '';
    }
  }

  async function handleSetup() {
    setupError = '';
    disableMessage = '';
    disableError = '';
    setupLoading = true;
    try {
      setup = await authApi.setupTwoFactor();
      confirmSuccess = false;
      confirmCode = '';
    } catch (err: any) {
      setupError = err.detail ?? 'Failed to start 2FA setup';
    } finally {
      setupLoading = false;
    }
  }

  async function handleConfirm(e: SubmitEvent) {
    e.preventDefault();
    confirmError = '';
    confirmLoading = true;
    try {
      await authApi.confirmTwoFactor({ code: confirmCode });
      confirmSuccess = true;
    } catch (err: any) {
      confirmError = err.detail ?? 'Invalid verification code';
    } finally {
      confirmLoading = false;
    }
  }

  async function handleDisable() {
    disableError = '';
    disableMessage = '';
    disableLoading = true;
    try {
      await authApi.disableTwoFactor();
      setup = null;
      confirmSuccess = false;
      confirmCode = '';
      disableMessage = 'Two-factor authentication disabled.';
    } catch (err: any) {
      disableError = err.detail ?? 'Failed to disable two-factor authentication';
    } finally {
      disableLoading = false;
    }
  }

  async function loadTemplates() {
    templatesLoading = true;
    try {
      const res = await customizationApi.listTemplates(vaultId);
      templates = res.items;
    } finally {
      templatesLoading = false;
    }
  }

  async function loadCustomFields() {
    customFieldsLoading = true;
    try {
      const res = await customizationApi.listCustomFields(vaultId);
      customFields = res.items;
    } finally {
      customFieldsLoading = false;
    }
  }

  // --- Template CRUD ---
  function openTemplateCreate() {
    editTemplateId = null;
    templateForm = { name: '' };
    showTemplateModal = true;
  }

  function openTemplateEdit(t: Template) {
    editTemplateId = t.id;
    templateForm = { name: t.name, description: t.description };
    showTemplateModal = true;
  }

  async function handleTemplateSave() {
    templateSaving = true;
    try {
      if (editTemplateId) {
        const updated = await customizationApi.updateTemplate(vaultId, editTemplateId, templateForm);
        templates = templates.map((t) => (t.id === editTemplateId ? updated : t));
      } else {
        const created = await customizationApi.createTemplate(vaultId, templateForm);
        templates = [...templates, created];
      }
      showTemplateModal = false;
    } finally {
      templateSaving = false;
    }
  }

  async function handleTemplateDelete(id: string) {
    await customizationApi.deleteTemplate(vaultId, id);
    templates = templates.filter((t) => t.id !== id);
    templateDeleteId = null;
  }

  // --- Template Pages/Modules ---
  async function toggleTemplate(templateId: string) {
    if (expandedTemplateId === templateId) {
      expandedTemplateId = null;
      return;
    }
    const full = await customizationApi.getTemplate(vaultId, templateId);
    templates = templates.map((t) => (t.id === full.id ? full : t));
    expandedTemplateId = templateId;
  }

  function openPageCreate(templateId: string) {
    activeTemplateForPage = templateId;
    editPageId = null;
    const t = templates.find((t) => t.id === templateId);
    pageForm = { slug: '', name: '', order: (t?.pages?.length ?? 0) + 1 };
    showPageModal = true;
  }

  function openPageEdit(p: TemplatePage) {
    editPageId = p.id;
    pageForm = { slug: p.slug, name: p.name, order: p.order };
    showPageModal = true;
  }

  async function handlePageSave(e: Event) {
    e.preventDefault();
    pageSaving = true;
    try {
      if (editPageId) {
        await customizationApi.updatePage(vaultId, editPageId, pageForm);
      } else if (activeTemplateForPage) {
        await customizationApi.addPage(vaultId, activeTemplateForPage, pageForm);
      }
      showPageModal = false;
      if (expandedTemplateId) {
        const full = await customizationApi.getTemplate(vaultId, expandedTemplateId);
        templates = templates.map((t) => (t.id === full.id ? full : t));
      }
    } finally {
      pageSaving = false;
    }
  }

  async function handlePageDelete(pageId: string) {
    await customizationApi.deletePage(vaultId, pageId);
    pageDeleteId = null;
    if (expandedTemplateId) {
      const full = await customizationApi.getTemplate(vaultId, expandedTemplateId);
      templates = templates.map((t) => (t.id === full.id ? full : t));
    }
  }

  function openModuleCreate(pageId: string) {
    activePageForModule = pageId;
    editModuleId = null;
    moduleForm = { module_type: '', order: 0, config_json: '' };
    showModuleModal = true;
  }

  function openModuleEdit(m: TemplateModule) {
    editModuleId = m.id;
    moduleForm = { module_type: m.module_type, order: m.order, config_json: m.config_json ?? '' };
    showModuleModal = true;
  }

  async function handleModuleSave(e: Event) {
    e.preventDefault();
    moduleSaving = true;
    try {
      if (editModuleId) {
        await customizationApi.updateModule(vaultId, editModuleId, moduleForm);
      } else if (activePageForModule) {
        await customizationApi.addModule(vaultId, activePageForModule, moduleForm);
      }
      showModuleModal = false;
      if (expandedTemplateId) {
        const full = await customizationApi.getTemplate(vaultId, expandedTemplateId);
        templates = templates.map((t) => (t.id === full.id ? full : t));
      }
    } finally {
      moduleSaving = false;
    }
  }

  async function handleModuleDelete(moduleId: string) {
    await customizationApi.deleteModule(vaultId, moduleId);
    moduleDeleteId = null;
    if (expandedTemplateId) {
      const full = await customizationApi.getTemplate(vaultId, expandedTemplateId);
      templates = templates.map((t) => (t.id === full.id ? full : t));
    }
  }

  // --- Custom Field CRUD ---
  function openFieldCreate() {
    editFieldId = null;
    fieldForm = { scope: 'contact', name: '', slug: '', data_type: 'text' };
    showFieldModal = true;
  }

  function openFieldEdit(cf: CustomField) {
    editFieldId = cf.id;
    fieldForm = { scope: cf.scope, name: cf.name, slug: cf.slug, data_type: cf.data_type, config_json: cf.config_json };
    showFieldModal = true;
  }

  async function handleFieldSave() {
    fieldSaving = true;
    try {
      if (editFieldId) {
        const updated = await customizationApi.updateCustomField(vaultId, editFieldId, fieldForm);
        customFields = customFields.map((cf) => (cf.id === editFieldId ? updated : cf));
      } else {
        const created = await customizationApi.createCustomField(vaultId, fieldForm);
        customFields = [...customFields, created];
      }
      showFieldModal = false;
    } finally {
      fieldSaving = false;
    }
  }

  async function handleFieldDelete(id: string) {
    await customizationApi.deleteCustomField(vaultId, id);
    customFields = customFields.filter((cf) => cf.id !== id);
    fieldDeleteId = null;
  }

  // --- Relationship Types CRUD ---
  async function loadRelTypes() {
    relTypesLoading = true;
    try {
      relTypes = await relationshipTypesApi.list(vaultId);
    } finally {
      relTypesLoading = false;
    }
  }

  function openRelTypeCreate() {
    editRelTypeId = null;
    relTypeForm = { name: '', inverse_type_id: '' };
    showRelTypeModal = true;
  }

  function openRelTypeEdit(rt: RelationshipType) {
    editRelTypeId = rt.id;
    relTypeForm = { name: rt.name, inverse_type_id: rt.inverse_type_id ?? '' };
    showRelTypeModal = true;
  }

  async function handleRelTypeSave() {
    relTypeSaving = true;
    try {
      const data = { name: relTypeForm.name, inverse_type_id: relTypeForm.inverse_type_id || null };
      if (editRelTypeId) {
        const updated = await relationshipTypesApi.update(vaultId, editRelTypeId, data);
        relTypes = relTypes.map((rt) => (rt.id === editRelTypeId ? updated : rt));
      } else {
        const created = await relationshipTypesApi.create(vaultId, data);
        relTypes = [...relTypes, created];
      }
      showRelTypeModal = false;
    } finally {
      relTypeSaving = false;
    }
  }

  async function handleRelTypeDelete(id: string) {
    await relationshipTypesApi.del(vaultId, id);
    relTypes = relTypes.filter((rt) => rt.id !== id);
  }

  // --- Activity Types CRUD ---
  function openActivityTypeCreate() {
    editActivityTypeId = null;
    activityTypeForm = { name: '', icon: '', color: '#6b7280' };
    showActivityTypeModal = true;
  }

  function openActivityTypeEdit(t: ActivityType) {
    editActivityTypeId = t.id;
    activityTypeForm = { name: t.name, icon: t.icon, color: t.color };
    showActivityTypeModal = true;
  }

  async function handleActivityTypeSave(e: Event) {
    e.preventDefault();
    activityTypeSaving = true;
    try {
      if (editActivityTypeId) {
        const updated = await activitiesApi.updateType(vaultId, editActivityTypeId, activityTypeForm);
        activityTypes = activityTypes.map((t) => (t.id === updated.id ? updated : t));
      } else {
        const created = await activitiesApi.createType(vaultId, activityTypeForm);
        activityTypes = [...activityTypes, created];
      }
      showActivityTypeModal = false;
    } finally {
      activityTypeSaving = false;
    }
  }

  async function handleActivityTypeDelete(id: string) {
    await activitiesApi.deleteType(vaultId, id);
    activityTypes = activityTypes.filter((t) => t.id !== id);
    activityTypeDeleteId = null;
  }

  // --- PAT CRUD ---
  async function loadTokens() {
    tokensLoading = true;
    try {
      tokens = await tokensApi.list();
    } finally {
      tokensLoading = false;
    }
  }

  function openTokenCreate() {
    tokenForm = { name: '', scopes: ['read'] };
    newToken = null;
    tokenCopied = false;
    showTokenModal = true;
  }

  function toggleScope(scope: string) {
    if (tokenForm.scopes.includes(scope)) {
      tokenForm.scopes = tokenForm.scopes.filter((s) => s !== scope);
    } else {
      tokenForm.scopes = [...tokenForm.scopes, scope];
    }
  }

  async function handleTokenCreate() {
    tokenSaving = true;
    try {
      const result = await tokensApi.create(tokenForm);
      newToken = result;
      tokens = [...tokens, result];
    } finally {
      tokenSaving = false;
    }
  }

  async function copyToken() {
    if (!newToken) return;
    await navigator.clipboard.writeText(newToken.token);
    tokenCopied = true;
    setTimeout(() => (tokenCopied = false), 2000);
  }

  async function handleTokenRevoke(id: string) {
    await tokensApi.revoke(id);
    tokens = tokens.filter((t) => t.id !== id);
    revokeConfirmId = null;
  }

  function formatTokenDate(d: string | null): string {
    if (!d) return 'Never';
    return new Date(d).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
  }

  $effect(() => {
    if (!vaultId) return;
    if (activeTab === 'General') loadSettings();
    if (activeTab === 'Members') loadMembers();
    if (activeTab === 'Templates') loadTemplates();
    if (activeTab === 'Custom Fields') loadCustomFields();
    if (activeTab === 'Relationship Types') loadRelTypes();
    if (activeTab === 'Activity Types') {
      activityTypesLoading = true;
      activitiesApi.listTypes(vaultId, { limit: 100 }).then((r) => {
        activityTypes = r.items;
        activityTypesLoading = false;
      });
    }
    if (activeTab === 'Security') loadTokens();
  });
</script>

<svelte:head>
  <title>Settings</title>
</svelte:head>

<div class="space-y-6">
  <div>
    <h1 class="text-2xl font-semibold text-white">Settings</h1>
    <p class="text-sm text-neutral-400">Manage vault preferences for {vaultId}.</p>
  </div>

  <div class="flex flex-wrap gap-2">
    {#each tabs as tab}
      <button
        type="button"
        class="rounded-lg px-3 py-1.5 text-sm transition {activeTab === tab
          ? 'bg-brand-500/10 text-brand-400'
          : 'text-neutral-400 hover:bg-neutral-800 hover:text-white'}"
        onclick={() => (activeTab = tab)}
      >
        {tab}
      </button>
    {/each}
  </div>

  {#if activeTab === 'General'}
    <section class="space-y-4 rounded-xl border border-neutral-800 bg-neutral-900 p-6">
      {#if settingsError}
        <div class="rounded-lg bg-red-950/50 px-4 py-3 text-sm text-red-400">{settingsError}</div>
      {/if}
      {#if settingsMessage}
        <div class="rounded-lg bg-emerald-950/50 px-4 py-3 text-sm text-emerald-300">{settingsMessage}</div>
      {/if}

      {#if settingsLoading}
        <p class="text-sm text-neutral-500">Loading settings…</p>
      {:else}
        <div class="grid gap-4 md:grid-cols-2">
          <div>
            <label class="mb-1.5 block text-sm font-medium text-neutral-300">Language</label>
            <select
              bind:value={settingsForm.language}
              class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500"
            >
              <option value="en">English</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
            </select>
          </div>
          <div>
            <label class="mb-1.5 block text-sm font-medium text-neutral-300">Date format</label>
            <select
              bind:value={settingsForm.date_format}
              class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500"
            >
              <option value="YYYY-MM-DD">YYYY-MM-DD</option>
              <option value="MM/DD/YYYY">MM/DD/YYYY</option>
              <option value="DD/MM/YYYY">DD/MM/YYYY</option>
            </select>
          </div>
          <div>
            <label class="mb-1.5 block text-sm font-medium text-neutral-300">Time format</label>
            <select
              bind:value={settingsForm.time_format}
              class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500"
            >
              <option value="24h">24-hour</option>
              <option value="12h">12-hour</option>
            </select>
          </div>
          <Input label="Timezone" bind:value={settingsForm.timezone} />
        </div>

        <div>
          <h3 class="text-sm font-medium text-neutral-300">Feature flags</h3>
          <div class="mt-3 grid gap-3 sm:grid-cols-2">
            <label class="flex items-center justify-between rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2 text-sm text-neutral-300">
              Debts
              <input type="checkbox" bind:checked={settingsForm.debts} class="h-4 w-4 accent-brand-500" />
            </label>
            <label class="flex items-center justify-between rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2 text-sm text-neutral-300">
              Gifts
              <input type="checkbox" bind:checked={settingsForm.gifts} class="h-4 w-4 accent-brand-500" />
            </label>
            <label class="flex items-center justify-between rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2 text-sm text-neutral-300">
              Pets
              <input type="checkbox" bind:checked={settingsForm.pets} class="h-4 w-4 accent-brand-500" />
            </label>
            <label class="flex items-center justify-between rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2 text-sm text-neutral-300">
              Journal
              <input type="checkbox" bind:checked={settingsForm.journal} class="h-4 w-4 accent-brand-500" />
            </label>
          </div>
        </div>

        <div class="flex justify-end">
          <Button onclick={saveSettings} loading={settingsSaving}>Save settings</Button>
        </div>
      {/if}
    </section>
  {/if}

  {#if activeTab === 'Members'}
    <section class="space-y-4 rounded-xl border border-neutral-800 bg-neutral-900 p-6">
      <div class="space-y-2">
        <h2 class="text-lg font-semibold text-white">Members</h2>
        {#if membersLoading}
          <p class="text-sm text-neutral-500">Loading members…</p>
        {:else if members.length === 0}
          <p class="text-sm text-neutral-500">No members yet.</p>
        {:else}
          <div class="space-y-2">
            {#each members as member}
              <div class="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2">
                <div>
                  <p class="text-sm font-medium text-white">{member.name || member.email}</p>
                  <p class="text-xs text-neutral-500">{member.email}</p>
                </div>
                <div class="flex items-center gap-2">
                  <Badge text={member.role} variant={member.role === 'owner' ? 'warning' : 'default'} />
                  <select
                    value={member.role}
                    onchange={(e) => handleRoleChange(member, (e.target as HTMLSelectElement).value)}
                    class="rounded-lg border border-neutral-700 bg-neutral-800 px-2 py-1 text-xs text-white outline-none transition focus:border-brand-500"
                  >
                    <option value="owner">Owner</option>
                    <option value="admin">Admin</option>
                    <option value="member">Member</option>
                    <option value="viewer">Viewer</option>
                  </select>
                  <Button size="sm" variant="ghost" onclick={() => handleRemove(member)}>Remove</Button>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>

      <form onsubmit={handleInvite} class="grid gap-3 rounded-lg border border-neutral-800 bg-neutral-950 p-4 md:grid-cols-[1fr_auto_auto] md:items-end">
        <Input label="Invite email" type="email" bind:value={inviteEmail} required />
        <div>
          <label class="mb-1.5 block text-sm font-medium text-neutral-300">Role</label>
          <select
            bind:value={inviteRole}
            class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500"
          >
            <option value="member">Member</option>
            <option value="admin">Admin</option>
            <option value="viewer">Viewer</option>
          </select>
        </div>
        <Button type="submit" loading={inviting}>Invite</Button>
      </form>
    </section>
  {/if}

  {#if activeTab === 'Templates'}
    <section class="space-y-4 rounded-xl border border-neutral-800 bg-neutral-900 p-6">
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold text-white">Templates</h2>
        <Button size="sm" onclick={openTemplateCreate}>Add template</Button>
      </div>
      {#if templatesLoading}
        <p class="text-sm text-neutral-500">Loading templates…</p>
      {:else if templates.length === 0}
        <p class="text-sm text-neutral-500">No templates configured.</p>
      {:else}
        <div class="space-y-2">
          {#each templates as t (t.id)}
            <div class="rounded-lg border border-neutral-800 bg-neutral-950">
              <div class="group flex items-center justify-between px-3 py-2">
                <button type="button" class="flex items-center gap-2 text-sm font-medium text-white" onclick={() => toggleTemplate(t.id)}>
                  {#if expandedTemplateId === t.id}
                    <ChevronDown size={14} />
                  {:else}
                    <ChevronRight size={14} />
                  {/if}
                  {t.name}
                </button>
                <div class="flex items-center gap-2">
                  <span class="text-xs text-neutral-500">{new Date(t.updated_at).toLocaleDateString()}</span>
                  {#if templateDeleteId === t.id}
                    <span class="text-xs text-red-400">Delete?</span>
                    <Button size="sm" variant="danger" onclick={() => handleTemplateDelete(t.id)}>Yes</Button>
                    <Button size="sm" variant="ghost" onclick={() => (templateDeleteId = null)}>No</Button>
                  {:else}
                    <button onclick={() => openTemplateEdit(t)} class="text-neutral-600 opacity-0 transition hover:text-white group-hover:opacity-100"><Pencil size={14} /></button>
                    <button onclick={() => (templateDeleteId = t.id)} class="text-neutral-600 opacity-0 transition hover:text-red-400 group-hover:opacity-100"><Trash2 size={14} /></button>
                  {/if}
                </div>
              </div>

              {#if expandedTemplateId === t.id}
                <div class="border-t border-neutral-800 px-3 py-2">
                  <div class="flex items-center justify-between mb-2">
                    <p class="text-xs font-medium uppercase tracking-wide text-neutral-500">Pages</p>
                    <Button size="sm" onclick={() => openPageCreate(t.id)}>Add page</Button>
                  </div>
                  {#if !t.pages?.length}
                    <p class="text-xs text-neutral-500">No pages.</p>
                  {:else}
                    <div class="space-y-1">
                      {#each t.pages as pg (pg.id)}
                        <div class="rounded-lg border border-neutral-800 bg-neutral-900">
                          <div class="group flex items-center justify-between px-3 py-1.5">
                            <button type="button" class="flex items-center gap-2 text-sm text-neutral-200" onclick={() => (expandedPageId = expandedPageId === pg.id ? null : pg.id)}>
                              {#if expandedPageId === pg.id}
                                <ChevronDown size={12} />
                              {:else}
                                <ChevronRight size={12} />
                              {/if}
                              {pg.name}
                              <span class="text-xs text-neutral-500">({pg.slug})</span>
                              <span class="text-xs text-neutral-600">#{pg.order}</span>
                            </button>
                            <div class="flex items-center gap-2">
                              {#if pageDeleteId === pg.id}
                                <span class="text-xs text-red-400">Delete?</span>
                                <Button size="sm" variant="danger" onclick={() => handlePageDelete(pg.id)}>Yes</Button>
                                <Button size="sm" variant="ghost" onclick={() => (pageDeleteId = null)}>No</Button>
                              {:else}
                                <button onclick={() => openPageEdit(pg)} class="text-neutral-600 opacity-0 transition hover:text-white group-hover:opacity-100"><Pencil size={12} /></button>
                                <button onclick={() => (pageDeleteId = pg.id)} class="text-neutral-600 opacity-0 transition hover:text-red-400 group-hover:opacity-100"><Trash2 size={12} /></button>
                              {/if}
                            </div>
                          </div>

                          {#if expandedPageId === pg.id}
                            <div class="border-t border-neutral-800 px-3 py-2">
                              <div class="flex items-center justify-between mb-2">
                                <p class="text-xs font-medium uppercase tracking-wide text-neutral-600">Modules</p>
                                <Button size="sm" onclick={() => openModuleCreate(pg.id)}>Add module</Button>
                              </div>
                              {#if !pg.modules?.length}
                                <p class="text-xs text-neutral-500">No modules.</p>
                              {:else}
                                <div class="space-y-1">
                                  {#each pg.modules as mod (mod.id)}
                                    <div class="group flex items-center justify-between rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-1.5">
                                      <div class="flex items-center gap-2 text-sm text-neutral-300">
                                        <span>{mod.module_type}</span>
                                        <span class="text-xs text-neutral-600">#{mod.order}</span>
                                      </div>
                                      <div class="flex items-center gap-2">
                                        {#if moduleDeleteId === mod.id}
                                          <span class="text-xs text-red-400">Delete?</span>
                                          <Button size="sm" variant="danger" onclick={() => handleModuleDelete(mod.id)}>Yes</Button>
                                          <Button size="sm" variant="ghost" onclick={() => (moduleDeleteId = null)}>No</Button>
                                        {:else}
                                          <button onclick={() => openModuleEdit(mod)} class="text-neutral-600 opacity-0 transition hover:text-white group-hover:opacity-100"><Pencil size={12} /></button>
                                          <button onclick={() => (moduleDeleteId = mod.id)} class="text-neutral-600 opacity-0 transition hover:text-red-400 group-hover:opacity-100"><Trash2 size={12} /></button>
                                        {/if}
                                      </div>
                                    </div>
                                  {/each}
                                </div>
                              {/if}
                            </div>
                          {/if}
                        </div>
                      {/each}
                    </div>
                  {/if}
                </div>
              {/if}
            </div>
          {/each}
        </div>
      {/if}
    </section>

    {#if showTemplateModal}
      <Modal title={editTemplateId ? 'Edit Template' : 'New Template'} onclose={() => (showTemplateModal = false)}>
        <form onsubmit={handleTemplateSave} class="space-y-4">
          <Input label="Name" bind:value={templateForm.name} required />
          <Input label="Description" bind:value={templateForm.description} />
          <div class="flex justify-end gap-3">
            <Button variant="ghost" onclick={() => (showTemplateModal = false)}>Cancel</Button>
            <Button type="submit" loading={templateSaving}>Save</Button>
          </div>
        </form>
      </Modal>
    {/if}

    {#if showPageModal}
      <Modal title={editPageId ? 'Edit Page' : 'New Page'} onclose={() => (showPageModal = false)}>
        <form onsubmit={handlePageSave} class="space-y-4">
          <Input label="Name" bind:value={pageForm.name} required />
          <Input label="Slug" bind:value={pageForm.slug} required />
          <Input label="Order" type="number" bind:value={pageForm.order} />
          <div class="flex justify-end gap-3">
            <Button variant="ghost" onclick={() => (showPageModal = false)}>Cancel</Button>
            <Button type="submit" loading={pageSaving}>Save</Button>
          </div>
        </form>
      </Modal>
    {/if}

    {#if showModuleModal}
      <Modal title={editModuleId ? 'Edit Module' : 'New Module'} onclose={() => (showModuleModal = false)}>
        <form onsubmit={handleModuleSave} class="space-y-4">
          <Input label="Module type" bind:value={moduleForm.module_type} required />
          <Input label="Order" type="number" bind:value={moduleForm.order} />
          <Input label="Config (JSON)" bind:value={moduleForm.config_json} />
          <div class="flex justify-end gap-3">
            <Button variant="ghost" onclick={() => (showModuleModal = false)}>Cancel</Button>
            <Button type="submit" loading={moduleSaving}>Save</Button>
          </div>
        </form>
      </Modal>
    {/if}
  {/if}

  {#if activeTab === 'Custom Fields'}
    <section class="space-y-4 rounded-xl border border-neutral-800 bg-neutral-900 p-6">
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold text-white">Custom Fields</h2>
        <Button size="sm" onclick={openFieldCreate}>Add field</Button>
      </div>
      {#if customFieldsLoading}
        <p class="text-sm text-neutral-500">Loading custom fields…</p>
      {:else if customFields.length === 0}
        <p class="text-sm text-neutral-500">No custom fields configured.</p>
      {:else}
        <div class="space-y-2">
          {#each customFields as cf (cf.id)}
            <div class="group flex items-center justify-between rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2">
              <div>
                <p class="text-sm font-medium text-white">{cf.name}</p>
                <p class="text-xs text-neutral-500">{cf.data_type} · {cf.scope} · {cf.slug}</p>
              </div>
              <div class="flex items-center gap-2">
                {#if fieldDeleteId === cf.id}
                  <span class="text-xs text-red-400">Delete?</span>
                  <Button size="sm" variant="danger" onclick={() => handleFieldDelete(cf.id)}>Yes</Button>
                  <Button size="sm" variant="ghost" onclick={() => (fieldDeleteId = null)}>No</Button>
                {:else}
                  <button onclick={() => openFieldEdit(cf)} class="text-neutral-600 opacity-0 transition hover:text-white group-hover:opacity-100"><Pencil size={14} /></button>
                  <button onclick={() => (fieldDeleteId = cf.id)} class="text-neutral-600 opacity-0 transition hover:text-red-400 group-hover:opacity-100"><Trash2 size={14} /></button>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </section>

    {#if showFieldModal}
      <Modal title={editFieldId ? 'Edit Custom Field' : 'New Custom Field'} onclose={() => (showFieldModal = false)}>
        <form onsubmit={handleFieldSave} class="space-y-4">
          <div>
            <label class="mb-1.5 block text-sm font-medium text-neutral-300">Scope</label>
            <select bind:value={fieldForm.scope} class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500">
              <option value="contact">Contact</option>
              <option value="activity">Activity</option>
              <option value="task">Task</option>
            </select>
          </div>
          <Input label="Name" bind:value={fieldForm.name} required />
          <Input label="Slug" bind:value={fieldForm.slug} required />
          <div>
            <label class="mb-1.5 block text-sm font-medium text-neutral-300">Data type</label>
            <select bind:value={fieldForm.data_type} class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500">
              <option value="text">Text</option>
              <option value="number">Number</option>
              <option value="date">Date</option>
              <option value="boolean">Boolean</option>
              <option value="select">Select</option>
            </select>
          </div>
          <Input label="Config (JSON)" bind:value={fieldForm.config_json} />
          <div class="flex justify-end gap-3">
            <Button variant="ghost" onclick={() => (showFieldModal = false)}>Cancel</Button>
            <Button type="submit" loading={fieldSaving}>Save</Button>
          </div>
        </form>
      </Modal>
    {/if}
  {/if}

  {#if activeTab === 'Relationship Types'}
    <section class="space-y-4 rounded-xl border border-neutral-800 bg-neutral-900 p-6">
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold text-white">Relationship Types</h2>
        <Button size="sm" onclick={openRelTypeCreate}>Add type</Button>
      </div>
      {#if relTypesLoading}
        <p class="text-sm text-neutral-500">Loading relationship types…</p>
      {:else if relTypes.length === 0}
        <p class="text-sm text-neutral-500">No relationship types configured.</p>
      {:else}
        <div class="space-y-2">
          {#each relTypes as rt (rt.id)}
            <div class="group flex items-center justify-between rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2">
              <div>
                <p class="text-sm font-medium text-white">{rt.name}</p>
                {#if rt.inverse_type_id}
                  {@const inv = relTypes.find((r) => r.id === rt.inverse_type_id)}
                  {#if inv}<p class="text-xs text-neutral-500">Inverse: {inv.name}</p>{/if}
                {/if}
              </div>
              <div class="flex items-center gap-2">
                <button onclick={() => openRelTypeEdit(rt)} class="text-neutral-600 opacity-0 transition hover:text-white group-hover:opacity-100"><Pencil size={14} /></button>
                <button onclick={() => handleRelTypeDelete(rt.id)} class="text-neutral-600 opacity-0 transition hover:text-red-400 group-hover:opacity-100"><Trash2 size={14} /></button>
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </section>

    {#if showRelTypeModal}
      <Modal title={editRelTypeId ? 'Edit Relationship Type' : 'New Relationship Type'} onclose={() => (showRelTypeModal = false)}>
        <form onsubmit={handleRelTypeSave} class="space-y-4">
          <Input label="Name" bind:value={relTypeForm.name} required />
          <div>
            <label class="mb-1.5 block text-sm font-medium text-neutral-300">Inverse type</label>
            <select bind:value={relTypeForm.inverse_type_id} class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500">
              <option value="">None</option>
              {#each relTypes.filter((r) => r.id !== editRelTypeId) as rt (rt.id)}
                <option value={rt.id}>{rt.name}</option>
              {/each}
            </select>
          </div>
          <div class="flex justify-end gap-3">
            <Button variant="ghost" onclick={() => (showRelTypeModal = false)}>Cancel</Button>
            <Button type="submit" loading={relTypeSaving}>Save</Button>
          </div>
        </form>
      </Modal>
    {/if}
  {/if}

  {#if activeTab === 'Activity Types'}
    <section class="space-y-4 rounded-xl border border-neutral-800 bg-neutral-900 p-6">
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-semibold text-white">Activity Types</h2>
        <Button size="sm" onclick={openActivityTypeCreate}>Add type</Button>
      </div>
      {#if activityTypesLoading}
        <p class="text-sm text-neutral-500">Loading activity types…</p>
      {:else if activityTypes.length === 0}
        <p class="text-sm text-neutral-500">No activity types configured.</p>
      {:else}
        <div class="space-y-2">
          {#each activityTypes as t (t.id)}
            <div class="group flex items-center justify-between rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2">
              <div class="flex items-center gap-3">
                <div class="h-3 w-3 rounded-full" style="background-color: {t.color}"></div>
                <p class="text-sm font-medium text-white">{t.name}</p>
                {#if t.icon}
                  <span class="text-xs text-neutral-500">{t.icon}</span>
                {/if}
              </div>
              <div class="flex items-center gap-2">
                {#if activityTypeDeleteId === t.id}
                  <span class="text-xs text-red-400">Delete?</span>
                  <Button size="sm" variant="danger" onclick={() => handleActivityTypeDelete(t.id)}>Yes</Button>
                  <Button size="sm" variant="ghost" onclick={() => (activityTypeDeleteId = null)}>No</Button>
                {:else}
                  <button onclick={() => openActivityTypeEdit(t)} class="text-neutral-600 opacity-0 transition hover:text-white group-hover:opacity-100"><Pencil size={14} /></button>
                  <button onclick={() => (activityTypeDeleteId = t.id)} class="text-neutral-600 opacity-0 transition hover:text-red-400 group-hover:opacity-100"><Trash2 size={14} /></button>
                {/if}
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </section>

    {#if showActivityTypeModal}
      <Modal title={editActivityTypeId ? 'Edit Activity Type' : 'New Activity Type'} onclose={() => (showActivityTypeModal = false)}>
        <form onsubmit={handleActivityTypeSave} class="space-y-4">
          <Input label="Name" bind:value={activityTypeForm.name} required />
          <Input label="Icon (Lucide name)" bind:value={activityTypeForm.icon} placeholder="e.g. phone, coffee, video" />
          <div>
            <label class="mb-1.5 block text-sm font-medium text-neutral-300">Color</label>
            <div class="flex items-center gap-3">
              <input type="color" bind:value={activityTypeForm.color} class="h-9 w-9 cursor-pointer rounded border border-neutral-700 bg-transparent" />
              <Input bind:value={activityTypeForm.color} />
            </div>
          </div>
          <div class="flex justify-end gap-3">
            <Button variant="ghost" onclick={() => (showActivityTypeModal = false)}>Cancel</Button>
            <Button type="submit" loading={activityTypeSaving}>Save</Button>
          </div>
        </form>
      </Modal>
    {/if}
  {/if}

  {#if activeTab === 'Security'}
    <section class="rounded-xl border border-neutral-800 bg-neutral-900 p-6">
      <div class="flex flex-col gap-1">
        <h2 class="text-lg font-semibold text-white">Two-Factor Authentication</h2>
        <p class="text-sm text-neutral-400">
          Add an extra layer of protection with an authenticator app and recovery codes.
        </p>
      </div>

      {#if setupError}
        <div class="mt-4 rounded-lg bg-red-950/50 px-4 py-3 text-sm text-red-400">
          {setupError}
        </div>
      {/if}

      {#if disableMessage}
        <div class="mt-4 rounded-lg bg-emerald-950/50 px-4 py-3 text-sm text-emerald-300">
          {disableMessage}
        </div>
      {/if}

      {#if disableError}
        <div class="mt-4 rounded-lg bg-red-950/50 px-4 py-3 text-sm text-red-400">
          {disableError}
        </div>
      {/if}

      <div class="mt-5 flex flex-wrap gap-3">
        <button
          type="button"
          disabled={setupLoading}
          class="rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-400 disabled:opacity-50"
          onclick={handleSetup}
        >
          {setupLoading ? 'Starting setup…' : 'Enable 2FA'}
        </button>
        <button
          type="button"
          disabled={disableLoading}
          class="rounded-lg border border-neutral-700 px-4 py-2 text-sm font-medium text-neutral-200 transition hover:border-neutral-500 disabled:opacity-50"
          onclick={handleDisable}
        >
          {disableLoading ? 'Disabling…' : 'Disable 2FA'}
        </button>
      </div>

      {#if setup}
        <div class="mt-6 grid gap-6 lg:grid-cols-[220px_1fr]">
          <div class="rounded-lg border border-neutral-800 bg-neutral-950 p-4">
            <p class="text-xs uppercase tracking-wide text-neutral-500">Scan QR Code</p>
            <img
              class="mt-3 w-full rounded-md border border-neutral-800 bg-white p-2"
              src={setup.qr_data_url}
              alt="CLARA 2FA QR code"
            />
            <p class="mt-3 text-xs text-neutral-500">Or enter this key:</p>
            <p class="mt-1 break-all text-xs text-neutral-200">{setup.provisioning_uri}</p>
          </div>

          <div class="space-y-4">
            <div class="rounded-lg border border-neutral-800 bg-neutral-950 p-4">
              <p class="text-xs uppercase tracking-wide text-neutral-500">Recovery Codes</p>
              <p class="mt-2 text-sm text-neutral-400">
                Save these codes somewhere safe. Each code can be used once.
              </p>
              <div class="mt-3 grid gap-2 sm:grid-cols-2">
                {#each setup.recovery_codes as code}
                  <div class="rounded-md border border-neutral-800 bg-neutral-900 px-3 py-2 text-sm font-mono text-neutral-200">
                    {code}
                  </div>
                {/each}
              </div>
            </div>

            <form onsubmit={handleConfirm} class="rounded-lg border border-neutral-800 bg-neutral-950 p-4">
              <p class="text-xs uppercase tracking-wide text-neutral-500">Verify Setup</p>

              {#if confirmError}
                <div class="mt-3 rounded-lg bg-red-950/50 px-3 py-2 text-sm text-red-400">
                  {confirmError}
                </div>
              {/if}

              {#if confirmSuccess}
                <div class="mt-3 rounded-lg bg-emerald-950/50 px-3 py-2 text-sm text-emerald-300">
                  Two-factor authentication enabled.
                </div>
              {/if}

              <div class="mt-3">
                <label for="confirm-code" class="mb-1.5 block text-sm font-medium text-neutral-300">
                  Authenticator code
                </label>
                <input
                  id="confirm-code"
                  type="text"
                  bind:value={confirmCode}
                  required
                  autocomplete="one-time-code"
                  class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white placeholder-neutral-500 outline-none transition focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
                  placeholder="123456"
                />
              </div>

              <button
                type="submit"
                disabled={confirmLoading}
                class="mt-4 rounded-lg bg-brand-500 px-4 py-2 text-sm font-medium text-white transition hover:bg-brand-400 disabled:opacity-50"
              >
                {confirmLoading ? 'Verifying…' : 'Confirm 2FA'}
              </button>
            </form>
          </div>
        </div>
      {/if}
    </section>

    <section class="space-y-4 rounded-xl border border-neutral-800 bg-neutral-900 p-6">
      <div class="flex items-center justify-between">
        <div>
          <h2 class="text-lg font-semibold text-white">Personal Access Tokens</h2>
          <p class="text-sm text-neutral-400">Tokens for API access. Treat them like passwords.</p>
        </div>
        <Button size="sm" onclick={openTokenCreate}>Create token</Button>
      </div>

      {#if tokensLoading}
        <p class="text-sm text-neutral-500">Loading tokens…</p>
      {:else if tokens.length === 0}
        <p class="text-sm text-neutral-500">No tokens created.</p>
      {:else}
        <div class="space-y-2">
          {#each tokens as tok (tok.id)}
            <div class="flex items-center justify-between rounded-lg border border-neutral-800 bg-neutral-950 px-3 py-2">
              <div>
                <p class="text-sm font-medium text-white">{tok.name}</p>
                <p class="text-xs text-neutral-500">
                  {tok.token_prefix}… · {tok.scopes.join(', ')} · Created {formatTokenDate(tok.created_at)}
                  {#if tok.last_used_at} · Last used {formatTokenDate(tok.last_used_at)}{/if}
                  {#if tok.expires_at} · Expires {formatTokenDate(tok.expires_at)}{/if}
                </p>
              </div>
              {#if revokeConfirmId === tok.id}
                <div class="flex items-center gap-2">
                  <span class="text-xs text-red-400">Revoke?</span>
                  <Button size="sm" variant="danger" onclick={() => handleTokenRevoke(tok.id)}>Yes</Button>
                  <Button size="sm" variant="ghost" onclick={() => (revokeConfirmId = null)}>No</Button>
                </div>
              {:else}
                <Button size="sm" variant="ghost" onclick={() => (revokeConfirmId = tok.id)}>
                  <Trash2 size={14} class="text-red-400" />
                </Button>
              {/if}
            </div>
          {/each}
        </div>
      {/if}
    </section>

    {#if showTokenModal}
      <Modal title={newToken ? 'Token Created' : 'Create Token'} onclose={() => (showTokenModal = false)}>
        {#if newToken}
          <div class="space-y-4">
            <div class="rounded-lg border border-amber-500/30 bg-amber-950/20 px-4 py-3 text-sm text-amber-300">
              Copy this token now — it won't be shown again.
            </div>
            <div class="flex items-center gap-2 rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2">
              <code class="flex-1 break-all text-sm text-white">{newToken.token}</code>
              <button onclick={copyToken} class="shrink-0 rounded p-1 text-neutral-400 transition hover:text-white">
                {#if tokenCopied}
                  <Check size={16} class="text-emerald-400" />
                {:else}
                  <Copy size={16} />
                {/if}
              </button>
            </div>
            <div class="flex justify-end">
              <Button onclick={() => (showTokenModal = false)}>Done</Button>
            </div>
          </div>
        {:else}
          <form onsubmit={handleTokenCreate} class="space-y-4">
            <Input label="Token name" bind:value={tokenForm.name} required />
            <div>
              <label class="mb-1.5 block text-sm font-medium text-neutral-300">Scopes</label>
              <div class="flex gap-3">
                <label class="flex items-center gap-2 text-sm text-neutral-300">
                  <input type="checkbox" checked={tokenForm.scopes.includes('read')} onchange={() => toggleScope('read')} class="h-4 w-4 accent-brand-500" />
                  Read
                </label>
                <label class="flex items-center gap-2 text-sm text-neutral-300">
                  <input type="checkbox" checked={tokenForm.scopes.includes('write')} onchange={() => toggleScope('write')} class="h-4 w-4 accent-brand-500" />
                  Write
                </label>
              </div>
            </div>
            <Input label="Expires at" type="date" bind:value={tokenForm.expires_at} />
            <div class="flex justify-end gap-3">
              <Button variant="ghost" onclick={() => (showTokenModal = false)}>Cancel</Button>
              <Button type="submit" loading={tokenSaving} disabled={!tokenForm.name || tokenForm.scopes.length === 0}>Create</Button>
            </div>
          </form>
        {/if}
      </Modal>
    {/if}
  {/if}

  {#if activeTab === 'Import/Export'}
    <section class="space-y-4 rounded-xl border border-neutral-800 bg-neutral-900 p-6">
      <input id="import-vcard" type="file" accept=".vcf,text/vcard" class="hidden" onchange={handleImportVcard} />
      <input id="import-csv" type="file" accept=".csv,text/csv" class="hidden" onchange={handleImportCsv} />

      {#if importMessage}
        <div class="rounded-lg bg-emerald-950/50 px-4 py-3 text-sm text-emerald-300">{importMessage}</div>
      {/if}
      {#if importError}
        <div class="rounded-lg bg-red-950/50 px-4 py-3 text-sm text-red-400">{importError}</div>
      {/if}

      <div class="space-y-2">
        <h2 class="text-lg font-semibold text-white">Import</h2>
        <div class="flex flex-wrap gap-3">
          <Button loading={importLoading} onclick={() => document.getElementById('import-vcard')?.click()}>
            Import vCard
          </Button>
          <Button loading={importLoading} variant="secondary" onclick={() => document.getElementById('import-csv')?.click()}>
            Import CSV
          </Button>
        </div>
      </div>

      <div class="space-y-2">
        <h2 class="text-lg font-semibold text-white">Export</h2>
        <div class="flex flex-wrap gap-3">
          <Button variant="secondary" onclick={() => importExportApi.exportVcard(vaultId)}>Export vCard</Button>
          <Button variant="secondary" onclick={() => importExportApi.exportCsv(vaultId)}>Export CSV</Button>
          <Button variant="secondary" onclick={() => importExportApi.exportJson(vaultId)}>Export JSON</Button>
        </div>
      </div>
    </section>
  {/if}
</div>
