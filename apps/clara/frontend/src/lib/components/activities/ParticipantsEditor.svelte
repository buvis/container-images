<script lang="ts">
  import { lookup } from '$state/lookup.svelte';
  import Button from '$components/ui/Button.svelte';
  import Input from '$components/ui/Input.svelte';
  import { Plus, X } from 'lucide-svelte';

  interface Props {
    participants: { contact_id: string; role?: string }[];
    vaultId: string;
  }

  let { participants = $bindable(), vaultId }: Props = $props();

  function addParticipant() {
    participants = [...participants, { contact_id: '', role: '' }];
  }

  function removeParticipant(index: number) {
    participants = participants.filter((_, i) => i !== index);
  }
</script>

<div class="space-y-2">
  {#each participants as participant, index}
    <div class="flex items-start gap-2">
      <div class="flex-1">
        <select
          bind:value={participant.contact_id}
          class="w-full rounded-lg border border-neutral-700 bg-neutral-800 px-3 py-2 text-sm text-white outline-none transition focus:border-brand-500 focus:ring-1 focus:ring-brand-500"
        >
          <option value="" disabled>Select contact</option>
          {#each lookup.contacts as contact}
            <option value={contact.id}>{contact.name}</option>
          {/each}
        </select>
      </div>
      <div class="flex-1">
        <Input
          placeholder="Role (optional)"
          bind:value={participant.role}
        />
      </div>
      <Button
        variant="ghost"
        class="h-9 w-9 shrink-0 p-0 text-neutral-400 hover:text-red-400"
        onclick={() => removeParticipant(index)}
        aria-label="Remove participant"
      >
        <X size={18} />
      </Button>
    </div>
  {/each}

  <Button
    variant="ghost"
    size="sm"
    onclick={addParticipant}
    class="text-neutral-400 hover:text-white"
  >
    <Plus size={16} />
    <span>Add participant</span>
  </Button>
</div>
