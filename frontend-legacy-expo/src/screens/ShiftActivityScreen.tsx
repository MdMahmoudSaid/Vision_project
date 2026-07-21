import { NativeStackScreenProps } from '@react-navigation/native-stack';
import React, { useCallback, useState } from 'react';
import { useFocusEffect } from '@react-navigation/native';
import { FlatList, StyleSheet, Text, View } from 'react-native';
import * as api from '../api/mockApi';
import { AttendanceEvent } from '../api/types';
import { useAuth } from '../context/AuthContext';
import { RootStackParamList } from '../navigation/types';
import { colors, radius, spacing } from '../theme';

type Props = NativeStackScreenProps<RootStackParamList, 'ShiftActivity'>;

export default function ShiftActivityScreen({}: Props) {
  const { guard } = useAuth();
  const [events, setEvents] = useState<AttendanceEvent[]>([]);

  useFocusEffect(
    useCallback(() => {
      if (!guard) return;
      api.getShiftActivity(guard.id).then(setEvents);
    }, [guard])
  );

  return (
    <View style={styles.container}>
      <FlatList
        data={events}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        ListEmptyComponent={<Text style={styles.empty}>No attendance recorded this shift yet</Text>}
        renderItem={({ item }) => {
          const time = new Date(item.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false,
          });
          return (
            <View style={styles.row}>
              <View>
                <Text style={styles.name}>{item.employeeName}</Text>
                <Text style={styles.meta}>{item.type === 'arrival' ? 'Arrival' : 'Departure'}</Text>
              </View>
              <Text style={styles.time}>{time}</Text>
            </View>
          );
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, padding: spacing.md },
  listContent: { paddingBottom: spacing.xl },
  row: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.md,
    marginBottom: spacing.sm,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  name: { fontSize: 15, fontWeight: '600', color: colors.text },
  meta: { fontSize: 13, color: colors.textMuted, marginTop: 2 },
  time: { fontSize: 15, fontWeight: '700', color: colors.primary },
  empty: { textAlign: 'center', color: colors.textMuted, marginTop: spacing.xl },
});
