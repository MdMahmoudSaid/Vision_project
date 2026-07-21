import { NativeStackScreenProps } from '@react-navigation/native-stack';
import React, { useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import * as api from '../api/mockApi';
import { Employee } from '../api/types';
import { RootStackParamList } from '../navigation/types';
import { colors, radius, spacing } from '../theme';

type Props = NativeStackScreenProps<RootStackParamList, 'EmployeeDetail'>;

export default function EmployeeDetailScreen({ route, navigation }: Props) {
  const { employeeId } = route.params;
  const [employee, setEmployee] = useState<Employee | null>(null);

  useEffect(() => {
    api.getEmployee(employeeId).then(setEmployee);
  }, [employeeId]);

  if (!employee) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  const goVerify = (type: 'arrival' | 'departure') => {
    navigation.navigate('VerifyFace', { employeeId: employee.id, type });
  };

  return (
    <View style={styles.container}>
      <View style={styles.card}>
        <Text style={styles.name}>{employee.fullName}</Text>
        <Text style={styles.meta}>Employee #{employee.employeeNumber}</Text>
        {employee.department ? <Text style={styles.meta}>{employee.department}</Text> : null}
        {employee.jobTitle ? <Text style={styles.meta}>{employee.jobTitle}</Text> : null}

        {!employee.faceRegistered && (
          <Text style={styles.warning}>
            This employee has no registered face. Verification will fail until an
            administrator registers their face.
          </Text>
        )}
      </View>

      <Text style={styles.prompt}>Select the event to record</Text>

      <TouchableOpacity style={[styles.actionButton, styles.arrival]} onPress={() => goVerify('arrival')}>
        <Text style={styles.actionText}>Arrival</Text>
      </TouchableOpacity>

      <TouchableOpacity style={[styles.actionButton, styles.departure]} onPress={() => goVerify('departure')}>
        <Text style={styles.actionText}>Departure</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, padding: spacing.lg },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    padding: spacing.lg,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: spacing.xl,
  },
  name: { fontSize: 20, fontWeight: '700', color: colors.text },
  meta: { fontSize: 14, color: colors.textMuted, marginTop: spacing.xs },
  warning: {
    marginTop: spacing.md,
    fontSize: 13,
    color: colors.danger,
  },
  prompt: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textMuted,
    marginBottom: spacing.md,
    textAlign: 'center',
  },
  actionButton: {
    borderRadius: radius.md,
    paddingVertical: spacing.lg,
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  arrival: { backgroundColor: colors.primary },
  departure: { backgroundColor: colors.primaryDark },
  actionText: { color: '#fff', fontSize: 18, fontWeight: '700' },
});
