import { getAvailableOptions } from "$lib/server/backend";
import type { LayoutServerLoad } from "./$types";

export const load: LayoutServerLoad = async () => {
  return {
    availableOptions: await getAvailableOptions(),
  };
};
