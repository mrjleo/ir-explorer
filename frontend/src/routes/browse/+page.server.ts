import { getCorpora } from "$lib/server/backend";
import type { Corpus, ListItem } from "$lib/types";
import type { PageServerLoad } from "./$types";

export const load: PageServerLoad = async () => {
  let listItems: ListItem<Corpus>[] = [];
  for (const corpus of await getCorpora()) {
    listItems.push({
      target: "/browse/" + corpus.name,
      item: corpus,
    });
  }
  return { corpusList: listItems };
};
