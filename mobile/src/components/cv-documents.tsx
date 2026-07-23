import * as DocumentPicker from 'expo-document-picker';
import { SymbolView } from 'expo-symbols';
import { useEffect, useState } from 'react';
import { Linking, Pressable, StyleSheet, View } from 'react-native';

import { botJobsApi } from '@/api/client';
import type { CvDocument } from '@/api/types';
import { useTheme } from '@/hooks/use-theme';
import { ThemedText } from './themed-text';

export function CvDocuments() {
  const theme = useTheme();
  const [documents, setDocuments] = useState<CvDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      setDocuments(await botJobsApi.cvs());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'No se pudieron cargar los CV');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, []);

  const upload = async () => {
    const result = await DocumentPicker.getDocumentAsync({ type: 'application/pdf', multiple: false, copyToCacheDirectory: true });
    if (result.canceled) return;
    setLoading(true);
    try {
      await botJobsApi.uploadCv(result.assets[0]);
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'No se pudo subir el CV');
      setLoading(false);
    }
  };

  const activate = async (cvId: string) => {
    setLoading(true);
    try {
      await botJobsApi.activateCv(cvId);
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'No se pudo activar el CV');
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={{ flex: 1, gap: 2 }}>
          <ThemedText selectable style={styles.title}>Currículums</ThemedText>
          <ThemedText selectable type="small" themeColor="textSecondary">PDF · máximo 10 MB</ThemedText>
        </View>
        <Pressable accessibilityRole="button" disabled={loading} onPress={() => void upload()} style={({ pressed }) => [styles.upload, { backgroundColor: theme.primary, opacity: loading ? 0.5 : pressed ? 0.72 : 1 }]}>
          <SymbolView name={{ ios: 'arrow.up.doc', android: 'upload_file', web: 'upload_file' }} tintColor={theme.primaryText} size={18} />
          <ThemedText selectable type="smallBold" style={{ color: theme.primaryText }}>{loading ? 'Cargando…' : 'Subir CV'}</ThemedText>
        </Pressable>
      </View>
      {!!error && <ThemedText selectable type="small" style={{ color: theme.danger }}>{error}</ThemedText>}
      {!loading && documents.length === 0 && <ThemedText selectable themeColor="textSecondary">No hay CV cargados.</ThemedText>}
      {documents.map((document) => (
        <View key={document.cv_id} style={[styles.row, { borderColor: theme.border }]}>
          <View style={{ flex: 1, gap: 2 }}>
            <ThemedText selectable type="smallBold">{document.filename}</ThemedText>
            <ThemedText selectable type="small" themeColor="textSecondary">
              {formatBytes(document.size_bytes)} · {formatDate(document.uploaded_at)}{document.active ? ' · Activo por defecto' : ''}
            </ThemedText>
          </View>
          {!document.active && <Pressable accessibilityRole="button" disabled={loading} onPress={() => void activate(document.cv_id)} style={[styles.button, { borderColor: theme.primary }]}><ThemedText selectable type="smallBold" style={{ color: theme.primary }}>Activar</ThemedText></Pressable>}
          <Pressable accessibilityRole="link" onPress={() => void Linking.openURL(botJobsApi.cvUrl(document.cv_id))} style={[styles.button, { borderColor: theme.info }]}><ThemedText selectable type="smallBold" style={{ color: theme.info }}>Ver</ThemedText></Pressable>
        </View>
      ))}
    </View>
  );
}

const formatBytes = (value: number) => value < 1024 * 1024 ? `${Math.max(1, Math.round(value / 1024))} KB` : `${(value / 1024 / 1024).toFixed(1)} MB`;
const formatDate = (value: string) => new Intl.DateTimeFormat('es-MX', { dateStyle: 'medium' }).format(new Date(value));
const styles = StyleSheet.create({
  container: { gap: 12 },
  header: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  title: { fontSize: 18, lineHeight: 24, fontWeight: '700' },
  upload: { minHeight: 44, flexDirection: 'row', alignItems: 'center', gap: 8, borderRadius: 8, paddingHorizontal: 12 },
  row: { minHeight: 62, flexDirection: 'row', alignItems: 'center', gap: 10, borderBottomWidth: StyleSheet.hairlineWidth, paddingVertical: 8 },
  button: { minHeight: 40, justifyContent: 'center', borderWidth: 1, borderRadius: 8, paddingHorizontal: 10 },
});
