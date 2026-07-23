import { CvDocuments } from '@/components/cv-documents';
import { Page } from '@/components/page';
import { ScreenHeader } from '@/components/screen-header';
import { useBotJobs } from '@/state/botjobs-provider';

export default function DocumentsScreen() {
  const { connected } = useBotJobs();
  return <Page><ScreenHeader title="Documentos" connected={connected} /><CvDocuments /></Page>;
}
