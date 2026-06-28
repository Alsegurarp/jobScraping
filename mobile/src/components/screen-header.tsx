import { StyleSheet, View } from 'react-native';

import { ThemedText } from '@/components/themed-text';
import { useTheme } from '@/hooks/use-theme';

export function ScreenHeader({ title, connected }: { title: string; connected?: boolean }) {
  const theme = useTheme();
  return (
    <View style={styles.row}>
      <ThemedText selectable style={styles.title}>{title}</ThemedText>
      {connected !== undefined && (
        <View style={styles.status}>
          <View style={[styles.dot, { backgroundColor: connected ? theme.primary : theme.danger }]} />
          <ThemedText selectable type="small" themeColor="textSecondary">
            {connected ? 'Conectado' : 'Sin conexión'}
          </ThemedText>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 12 },
  title: { fontSize: 28, lineHeight: 34, fontWeight: '700' },
  status: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  dot: { width: 8, height: 8, borderRadius: 4 },
});
