<script lang="ts">
  import IconWithText from "$lib/components/IconWithText.svelte";
  import NavProgress from "$lib/components/NavProgress.svelte";
  import { faGithub } from "@fortawesome/free-brands-svg-icons";
  import "../app.css";

  let { children } = $props();
</script>

<svelte:head>
  <title>IR explorer</title>
</svelte:head>

<NavProgress />
<div
  class="grid max-h-full min-h-screen w-screen max-w-full grid-rows-[1fr_auto]">
  <div>
    {@render children()}
  </div>

  <footer
    class="flex w-full flex-col justify-center gap-2 border-t border-base-300 bg-base-200 px-4 py-2 text-sm md:flex-row md:items-center">
    <a
      class="badge font-mono text-xs text-neutral-content badge-neutral"
      href="https://github.com/ir-explorer">
      <IconWithText icon={faGithub} text="ir-explorer" />
    </a>
    <p class="hidden md:block">&bull;</p>
    <p>
      Made with <a class="link" href="https://www.paradedb.com/">ParadeDB</a>,
      <a class="link" href="https://litestar.dev/">Litestar</a>, and
      <a class="link" href="https://svelte.dev/">SvelteKit</a>.
    </p>
  </footer>
</div>
