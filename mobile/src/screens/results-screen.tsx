import { SymbolView } from 'expo-symbols';
import { useEffect, useMemo, useState } from 'react';
import { Linking, Pressable, ScrollView, StyleSheet, View } from 'react-native';

import type { CvDocument, ResultSheet, ResultValue } from '@/api/types';
import { botJobsApi } from '@/api/client';
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
  ['aplicaciones', 'Seguimiento'],
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
  ['estado_aplicacion', 'Estado de aplicación'],
  ['resultado_aplicacion', 'Resultado de aplicación'],
  ['fecha_aplicacion', 'Fecha de aplicación'],
] as const;

export default function ResultsScreen() {
  const theme = useTheme();
  const { connected, results, activeRun, loading, error, refresh } = useBotJobs();
  const [selected, setSelected] = useState<string>('resumen_ejecucion');
  const [cvs, setCvs] = useState<CvDocument[]>([]);
  const sheet = results?.sheets[selected];
  useEffect(() => { void botJobsApi.cvs().then(setCvs).catch(() => undefined); }, []);

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
        <View style={styles.list}>{sheet.rows.map((row, index) => <ResultCard key={`${selected}-${index}-${String(row.url || '')}`} row={row} cvs={cvs} />)}</View>
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

function ResultCard({ row, cvs }: { row: Record<string, ResultValue>; cvs: CvDocument[] }) {
  const theme = useTheme();
  const [expanded, setExpanded] = useState(false);
  const [decision, setDecision] = useState(String(row.decision_usuario || ''));
  const [decisionLoading, setDecisionLoading] = useState(false);
  const [decisionError, setDecisionError] = useState<string | null>(null);
  const [selectedCv, setSelectedCv] = useState(String(row.cv_id || ''));
  const [letter, setLetter] = useState<string | null>(null);
  const [letterError, setLetterError] = useState<string | null>(null);
  const [letterLoading, setLetterLoading] = useState(false);
  const details = useMemo(() => DETAIL_FIELDS.flatMap(([key, label]) => {
    const value = row[key];
    return value === '' || value === null || value === undefined ? [] : [{ key, label, value }];
  }), [row]);
  const title = String(row.nombre_de_la_vacante || row.empresa || 'Registro');
  const subtitle = [row.empresa, row.portal, row.modalidad].filter(Boolean).join(' · ');
  const letterId = String(row.carta_id || '');
  const url = String(row.url || '');
  const evidenceId = String(row.evidencia_aplicacion || '').match(/([a-f0-9]{16})\.png$/)?.[1] || '';

  const toggleLetter = async () => {
    if (letter !== null) {
      setLetter(null);
      return;
    }
    setLetterLoading(true);
    setLetterError(null);
    try {
      setLetter((await botJobsApi.letter(letterId)).content);
    } catch (error) {
      setLetterError(error instanceof Error ? error.message : 'No se pudo cargar la carta');
    } finally {
      setLetterLoading(false);
    }
  };

  const saveDecision = async (value: 'aprobada' | 'descartada' | 'revision') => {
    if (!url) return;
    setDecisionLoading(true);
    setDecisionError(null);
    try {
      await botJobsApi.decideJob({ url, decision: value, cv_id: selectedCv || undefined });
      setDecision(value);
    } catch (error) {
      setDecisionError(error instanceof Error ? error.message : 'No se pudo guardar la decision');
    } finally {
      setDecisionLoading(false);
    }
  };

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
          {!!decision && <ThemedText selectable type="smallBold" style={{ color: statusColor(decision, theme) }}>Decision: {humanize(decision)}</ThemedText>}
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
          {!!url && (
            <View style={styles.decisionRow}>
              {[
                ['aprobada', 'Aprobar', theme.primary],
                ['descartada', 'Descartar', theme.danger],
                ['revision', 'Revisar', theme.warning],
              ].map(([value, label, color]) => (
                <Pressable key={value} disabled={decisionLoading} onPress={() => void saveDecision(value as 'aprobada' | 'descartada' | 'revision')} style={[styles.decisionButton, { borderColor: color, backgroundColor: decision === value ? color : 'transparent', opacity: decisionLoading ? 0.55 : 1 }]}>
                  <ThemedText selectable type="smallBold" style={{ color: decision === value ? theme.primaryText : color }}>{label}</ThemedText>
                </Pressable>
              ))}
            </View>
          )}
          {!!decisionError && <ThemedText selectable type="small" style={{ color: theme.danger }}>{decisionError}</ThemedText>}
          {!!url && cvs.length > 0 && (
            <View style={{ gap: 8 }}>
              <ThemedText selectable type="smallBold">CV para esta vacante</ThemedText>
              <View style={styles.decisionRow}>
                {cvs.map((cv) => (
                  <Pressable
                    key={cv.cv_id}
                    accessibilityRole="radio"
                    accessibilityState={{ selected: selectedCv === cv.cv_id }}
                    onPress={() => setSelectedCv(cv.cv_id)}
                    style={[styles.cvChoice, { borderColor: selectedCv === cv.cv_id ? theme.primary : theme.border }]}>
                    <ThemedText selectable type="small" numberOfLines={1} style={{ color: selectedCv === cv.cv_id ? theme.primary : theme.text }}>{cv.filename}</ThemedText>
                  </Pressable>
                ))}
              </View>
              <ThemedText selectable type="small" themeColor="textSecondary">Se guarda al aprobar; sin selección se usa el CV activo.</ThemedText>
            </View>
          )}
          <View style={styles.actions}>
            {!!url && (
              <Pressable onPress={() => void Linking.openURL(url)} style={[styles.linkButton, { borderColor: theme.primary }]}>
                <SymbolView name={{ ios: 'arrow.up.right.square', android: 'open_in_new', web: 'open_in_new' }} tintColor={theme.primary} size={18} />
                <ThemedText selectable type="smallBold" style={{ color: theme.primary }}>Abrir vacante</ThemedText>
              </Pressable>
            )}
            {!!letterId && (
              <Pressable disabled={letterLoading} onPress={() => void toggleLetter()} style={[styles.linkButton, { borderColor: theme.info, opacity: letterLoading ? 0.55 : 1 }]}>
                <SymbolView name={{ ios: 'doc.text', android: 'description', web: 'description' }} tintColor={theme.info} size={18} />
                <ThemedText selectable type="smallBold" style={{ color: theme.info }}>{letterLoading ? 'Cargando carta…' : letter === null ? 'Ver carta de empleo' : 'Ocultar carta'}</ThemedText>
              </Pressable>
            )}
            {!!evidenceId && (
              <Pressable onPress={() => void Linking.openURL(botJobsApi.evidenceUrl(evidenceId))} style={[styles.linkButton, { borderColor: theme.info }]}>
                <SymbolView name={{ ios: 'photo', android: 'image', web: 'image' }} tintColor={theme.info} size={18} />
                <ThemedText selectable type="smallBold" style={{ color: theme.info }}>Ver evidencia</ThemedText>
              </Pressable>
            )}
          </View>
          {!!letterError && <ThemedText selectable type="small" style={{ color: theme.danger }}>{letterError}</ThemedText>}
          {letter !== null && (
            <View style={[styles.letter, { backgroundColor: theme.backgroundElement, borderColor: theme.border }]}>
              <ThemedText selectable type="smallBold">Carta de empleo</ThemedText>
              <ThemedText selectable type="small">{letter}</ThemedText>
            </View>
          )}
        </View>
      )}
    </View>
  );
}

function statusColor(status: string, theme: ReturnType<typeof useTheme>) {
  if (status.includes('preseleccionada') || status.includes('aplicada') || status.includes('aprobada')) return theme.primary;
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
  decisionRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  decisionButton: { flex: 1, minHeight: 40, alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderRadius: 8, paddingHorizontal: 8 },
  cvChoice: { flex: 1, minWidth: 120, minHeight: 40, justifyContent: 'center', borderWidth: 1, borderRadius: 8, paddingHorizontal: 8 },
  actions: { gap: 8 },
  linkButton: { minHeight: 44, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, borderWidth: 1, borderRadius: 8, paddingHorizontal: 12 },
  letter: { gap: 10, borderWidth: 1, borderRadius: 8, padding: 14 },
});
