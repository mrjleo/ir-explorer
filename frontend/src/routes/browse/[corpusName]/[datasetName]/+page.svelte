<script lang="ts">
  import type { PageProps } from "./$types";
  import PaginatedList from "$lib/components/browse/PaginatedList.svelte";
  import Fa from "svelte-fa";
  import { queryIcon } from "$lib/icons";
  import type { Paginated, Query } from "$lib/types";
  import { page } from "$app/state";

  let { data }: PageProps = $props();

  const getTargetLink = (q: Query) =>
    `/browse/${page.params.corpusName}/${page.params.datasetName}?${new URLSearchParams({ query_id: q.id })}`;

  async function getPage(num_items: number, offset: number) {
    const searchParams = new URLSearchParams({
      corpus_name: page.params.corpusName,
      dataset_name: page.params.datasetName,
      num_results: num_items.toString(),
      offset: offset.toString(),
    });

    const res = await fetch("/api/queries?" + searchParams);
    return (await res.json()) as Paginated<Query>;
  }
</script>

{#if data.query !== null}
  <div class="collapse mb-4 border border-base-300 bg-base-200">
    <input type="checkbox" checked />
    <div class="collapse-title flex flex-row items-center gap-2">
      <Fa icon={queryIcon} />
      {data.query.id}
    </div>
    <div class="collapse-content text-sm">
      {data.query.text}
    </div>
  </div>
{:else}
  <PaginatedList {getPage} {getTargetLink} itemsPerPage={10}>
    {#snippet head()}
      <p class="flex flex-row items-center gap-2">
        <Fa icon={queryIcon} />Queries
      </p>
    {/snippet}
    {#snippet item(q: Query)}
      {q.id} ({q.num_relevant_documents} relevant documents)
    {/snippet}
  </PaginatedList>
{/if}
