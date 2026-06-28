import { ActivityIndicator, StyleSheet, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { useTheme } from '@/hooks/use-theme';

export function FeedbackBanner({ loading, error, status }: { loading: boolean; error: string | null; status?: string }) {
  const theme = useTheme();
  if (!loading && !error && !status) return null;

  return (
    <View style={[styles.banner, { backgroundColor: error ? `${theme.danger}18` : theme.backgroundElement, borderColor: error ? theme.danger : theme.border }]}>
      {loading && <ActivityIndicator color={theme.primary} />}
      <ThemedText selectable type="small" style={{ flex: 1, color: error ? theme.danger : theme.text }}>
        {error || status || 'Cargando…'}
      </ThemedText>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    minHeight: 48,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
});
