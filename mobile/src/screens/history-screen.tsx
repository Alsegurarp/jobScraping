import { SymbolView } from 'expo-symbols';
import { router } from 'expo-router';
import { Pressable, StyleSheet, View } from 'react-native';

import type { RunRecord } from '@/api/types';
import { FeedbackBanner } from '@/components/feedback-banner';
import { Page } from '@/components/page';
import { ScreenHeader } from '@/components/screen-header';
import { ThemedText } from '@/components/themed-text';
import { useTheme } from '@/hooks/use-theme';
import { useBotJobs } from '@/state/botjobs-provider';

export default function HistoryScreen() {
  const theme = useTheme();
  const { connected, runs, loading, error, refresh, loadRunResults } = useBotJobs();
  const openRun = async (run: RunRecord) => {
    if (run.status !== 'completed') return;
    await loadRunResults(run);
    router.push('/results');
  };

  return (
    <Page>
      <View style={styles.headerRow}>
        <ScreenHeader title="Historial" connected={connected} />
        <Pressable accessibilityLabel="Actualizar historial" onPress={() => void refresh()} style={({ pressed }) => [styles.iconButton, { backgroundColor: theme.surface, borderColor: theme.border, opacity: pressed ? 0.55 : 1 }]}>
          <SymbolView name={{ ios: 'arrow.clockwise', android: 'refresh', web: 'refresh' }} tintColor={theme.primary} size={20} />
        </Pressable>
      </View>
      <FeedbackBanner loading={loading} error={error} />
      <View style={styles.list}>
        {runs.map((run) => (
          <Pressable key={run.run_id} disabled={run.status !== 'completed'} onPress={() => void openRun(run)} style={({ pressed }) => [styles.run, { backgroundColor: theme.surface, borderColor: theme.border, opacity: pressed ? 0.65 : 1 }]}>
            <View style={[styles.runIcon, { backgroundColor: theme.backgroundElement }]}>
              <SymbolView name={{ ios: iconForType(run.type), android: 'history', web: 'history' }} tintColor={theme.primary} size={22} />
            </View>
            <View style={{ flex: 1, gap: 4 }}>
              <View style={styles.titleRow}>
                <ThemedText selectable type="smallBold">{typeLabel(run.type)}</ThemedText>
                <ThemedText selectable type="smallBold" style={{ color: statusColor(run.status, theme) }}>{statusLabel(run.status)}</ThemedText>
              </View>
              <ThemedText selectable type="small" themeColor="textSecondary">{formatDate(run.created_at)}</ThemedText>
              {run.type === 'search' && <ThemedText selectable type="small" themeColor="textSecondary">{formatSearchParams(run.params)}</ThemedText>}
              {!!run.error && <ThemedText selectable type="small" style={{ color: theme.danger }}>{run.error}</ThemedText>}
            </View>
            {run.status === 'completed' && <SymbolView name={{ ios: 'chevron.right', android: 'chevron_right', web: 'chevron_right' }} tintColor={theme.textSecondary} size={18} />}
          </Pressable>
        ))}
        {!runs.length && <ThemedText selectable themeColor="textSecondary">Aún no hay ejecuciones registradas.</ThemedText>}
      </View>
    </Page>
  );
}

const typeLabel = (type: string) => ({ search: 'Búsqueda', extract_links: 'Extracción de links', apply_approved_dry_run: 'Simulación de aplicaciones' }[type] || type);
const statusLabel = (status: string) => ({ pending: 'Pendiente', running: 'Ejecutando', completed: 'Completada', failed: 'Fallida' }[status] || status);
const iconForType = (type: string) => type === 'search' ? 'magnifyingglass' : type === 'extract_links' ? 'link' : 'doc.text.magnifyingglass';
const formatDate = (value: string) => new Intl.DateTimeFormat('es-MX', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));
const formatSearchParams = (params: Record<string, unknown>) => `${Array.isArray(params.portals) ? params.portals.join(', ') : ''} · ${params.max_results || 0} resultados`;

function statusColor(status: string, theme: ReturnType<typeof useTheme>) {
  if (status === 'completed') return theme.primary;
  if (status === 'failed') return theme.danger;
  return theme.warning;
}

const styles = StyleSheet.create({
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 12 },
  iconButton: { width: 44, height: 44, borderWidth: 1, borderRadius: 8, alignItems: 'center', justifyContent: 'center' },
  list: { gap: 10 },
  run: { minHeight: 82, flexDirection: 'row', alignItems: 'center', gap: 12, borderWidth: 1, borderRadius: 8, padding: 12 },
  runIcon: { width: 42, height: 42, borderRadius: 8, alignItems: 'center', justifyContent: 'center' },
  titleRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 10 },
});
