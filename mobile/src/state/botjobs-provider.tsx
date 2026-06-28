import { botJobsApi } from '@/api/client';
import type { BotJobsResults, RunRecord, SearchParams } from '@/api/types';
import { createContext, ReactNode, use, useCallback, useEffect, useMemo, useState } from 'react';

type BotJobsState = {
  connected: boolean;
  runs: RunRecord[];
  activeRun: RunRecord | null;
  results: BotJobsResults | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  startSearch: (params: SearchParams) => Promise<boolean>;
  startExtractLinks: (params: { browser: boolean; research: boolean }) => Promise<boolean>;
  startApplyDryRun: () => Promise<boolean>;
  loadRunResults: (run: RunRecord) => Promise<void>;
};

const BotJobsContext = createContext<BotJobsState | null>(null);
const wait = (milliseconds: number) => new Promise((resolve) => setTimeout(resolve, milliseconds));

export function BotJobsProvider({ children }: { children: ReactNode }) {
  const [connected, setConnected] = useState(false);
  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [activeRun, setActiveRun] = useState<RunRecord | null>(null);
  const [results, setResults] = useState<BotJobsResults | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await botJobsApi.health();
      setConnected(true);
      const [runItems, latest] = await Promise.all([
        botJobsApi.runs(),
        botJobsApi.latestResults().catch(() => null),
      ]);
      setRuns(runItems);
      if (latest) setResults(latest);
    } catch (caught) {
      setConnected(false);
      setError(caught instanceof Error ? caught.message : 'No se pudo cargar BotJobs');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const followRun = useCallback(async (initial: RunRecord) => {
    setActiveRun(initial);
    let current = initial;
    while (current.status === 'pending' || current.status === 'running') {
      await wait(1500);
      current = await botJobsApi.run(current.run_id);
      setActiveRun(current);
    }
    setRuns(await botJobsApi.runs());
    if (current.status === 'completed') {
      setResults(await botJobsApi.runResults(current.run_id));
      return true;
    } else {
      setError(current.error || current.stderr || 'La ejecución no terminó correctamente');
      return false;
    }
  }, []);

  const execute = useCallback(
    async (starter: () => Promise<RunRecord>) => {
      setLoading(true);
      setError(null);
      try {
        return await followRun(await starter());
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : 'No se pudo ejecutar la acción');
        return false;
      } finally {
        setLoading(false);
      }
    },
    [followRun],
  );

  const loadRunResults = useCallback(async (run: RunRecord) => {
    setLoading(true);
    setError(null);
    setActiveRun(run);
    try {
      setResults(await botJobsApi.runResults(run.run_id));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'No se pudieron cargar los resultados');
      throw caught;
    } finally {
      setLoading(false);
    }
  }, []);

  const value = useMemo<BotJobsState>(
    () => ({
      connected,
      runs,
      activeRun,
      results,
      loading,
      error,
      refresh,
      startSearch: (params) => execute(() => botJobsApi.search(params)),
      startExtractLinks: (params) => execute(() => botJobsApi.extractLinks(params)),
      startApplyDryRun: () => execute(() => botJobsApi.applyDryRun()),
      loadRunResults,
    }),
    [activeRun, connected, error, execute, loadRunResults, loading, refresh, results, runs],
  );

  return <BotJobsContext value={value}>{children}</BotJobsContext>;
}

export function useBotJobs() {
  const context = use(BotJobsContext);
  if (!context) throw new Error('useBotJobs must be used inside BotJobsProvider');
  return context;
}
