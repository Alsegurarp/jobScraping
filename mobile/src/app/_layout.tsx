import { DarkTheme, DefaultTheme, ThemeProvider } from 'expo-router';
import { useColorScheme } from 'react-native';

import AppTabs from '@/components/app-tabs';
import { BotJobsProvider } from '@/state/botjobs-provider';

export default function TabLayout() {
  const colorScheme = useColorScheme();
  return (
    <ThemeProvider value={colorScheme === 'dark' ? DarkTheme : DefaultTheme}>
      <BotJobsProvider>
        <AppTabs />
      </BotJobsProvider>
    </ThemeProvider>
  );
}
