<script lang="ts">
  import type { LayoutProps } from "./$types";
  import { page } from "$app/state";
  import SearchBar from "$lib/components/search/SearchBar.svelte";
  import Header from "$lib/components/Header.svelte";

  let { data, children }: LayoutProps = $props();
  let searchInit = $derived(page.url.searchParams.get("q"));
  let languageInit = $derived(page.url.searchParams.get("language"));
  let selectedCorporaInit = $derived(page.url.searchParams.getAll("corpus"));
</script>

<Header>
  <div class="w-2xl">
    <SearchBar
      corpora={data.corpora}
      {searchInit}
      {languageInit}
      {selectedCorporaInit} />
  </div>
</Header>

<div class="mx-4 mt-20 mb-4 max-w-full">
  <div class="mx-auto max-w-5xl">
    {@render children()}
  </div>
</div>
