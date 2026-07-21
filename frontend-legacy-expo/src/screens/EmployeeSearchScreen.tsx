import { NativeStackScreenProps } from '@react-navigation/native-stack';
import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import * as api from '../api/mockApi';
import { Employee } from '../api/types';
import { useAuth } from '../context/AuthContext';
import { RootStackParamList } from '../navigation/types';
import { colors, radius, spacing } from '../theme';

type Props = NativeStackScreenProps<RootStackParamList, 'EmployeeSearch'>;

export default function EmployeeSearchScreen({ navigation }: Props) {
  const { guard, signOut } = useAuth();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Employee[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    navigation.setOptions({
      headerRight: () => (
        <TouchableOpacity onPress={() => navigation.navigate('ShiftActivity')}>
          <Text style={styles.headerLink}>Shift activity</Text>
        </TouchableOpacity>
      ),
    });
  }, [navigation]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api.searchEmployees(query).then((employees) => {
      if (!cancelled) {
        setResults(employees);
        setLoading(false);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [query]);

  return (
    <View style={styles.container}>
      <View style={styles.topBar}>
        <Text style={styles.welcome}>Signed in as {guard?.fullName}</Text>
        <TouchableOpacity onPress={() => signOut()}>
          <Text style={styles.signOut}>Sign out</Text>
        </TouchableOpacity>
      </View>

      <TextInput
        style={styles.searchInput}
        placeholder="Search by name or employee number"
        placeholderTextColor={colors.textMuted}
        value={query}
        onChangeText={setQuery}
        autoCapitalize="none"
        autoCorrect={false}
      />

      {loading ? (
        <ActivityIndicator style={styles.loading} color={colors.primary} />
      ) : (
        <FlatList
          data={results}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContent}
          ListEmptyComponent={<Text style={styles.empty}>No employees found</Text>}
          renderItem={({ item }) => (
            <TouchableOpacity
              style={styles.row}
              onPress={() => navigation.navigate('EmployeeDetail', { employeeId: item.id })}
            >
              <View>
                <Text style={styles.rowName}>{item.fullName}</Text>
                <Text style={styles.rowMeta}>
                  #{item.employeeNumber}
                  {item.department ? ` · ${item.department}` : ''}
                </Text>
              </View>
              {!item.faceRegistered && <Text style={styles.badge}>No face on file</Text>}
            </TouchableOpacity>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, padding: spacing.md },
  topBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  welcome: { color: colors.textMuted, fontSize: 13 },
  signOut: { color: colors.danger, fontSize: 13, fontWeight: '600' },
  headerLink: { color: colors.primary, fontWeight: '600' },
  searchInput: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm + 4,
    fontSize: 16,
    marginBottom: spacing.md,
  },
  loading: { marginTop: spacing.xl },
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
  rowName: { fontSize: 16, fontWeight: '600', color: colors.text },
  rowMeta: { fontSize: 13, color: colors.textMuted, marginTop: 2 },
  badge: {
    fontSize: 11,
    color: colors.danger,
    fontWeight: '600',
  },
  empty: { textAlign: 'center', color: colors.textMuted, marginTop: spacing.xl },
});
