<script lang="ts">
  import { page } from "$app/state";
  import { browseIcon, closeMenuIcon, menuIcon, searchIcon } from "$lib/icons";
  import { selectedOptions } from "$lib/options.svelte";
  import type { AvailableOptions } from "$lib/types";
  import Fa from "svelte-fa";
  import Logo from "./Logo.svelte";

  interface Props {
    /** All available options. */
    availableOptions: AvailableOptions;
  }
  let { availableOptions }: Props = $props();

  let atSearch: boolean = $derived(
    page.url.pathname.startsWith("/search") || page.url.pathname == "/",
  );
  let atBrowse: boolean = $derived(page.url.pathname.startsWith("/browse"));
</script>

<!--
@component
The main menu drawer.
-->
<div class="drawer w-auto">
  <input id="my-drawer" type="checkbox" class="drawer-toggle" />
  <div class="drawer-content">
    <label for="my-drawer" class="drawer-button btn btn-ghost btn-sm">
      <Fa icon={menuIcon} />
    </label>
  </div>
  <div class="drawer-side z-99">
    <label for="my-drawer" aria-label="close sidebar" class="drawer-overlay"
    ></label>
    <div class="menu min-h-full w-80 bg-base-200 p-4 text-base-content">
      <div class="flex w-full items-center gap-4">
        <label for="my-drawer" class="drawer-button btn btn-ghost btn-sm">
          <Fa icon={closeMenuIcon} />
        </label>
        <Logo small />
      </div>

      <div class="divider my-2"></div>

      <!-- navigation -->
      <ul class="menu w-full p-0">
        <li>
          <a
            class={[atSearch && "menu-active pointer-events-none", "px-0"]}
            href="/search">
            <Fa icon={searchIcon} class="mx-2 w-4" />Search
          </a>
        </li>
        <li>
          <a
            class={[atBrowse && "menu-active pointer-events-none", "px-0"]}
            href="/browse">
            <Fa icon={browseIcon} class="mx-2 w-4" />Browse
          </a>
        </li>
      </ul>

      <div class="divider my-2"></div>

      <!-- search settings -->
      <fieldset class="fieldset gap-4">
        <legend class="fieldset-legend">Search settings</legend>

        <label class="fieldset-label flex flex-col items-start">
          Query language
          <select
            class="select w-full select-sm"
            name="language"
            bind:value={selectedOptions.queryLanguage}>
            {#each availableOptions.queryLanguages as language}
              <option value={language}>{language}</option>
            {/each}
          </select>
        </label>

        <label class="fieldset-label flex flex-col items-start">
          Search only in
          <div
            id="filter-corpora"
            class="menu w-full gap-2 rounded-box border border-base-300 bg-base-100 text-sm">
            {#each availableOptions.corpusNames as corpusName}
              <label>
                <input
                  type="checkbox"
                  class="toggle mr-2 toggle-sm"
                  value={corpusName}
                  bind:group={selectedOptions.corpusNames}
                  name="corpus" />
                {corpusName}
              </label>
            {/each}
          </div>
        </label>
      </fieldset>

      <div class="my-2"></div>

      <!-- browse settings -->
      <fieldset class="fieldset gap-4">
        <legend class="fieldset-legend">Browse settings</legend>

        <label class="fieldset-label flex flex-col items-start">
          <div class="flex w-full flex-row justify-between">
            <span>Items per page</span>
            <span class="pr-2">{selectedOptions.itemsPerPage}</span>
          </div>
          <input
            type="range"
            min="5"
            max="100"
            bind:value={selectedOptions.itemsPerPage}
            class="range range-sm"
            step="5" />
        </label>

        <label class="fieldset-label flex flex-col items-start">
          <div class="flex w-full flex-row justify-between">
            <span>Snippet length</span>
            <span class="pr-2">{selectedOptions.snippetLength}</span>
          </div>
          <input
            type="range"
            min="50"
            max="1000"
            bind:value={selectedOptions.snippetLength}
            class="range range-sm"
            step="10" />
        </label>
      </fieldset>
    </div>
  </div>
</div>
