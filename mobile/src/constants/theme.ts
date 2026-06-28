/**
 * Below are the colors that are used in the app. The colors are defined in the light and dark mode.
 * There are many other ways to style your app. For example, [Nativewind](https://www.nativewind.dev/), [Tamagui](https://tamagui.dev/), [unistyles](https://reactnativeunistyles.vercel.app), etc.
 */

import { Platform } from 'react-native';

export const Colors = {
  light: {
    text: '#18211D',
    background: '#F7F9F8',
    surface: '#FFFFFF',
    backgroundElement: '#E9EFEC',
    backgroundSelected: '#D8E8DF',
    textSecondary: '#637069',
    border: '#DCE4E0',
    primary: '#236B4E',
    primaryText: '#FFFFFF',
    accent: '#B9563B',
    warning: '#A65D16',
    danger: '#9E3A3A',
    info: '#2E5E8C',
  },
  dark: {
    text: '#F3F6F4',
    background: '#111714',
    surface: '#19211D',
    backgroundElement: '#25302B',
    backgroundSelected: '#30483C',
    textSecondary: '#AAB6B0',
    border: '#33423B',
    primary: '#68B68E',
    primaryText: '#0E2419',
    accent: '#E88A70',
    warning: '#E2A45D',
    danger: '#E47F7F',
    info: '#79A9D6',
  },
} as const;

export type ThemeColor = keyof typeof Colors.light & keyof typeof Colors.dark;

export const Fonts = Platform.select({
  ios: {
    /** iOS `UIFontDescriptorSystemDesignDefault` */
    sans: 'system-ui',
    /** iOS `UIFontDescriptorSystemDesignSerif` */
    serif: 'ui-serif',
    /** iOS `UIFontDescriptorSystemDesignRounded` */
    rounded: 'ui-rounded',
    /** iOS `UIFontDescriptorSystemDesignMonospaced` */
    mono: 'ui-monospace',
  },
  default: {
    sans: 'normal',
    serif: 'serif',
    rounded: 'normal',
    mono: 'monospace',
  },
  web: {
    sans: 'var(--font-display)',
    serif: 'var(--font-serif)',
    rounded: 'var(--font-rounded)',
    mono: 'var(--font-mono)',
  },
});

export const Spacing = {
  half: 2,
  one: 4,
  two: 8,
  three: 16,
  four: 24,
  five: 32,
  six: 64,
} as const;

export const BottomTabInset = Platform.select({ ios: 50, android: 80, web: 72 }) ?? 0;
export const MaxContentWidth = 800;
