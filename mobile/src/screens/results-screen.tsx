import { SymbolView } from 'expo-symbols';
import { useMemo, useState } from 'react';
import { Linking, Pressable, ScrollView, StyleSheet, View } from 'react-native';

import type { ResultSheet, ResultValue } from '@/api/types';
import { FeedbackBanner } from '@/components/feedback-banner';
import { Page } from '@/components/page';
import { ScreenHeader } from '@/components/screen-header';
import { ThemedText } from '@/components/themed-text';
import { useTheme } from '@/hooks/use-theme';
import { useBotJobs } from '@/state/botjobs-provider';

const SHEETS = [
  ['resumen_ejecucion', 'Resumen'],
  ['vacantes_detectadas', 'Detectadas'],
  ['preseleccionadas', 'Preseleccionadas'],
  ['descartadas', 'Descartadas'],
  ['aplicadas', 'Aplicadas'],
  ['requiere_intervencion', 'Intervención humana'],
] as const;

const DETAIL_FIELDS = [
  ['industria', 'Industria'],
  ['ubicacion', 'Ubicación'],
  ['modalidad', 'Modalidad'],
  ['salario', 'Salario'],
  ['horas_semana', 'Horas por semana'],
  ['seniority', 'Seniority'],
  ['idioma', 'Idioma'],
  ['matched_skills', 'Habilidades coincidentes'],
  ['email_contacto', 'Contacto'],
  ['estado_extraccion', 'Estado de extracción'],
  ['motivo_intervencion', 'Motivo de intervención'],
  ['accion_recomendada', 'Acción recomendada'],
  ['mensaje_corto_reclutador', 'Mensaje para reclutador'],
] as const;

export default function ResultsScreen() {
  const theme = useTheme();
  const { connected, results, activeRun, loading, error, refresh } = useBotJobs();
  const [selected, setSelected] = useState<string>('resumen_ejecucion');
  const sheet = results?.sheets[selected];

  return (
    <Page>
      <View style={styles.headerRow}>
        <ScreenHeader title="Resultados" connected={connected} />
        <Pressable accessibilityLabel="Actualizar resultados" onPress={() => void refresh()} style={({ pressed }) => [styles.iconButton, { borderColor: theme.border, backgroundColor: theme.surface, opacity: pressed ? 0.55 : 1 }]}>
          <SymbolView name={{ ios: 'arrow.clockwise', android: 'refresh', web: 'refresh' }} tintColor={theme.primary} size={20} />
        </Pressable>
      </View>
      <FeedbackBanner loading={loading} error={error} status={activeRun?.status === 'running' ? 'Actualizando resultados…' : undefined} />

      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={[styles.segments, { backgroundColor: theme.backgroundElement }]}>
        {SHEETS.map(([id, label]) => {
          const active = selected === id;
          const count = results?.sheets[id]?.rows.length ?? 0;
          return (
            <Pressable key={id} onPress={() => setSelected(id)} style={[styles.segment, active && { backgroundColor: theme.surface, borderColor: theme.border }]}>
              <ThemedText selectable type="smallBold" style={{ color: active ? theme.primary : theme.textSecondary }}>{label} · {count}</ThemedText>
            </Pressable>
          );
        })}
      </ScrollView>

      {!sheet || sheet.rows.length === 0 ? (
        <View style={[styles.empty, { borderColor: theme.border }]}>
          <SymbolView name={{ ios: 'tray', android: 'inbox', web: 'inbox' }} tintColor={theme.textSecondary} size={30} />
          <ThemedText selectable themeColor="textSecondary">No hay registros en esta vista.</ThemedText>
        </View>
      ) : selected === 'resumen_ejecucion' ? <Summary sheet={sheet} /> : (
        <View style={styles.list}>{sheet.rows.map((row, index) => <ResultCard key={`${selected}-${index}-${String(row.url || '')}`} row={row} />)}</View>
      )}
    </Page>
  );
}

function Summary({ sheet }: { sheet: ResultSheet }) {
  const theme = useTheme();
  return (
    <View style={styles.metricGrid}>
      {sheet.rows.map((row) => (
        <View key={String(row.metrica)} style={[styles.metric, { backgroundColor: theme.surface, borderColor: theme.border }]}>
          <ThemedText selectable style={styles.metricValue}>{String(row.valor ?? '')}</ThemedText>
          <ThemedText selectable type="small" themeColor="textSecondary">{humanize(String(row.metrica))}</ThemedText>
        </View>
      ))}
    </View>
  );
}

function ResultCard({ row }: { row: Record<string, ResultValue> }) {
  const theme = useTheme();
  const [expanded, setExpanded] = useState(false);
  const details = useMemo(() => DETAIL_FIELDS.flatMap(([key, label]) => {
    const value = row[key];
    return value === '' || value === null || value === undefined ? [] : [{ key, label, value }];
  }), [row]);
  const title = String(row.nombre_de_la_vacante || row.empresa || 'Registro');
  const subtitle = [row.empresa, row.portal, row.modalidad].filter(Boolean).join(' · ');

  return (
    <View style={[styles.card, { backgroundColor: theme.surface, borderColor: theme.border }]}>
      <Pressable onPress={() => setExpanded((value) => !value)} style={styles.cardHeader}>
        <View style={{ flex: 1, gap: 4 }}>
          <View style={styles.scoreRow}>
            {row.score !== '' && <ThemedText selectable type="smallBold" style={{ color: theme.primary, fontVariant: ['tabular-nums'] }}>{String(row.score)}/100</ThemedText>}
            {row.estado !== '' && <ThemedText selectable type="small" style={{ color: statusColor(String(row.estado), theme) }}>{humanize(String(row.estado))}</ThemedText>}
          </View>
          <ThemedText selectable style={styles.cardTitle}>{title}</ThemedText>
          {!!subtitle && <ThemedText selectable type="small" themeColor="textSecondary">{subtitle}</ThemedText>}
          {!!row.razon_menos_250 && <ThemedText selectable type="small">{String(row.razon_menos_250)}</ThemedText>}
        </View>
        <SymbolView name={{ ios: expanded ? 'chevron.up' : 'chevron.down', android: expanded ? 'expand_less' : 'expand_more', web: expanded ? 'expand_less' : 'expand_more' }} tintColor={theme.textSecondary} size={20} />
      </Pressable>
      {expanded && (
        <View style={[styles.details, { borderTopColor: theme.border }]}>
          {details.map(({ key, label, value }) => (
            <View key={key} style={styles.detailRow}>
              <ThemedText selectable type="small" themeColor="textSecondary" style={styles.detailLabel}>{label}</ThemedText>
              <ThemedText selectable type="small" style={{ flex: 1 }}>{String(value)}</ThemedText>
            </View>
          ))}
          {!!row.url && (
            <Pressable onPress={() => void Linking.openURL(String(row.url))} style={[styles.linkButton, { borderColor: theme.primary }]}>
              <SymbolView name={{ ios: 'arrow.up.right.square', android: 'open_in_new', web: 'open_in_new' }} tintColor={theme.primary} size={18} />
              <ThemedText selectable type="smallBold" style={{ color: theme.primary }}>Abrir vacante</ThemedText>
            </Pressable>
          )}
        </View>
      )}
    </View>
  );
}

function statusColor(status: string, theme: ReturnType<typeof useTheme>) {
  if (status.includes('preseleccionada') || status.includes('aplicada')) return theme.primary;
  if (status.includes('descartada') || status.includes('failed')) return theme.danger;
  return theme.warning;
}

const humanize = (value: string) => value.replaceAll('_', ' ').replace(/^./, (letter) => letter.toUpperCase());

const styles = StyleSheet.create({
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 12 },
  iconButton: { width: 44, height: 44, borderRadius: 8, borderWidth: 1, alignItems: 'center', justifyContent: 'center' },
  segments: { gap: 4, borderRadius: 8, padding: 4 },
  segment: { minHeight: 38, justifyContent: 'center', borderRadius: 6, borderWidth: 1, borderColor: 'transparent', paddingHorizontal: 12 },
  empty: { minHeight: 180, borderWidth: 1, borderStyle: 'dashed', borderRadius: 8, alignItems: 'center', justifyContent: 'center', gap: 10, padding: 24 },
  metricGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  metric: { width: '48%', minHeight: 104, justifyContent: 'space-between', borderWidth: 1, borderRadius: 8, padding: 14 },
  metricValue: { fontSize: 24, lineHeight: 30, fontWeight: '700', fontVariant: ['tabular-nums'] },
  list: { gap: 10 }, card: { borderWidth: 1, borderRadius: 8, overflow: 'hidden' },
  cardHeader: { flexDirection: 'row', alignItems: 'center', gap: 12, padding: 14 },
  cardTitle: { fontSize: 17, lineHeight: 22, fontWeight: '700' },
  scoreRow: { minHeight: 20, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10 },
  details: { borderTopWidth: StyleSheet.hairlineWidth, gap: 10, padding: 14 },
  detailRow: { flexDirection: 'row', gap: 12 }, detailLabel: { width: 120 },
  linkButton: { minHeight: 44, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, borderWidth: 1, borderRadius: 8, paddingHorizontal: 12 },
});
