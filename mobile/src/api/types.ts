export type Portal = 'indeed' | 'linkedin' | 'occ' | 'computrabajo' | 'glassdoor';

export type SearchParams = {
  portals: Portal[];
  max_results: number;
  refresh_cache: boolean;
  browser: boolean;
  research: boolean;
};

export type RunStatus = 'pending' | 'running' | 'completed' | 'failed';

export type RunRecord = {
  run_id: string;
  type: 'search' | 'extract_links' | 'apply_approved_dry_run';
  status: RunStatus;
  params: Record<string, unknown>;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  output_file: string;
  result_file: string | null;
  error: string | null;
  stderr: string;
};

export type ResultValue = string | number | boolean | null;

export type ResultSheet = {
  name: string;
  columns: string[];
  rows: Record<string, ResultValue>[];
};

export type BotJobsResults = {
  run_id: string | null;
  output_file: string;
  sheets: Record<string, ResultSheet>;
};
