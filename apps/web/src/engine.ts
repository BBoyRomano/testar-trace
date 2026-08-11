import { mapAnalysisResult, mapRequirements, mapStateModels } from "./mapping.ts";
import type {
  AdapterDescriptor,
  AnalysisProgress,
  AnalysisResult,
  MethodDescriptor,
  RawSource,
  RequirementBundle,
  StateModelBundle,
} from "./types.ts";
import { WorkerClient } from "./worker/worker-client.ts";

export type EngineCatalog = {
  requirement_adapters: AdapterDescriptor[];
  state_model_adapters: AdapterDescriptor[];
  methods: MethodDescriptor[];
};

const worker = new WorkerClient();
let catalogPromise: Promise<EngineCatalog> | null = null;

export function fetchCatalog(): Promise<EngineCatalog> {
  catalogPromise ??= worker.request<EngineCatalog>("catalog").catch((error: unknown) => {
    catalogPromise = null;
    throw error;
  });
  return catalogPromise;
}

export async function parseRequirements(input: {
  sources: RawSource[];
  name: string;
  sourceKind: RequirementBundle["sourceKind"];
  adapterId: string;
}): Promise<RequirementBundle> {
  const data = await worker.request<Parameters<typeof mapRequirements>[0]["data"]>(
    "parse-requirements",
    { sources: input.sources, adapter: input.adapterId || undefined },
  );
  return mapRequirements({ ...input, data });
}

export async function parseStateModels(input: {
  sources: RawSource[];
  name: string;
  adapterId: string;
}): Promise<StateModelBundle> {
  const data = await worker.request<Parameters<typeof mapStateModels>[0]["data"]>(
    "parse-state-models",
    {
      sources: input.sources,
      adapter: input.adapterId || undefined,
      collection_id: crypto.randomUUID(),
      title: input.name,
    },
  );
  return mapStateModels({ ...input, data });
}

export async function analyze(input: {
  resultId: string;
  method: MethodDescriptor;
  requirements: RequirementBundle;
  stateModels: StateModelBundle;
  signal: AbortSignal;
  onProgress?: (progress: AnalysisProgress) => void;
}): Promise<AnalysisResult> {
  const requestOptions: {
    signal: AbortSignal;
    onProgress?: (progress: AnalysisProgress) => void;
  } = { signal: input.signal };
  if (input.onProgress !== undefined) requestOptions.onProgress = input.onProgress;
  const data = await worker.request<Parameters<typeof mapAnalysisResult>[0]["data"]>(
    "analyze",
    {
      method: input.method.id,
      requirements: {
        sources: input.requirements.sources,
        adapter: input.requirements.adapterId || undefined,
      },
      state_models: {
        sources: input.stateModels.sources,
        adapter: input.stateModels.adapterId || undefined,
        collection_id: input.stateModels.id,
        title: input.stateModels.name,
      },
    },
    requestOptions,
  );
  return mapAnalysisResult({ data, ...input });
}
