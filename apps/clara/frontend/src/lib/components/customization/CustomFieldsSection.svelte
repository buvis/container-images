<script lang="ts">
  import { customizationApi } from '$api/customization';
  import type { CustomField, CustomFieldValue } from '$lib/types/models';
  import Spinner from '$components/ui/Spinner.svelte';
  import { Check, X } from 'lucide-svelte';

  let { vaultId, entityType, entityId }: { vaultId: string; entityType: string; entityId: string } = $props();

  let definitions = $state<CustomField[]>([]);
  let values = $state<CustomFieldValue[]>([]);
  let loading = $state(true);
  let editingFieldId = $state<string | null>(null);
  let editValue = $state('');
  let saving = $state(false);

  $effect(() => {
    load();
  });

  async function load() {
    loading = true;
    const [defResult, vals] = await Promise.all([
      customizationApi.listCustomFields(vaultId, { scope: entityType, limit: 100 }),
      customizationApi.getFieldValues(vaultId, entityType, entityId)
    ]);
    definitions = defResult.items;
    values = vals;
    loading = false;
  }

  function getValueForField(defId: string): CustomFieldValue | undefined {
    return values.find((v) => v.definition_id === defId);
  }

  function displayValue(def: CustomField, val: CustomFieldValue | undefined): string {
    if (!val) return '—';
    try {
      const parsed = JSON.parse(val.value_json);
      if (def.data_type === 'boolean') return parsed ? 'Yes' : 'No';
      if (def.data_type === 'date') return new Date(parsed).toLocaleDateString();
      return String(parsed);
    } catch {
      return val.value_json;
    }
  }

  function startEdit(def: CustomField) {
    const val = getValueForField(def.id);
    if (val) {
      try {
        const parsed = JSON.parse(val.value_json);
        editValue = String(parsed);
      } catch {
        editValue = val.value_json;
      }
    } else {
      editValue = def.data_type === 'boolean' ? 'false' : '';
    }
    editingFieldId = def.id;
  }

  async function saveField(defId: string, dataType: string) {
    saving = true;
    try {
      let jsonValue: string;
      if (dataType === 'number') jsonValue = JSON.stringify(Number(editValue));
      else if (dataType === 'boolean') jsonValue = JSON.stringify(editValue === 'true');
      else jsonValue = JSON.stringify(editValue);

      const result = await customizationApi.setFieldValue(vaultId, {
        definition_id: defId,
        entity_type: entityType,
        entity_id: entityId,
        value_json: jsonValue
      });
      values = values.some((v) => v.definition_id === defId)
        ? values.map((v) => (v.definition_id === defId ? result : v))
        : [...values, result];
      editingFieldId = null;
    } finally {
      saving = false;
    }
  }
</script>

{#if loading}
  <div class="flex justify-center py-4"><Spinner /></div>
{:else if definitions.length === 0}
  <!-- no custom fields defined for this entity type -->
{:else}
  <section class="space-y-3 rounded-xl border border-neutral-800 bg-neutral-900 p-4">
    <h3 class="text-sm font-semibold text-neutral-400">Custom Fields</h3>
    <div class="space-y-2">
      {#each definitions as def (def.id)}
        {@const val = getValueForField(def.id)}
        <div class="flex items-center justify-between gap-3">
          <span class="text-sm text-neutral-400">{def.name}</span>
          {#if editingFieldId === def.id}
            <div class="flex items-center gap-2">
              {#if def.data_type === 'boolean'}
                <select bind:value={editValue} class="rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-sm text-white outline-none">
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              {:else if def.data_type === 'date'}
                <input type="date" bind:value={editValue} class="rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-sm text-white outline-none" />
              {:else if def.data_type === 'number'}
                <input type="number" bind:value={editValue} class="w-24 rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-sm text-white outline-none" />
              {:else if def.data_type === 'select'}
                {@const options = (() => { try { return JSON.parse(def.config_json ?? '[]'); } catch { return []; } })()}
                <select bind:value={editValue} class="rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-sm text-white outline-none">
                  <option value="">—</option>
                  {#each options as opt}
                    <option value={opt}>{opt}</option>
                  {/each}
                </select>
              {:else}
                <input type="text" bind:value={editValue} class="w-40 rounded border border-neutral-700 bg-neutral-800 px-2 py-1 text-sm text-white outline-none" />
              {/if}
              <button onclick={() => saveField(def.id, def.data_type)} disabled={saving} class="text-green-400 hover:text-green-300">
                <Check size={14} />
              </button>
              <button onclick={() => (editingFieldId = null)} class="text-neutral-500 hover:text-white">
                <X size={14} />
              </button>
            </div>
          {:else}
            <button onclick={() => startEdit(def)} class="text-sm text-white hover:text-brand-400">
              {displayValue(def, val)}
            </button>
          {/if}
        </div>
      {/each}
    </div>
  </section>
{/if}
