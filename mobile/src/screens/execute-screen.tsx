import { SymbolView, type SFSymbol } from 'expo-symbols';
import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, StyleSheet, Switch, TextInput, View } from 'react-native';

import type { Portal, SearchParams } from '@/api/types';
import { FeedbackBanner } from '@/components/feedback-banner';
import { Page } from '@/components/page';
import { ScreenHeader } from '@/components/screen-header';
import { ThemedText } from '@/components/themed-text';
import { useTheme } from '@/hooks/use-theme';
import { useBotJobs } from '@/state/botjobs-provider';

const PORTALS: { id: Portal; label: string }[] = [
  { id: 'indeed', label: 'Indeed' },
  { id: 'linkedin', label: 'LinkedIn' },
  { id: 'occ', label: 'OCC' },
  { id: 'computrabajo', label: 'Computrabajo' },
  { id: 'glassdoor', label: 'Glassdoor' },
];

export default function ExecuteScreen() {
  const theme = useTheme();
  const actions = useBotJobs();
  const [params, setParams] = useState<SearchParams>({
    portals: ['indeed', 'linkedin'], max_results: 10, refresh_cache: false, browser: false, research: false,
  });

  const togglePortal = (portal: Portal) => setParams((current) => {
    const selected = current.portals.includes(portal);
    if (selected && current.portals.length === 1) return current;
    return { ...current, portals: selected ? current.portals.filter((item) => item !== portal) : [...current.portals, portal] };
  });

  const runSearch = async () => {
    if (await actions.startSearch(params)) router.push('/results');
  };

  const runExtraction = async () => {
    if (await actions.startExtractLinks({ browser: params.browser, research: params.research })) router.push('/results');
  };

  return (
    <Page>
      <ScreenHeader title="BotJobs" connected={actions.connected} />
      <FeedbackBanner loading={actions.loading} error={actions.error} status={actions.activeRun ? `${runTypeLabel(actions.activeRun.type)} · ${statusLabel(actions.activeRun.status)}` : undefined} />

      <View style={styles.section}>
        <ThemedText selectable style={styles.sectionTitle}>Buscar vacantes</ThemedText>
        <View style={styles.portalGrid}>
          {PORTALS.map((portal) => {
            const selected = params.portals.includes(portal.id);
            return (
              <Pressable
                key={portal.id}
                accessibilityRole="checkbox"
                accessibilityState={{ checked: selected }}
                onPress={() => togglePortal(portal.id)}
                style={[styles.portal, { backgroundColor: selected ? theme.backgroundSelected : theme.surface, borderColor: selected ? theme.primary : theme.border }]}>
                <SymbolView name={{ ios: selected ? 'checkmark.circle.fill' : 'circle', android: selected ? 'check_circle' : 'radio_button_unchecked', web: selected ? 'check_circle' : 'circle' }} tintColor={selected ? theme.primary : theme.textSecondary} size={20} />
                <ThemedText selectable type="smallBold">{portal.label}</ThemedText>
              </Pressable>
            );
          })}
        </View>

        <View style={[styles.settingRow, { borderColor: theme.border }]}>
          <View>
            <ThemedText selectable type="smallBold">Máximo de resultados</ThemedText>
            <ThemedText selectable type="small" themeColor="textSecondary">Entre 1 y 50</ThemedText>
          </View>
          <TextInput
            accessibilityLabel="Máximo de resultados"
            keyboardType="number-pad"
            value={String(params.max_results)}
            onChangeText={(value) => setParams((current) => ({ ...current, max_results: Math.min(50, Math.max(1, Number(value) || 1)) }))}
            style={[styles.numberInput, { color: theme.text, backgroundColor: theme.surface, borderColor: theme.border }]}
          />
        </View>

        <SettingSwitch label="Actualizar caché" value={params.refresh_cache} onChange={(value) => setParams((current) => ({ ...current, refresh_cache: value }))} />
        <SettingSwitch label="Usar navegador" value={params.browser} onChange={(value) => setParams((current) => ({ ...current, browser: value }))} />
        <SettingSwitch label="Investigar empresas" value={params.research} onChange={(value) => setParams((current) => ({ ...current, research: value }))} />
        <CommandButton label="Iniciar búsqueda" icon="magnifyingglass" onPress={runSearch} disabled={actions.loading || !actions.connected} primary />
      </View>

      <View style={styles.section}>
        <ThemedText selectable style={styles.sectionTitle}>Otras acciones</ThemedText>
        <CommandButton label="Extraer links de la plantilla" icon="link" onPress={runExtraction} disabled={actions.loading || !actions.connected} />
        <CommandButton label="Simular aplicaciones aprobadas" icon="doc.text.magnifyingglass" onPress={actions.startApplyDryRun} disabled={actions.loading || !actions.connected} />
        <CommandButton label="Comprobar conexión" icon="arrow.clockwise" onPress={actions.refresh} disabled={actions.loading} />
      </View>
    </Page>
  );
}

function SettingSwitch({ label, value, onChange }: { label: string; value: boolean; onChange: (value: boolean) => void }) {
  const theme = useTheme();
  return <View style={[styles.settingRow, { borderColor: theme.border }]}><ThemedText selectable type="smallBold">{label}</ThemedText><Switch value={value} onValueChange={onChange} trackColor={{ true: theme.primary }} /></View>;
}

function CommandButton({ label, icon, onPress, disabled, primary = false }: { label: string; icon: SFSymbol; onPress: () => void | Promise<unknown>; disabled: boolean; primary?: boolean }) {
  const theme = useTheme();
  const androidIcon = icon === 'magnifyingglass' ? 'search' : icon === 'arrow.clockwise' ? 'refresh' : icon === 'link' ? 'link' : 'description';
  return (
    <Pressable accessibilityRole="button" disabled={disabled} onPress={() => void onPress()} style={({ pressed }) => [styles.command, { backgroundColor: primary ? theme.primary : theme.surface, borderColor: primary ? theme.primary : theme.border, opacity: disabled ? 0.45 : pressed ? 0.72 : 1 }]}>
      <SymbolView name={{ ios: icon, android: androidIcon, web: androidIcon }} tintColor={primary ? theme.primaryText : theme.primary} size={20} />
      <ThemedText selectable type="smallBold" style={{ color: primary ? theme.primaryText : theme.text, flex: 1 }}>{label}</ThemedText>
      <SymbolView name={{ ios: 'chevron.right', android: 'chevron_right', web: 'chevron_right' }} tintColor={primary ? theme.primaryText : theme.textSecondary} size={18} />
    </Pressable>
  );
}

const statusLabel = (status: string) => ({ pending: 'Pendiente', running: 'Ejecutando', completed: 'Completada', failed: 'Fallida' }[status] || status);
const runTypeLabel = (type: string) => ({ search: 'Búsqueda', extract_links: 'Extracción', apply_approved_dry_run: 'Simulación' }[type] || type);

const styles = StyleSheet.create({
  section: { gap: 12 }, sectionTitle: { fontSize: 18, lineHeight: 24, fontWeight: '700' },
  portalGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  portal: { minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: 8, borderWidth: 1, borderRadius: 8, paddingHorizontal: 12 },
  settingRow: { minHeight: 56, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12, borderBottomWidth: StyleSheet.hairlineWidth },
  numberInput: { width: 68, height: 42, borderWidth: 1, borderRadius: 8, textAlign: 'center', fontSize: 16, fontVariant: ['tabular-nums'] },
  command: { minHeight: 52, flexDirection: 'row', alignItems: 'center', gap: 12, borderWidth: 1, borderRadius: 8, paddingHorizontal: 14 },
});
