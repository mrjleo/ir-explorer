<script lang="ts" generics="T">
  import { goToIcon, matchIcon, orderAscIcon, orderDescIcon } from "$lib/icons";
  import type { OrderByOption, Paginated } from "$lib/types";
  import { onMount, type Snippet } from "svelte";
  import Fa from "svelte-fa";
  import List from "./List.svelte";

  const {
    getPage,
    headTitle,
    item,
    getTargetLink,
    itemsPerPage,
    loadFirstPage = true,
    orderByOptions = [],
    goToTarget = null,
    goToName = null,
  }: {
    getPage: (
      match: string | null,
      order_by: string | null,
      desc: boolean,
      num_items: number,
      offset: number,
    ) => Promise<Paginated<T>>;
    headTitle: Snippet;
    item: Snippet<[T]>;
    getTargetLink: (listItem: T) => string;
    itemsPerPage: number;
    loadFirstPage?: boolean;
    orderByOptions?: OrderByOption[];
    goToTarget?: string | null;
    goToName?: string | null;
  } = $props();

  let listItems: T[] = $state([]);
  let working = $state(false);
  let numItemsDisplayed = $derived(listItems.length);
  let totalNumItems = $state(0);
  let loaded = $state(false);
  let match = $state("");
  let matchTrimmed = $derived(match.trim());

  let promiseNextPage: Promise<Paginated<T>> | null = null;
  let abortToken = { abort: function () {} };

  let orderByValue = $state(null);
  let desc = $state(true);

  async function showNextPage(waitTime: number = 0) {
    working = true;

    if (promiseNextPage != null) {
      abortToken.abort();
    }

    promiseNextPage = new Promise<Paginated<T>>(async (resolve, reject) => {
      let aborted = false;
      abortToken.abort = function () {
        reject();
        aborted = true;
      };

      // wait for a specified time so we can abort before fetching the results
      await new Promise((resolve) => setTimeout(resolve, waitTime));
      if (aborted) {
        return;
      }

      const nextPage = await getPage(
        matchTrimmed.length > 0 ? matchTrimmed : null,
        orderByValue,
        desc,
        itemsPerPage,
        listItems.length,
      );
      resolve(nextPage);
    });

    promiseNextPage.then((nextPage) => {
      listItems = [...listItems, ...nextPage.items];
      totalNumItems = nextPage.total_num_items;
      working = false;
      loaded = true;
    });
  }

  async function reset(waitTime: number = 0) {
    listItems = [];
    loaded = false;
    await showNextPage(waitTime);
  }

  if (loadFirstPage) {
    onMount(showNextPage);
  }
</script>

<div class="mb-2 flex flex-col justify-center">
  <List bind:listItems {headTitle} {item} {getTargetLink}>
    {#snippet headItems()}
      <div class="flex flex-col gap-2 md:flex-row">
        <!-- match -->
        <label class="input input-sm w-full md:w-fit">
          <span class="text-sm">
            <Fa icon={matchIcon} />
          </span>
          <input
            type="text"
            class="w-full md:w-32"
            placeholder="Match..."
            bind:value={match}
            oninput={async () => {
              await reset(1000);
            }} />
        </label>

        <!-- order by -->
        <div class="join w-full md:w-fit">
          <!-- hide select if there are no options to order by -->
          {#if orderByOptions.length > 0}
            <select
              class="select join-item w-full select-sm md:w-fit"
              bind:value={orderByValue}
              onchange={async () => {
                await reset();
              }}>
              <option value={null} selected>Order by...</option>
              {#each orderByOptions as orderByOption}
                <option value={orderByOption.option}
                  >{orderByOption.name}</option>
              {/each}
            </select>
          {/if}

          <!-- hide desc\asc selection if nothing is selected -->
          {#if orderByValue != null}
            <label
              for="order-desc"
              class="btn join-item gap-0 border border-base-300 btn-sm has-checked:btn-primary">
              <input
                class="w-0 opacity-0"
                type="radio"
                id="order-desc"
                name="radio-order"
                value={true}
                onchange={async () => {
                  await reset();
                }}
                bind:group={desc}
                checked />
              <Fa icon={orderDescIcon} />
            </label>
            <label
              for="order-asc"
              class="btn join-item gap-0 border border-base-300 btn-sm has-checked:btn-primary">
              <input
                class="w-0 opacity-0"
                type="radio"
                id="order-asc"
                name="radio-order"
                value={false}
                onchange={async () => {
                  await reset();
                }}
                bind:group={desc} />
              <Fa icon={orderAscIcon} />
            </label>
          {/if}
        </div>

        {#if goToTarget !== null && goToName !== null}
          <!-- go to -->
          <form class="join w-full md:w-fit" action={goToTarget}>
            <input
              type="text"
              name={goToName}
              class="input input-sm join-item w-full md:w-24"
              placeholder="Go to ID..." />
            <button class="btn join-item btn-sm btn-primary" type="submit"
              ><Fa icon={goToIcon} /></button>
          </form>
        {/if}
      </div>
    {/snippet}
  </List>

  <!-- number of items and "more" button -->
  <div class="mx-auto join rounded-t-none">
    {#if loaded}
      <p
        class="join-item flex h-6 items-center rounded-t-none bg-neutral px-2 text-sm text-neutral-content shadow">
        Showing {numItemsDisplayed.toLocaleString()} of {totalNumItems.toLocaleString()}
      </p>
    {/if}
    {#if !working && numItemsDisplayed < totalNumItems}
      <button
        class="btn join-item h-6 w-12 rounded-t-none shadow btn-sm btn-primary"
        disabled={working}
        onclick={async () => {
          await showNextPage();
        }}
        >More
      </button>
    {/if}
    {#if working}
      <div
        class="join-item flex h-6 w-12 items-center justify-center rounded-t-none bg-base-300 shadow">
        <span class={[working && "loading loading-xs"]}></span>
      </div>
    {/if}
  </div>
</div>
