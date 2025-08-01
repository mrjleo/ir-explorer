import { getDatasets, getDocument } from "$lib/server/backend";
import type { Dataset, Document } from "$lib/types";
import type { PageServerLoad } from "./$types";

export const load: PageServerLoad = async ({ params, url }) => {
  let document: Document | null = null;
  let datasetList: Dataset[] | null = null;

  // if a document ID is specified, return that document
  const documentId = url.searchParams.get("documentId");
  if (documentId !== null) {
    try {
      document = await getDocument(params.corpusName, documentId);
    } catch {
      document = null;
    }
  }

  // if there is no document to display, we need the dataset list
  if (document === null) {
    datasetList = await getDatasets(params.corpusName);
  }

  return { document: document, datasetList: datasetList };
};
