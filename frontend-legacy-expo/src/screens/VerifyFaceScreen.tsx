import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { CameraView, useCameraPermissions } from 'expo-camera';
import React, { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import * as api from '../api/mockApi';
import { useAuth } from '../context/AuthContext';
import { RootStackParamList } from '../navigation/types';
import { colors, radius, spacing } from '../theme';

type Props = NativeStackScreenProps<RootStackParamList, 'VerifyFace'>;

type Status = 'idle' | 'capturing' | 'checking' | 'failed';

export default function VerifyFaceScreen({ route, navigation }: Props) {
  const { employeeId, type } = route.params;
  const { guard } = useAuth();
  const [permission, requestPermission] = useCameraPermissions();
  const [status, setStatus] = useState<Status>('idle');
  const [error, setError] = useState<string | null>(null);
  const cameraRef = useRef<CameraView>(null);

  useEffect(() => {
    if (permission && !permission.granted) {
      requestPermission();
    }
  }, [permission, requestPermission]);

  const handleVerify = async () => {
    if (!guard || status === 'capturing' || status === 'checking') return;
    setError(null);
    setStatus('capturing');
    try {
      const photo = await cameraRef.current?.takePictureAsync({ quality: 0.5 });
      setStatus('checking');
      const result = await api.verifyFace(employeeId, photo?.uri ?? '');
      if (!result.success) {
        setStatus('failed');
        setError('Face does not match the selected employee. Please try again.');
        return;
      }
      const event = await api.recordAttendance(employeeId, type, guard);
      navigation.replace('Confirmation', {
        employeeName: event.employeeName,
        type: event.type,
        timestamp: event.timestamp,
      });
    } catch (e) {
      setStatus('failed');
      setError(e instanceof Error ? e.message : 'Verification failed. Please try again.');
    }
  };

  if (!permission) {
    return (
      <View style={styles.center}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  if (!permission.granted) {
    return (
      <View style={styles.center}>
        <Text style={styles.permissionText}>Camera access is required to verify attendance.</Text>
        <TouchableOpacity style={styles.button} onPress={requestPermission}>
          <Text style={styles.buttonText}>Grant camera access</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const busy = status === 'capturing' || status === 'checking';

  return (
    <View style={styles.container}>
      <Text style={styles.instruction}>
        Ask the employee to stand in front of the camera, then tap Verify.
      </Text>

      <View style={styles.cameraWrapper}>
        <CameraView ref={cameraRef} style={styles.camera} facing="front" />
        <View style={styles.faceGuide} pointerEvents="none" />
      </View>

      {error ? <Text style={styles.error}>{error}</Text> : null}

      <TouchableOpacity
        style={[styles.button, busy && styles.buttonDisabled]}
        onPress={handleVerify}
        disabled={busy}
      >
        {busy ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>
            {status === 'failed' ? 'Try again' : `Verify ${type}`}
          </Text>
        )}
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, padding: spacing.lg },
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.lg,
    backgroundColor: colors.background,
  },
  instruction: {
    fontSize: 14,
    color: colors.textMuted,
    textAlign: 'center',
    marginBottom: spacing.md,
  },
  cameraWrapper: {
    flex: 1,
    borderRadius: radius.lg,
    overflow: 'hidden',
    marginBottom: spacing.md,
    backgroundColor: '#000',
  },
  camera: { flex: 1 },
  faceGuide: {
    position: 'absolute',
    top: '20%',
    left: '20%',
    right: '20%',
    bottom: '25%',
    borderWidth: 3,
    borderColor: '#ffffffaa',
    borderRadius: radius.lg,
  },
  error: {
    color: colors.danger,
    textAlign: 'center',
    marginBottom: spacing.md,
    fontSize: 13,
  },
  permissionText: {
    fontSize: 15,
    color: colors.text,
    textAlign: 'center',
    marginBottom: spacing.lg,
  },
  button: {
    backgroundColor: colors.primary,
    borderRadius: radius.md,
    paddingVertical: spacing.md,
    alignItems: 'center',
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '700' },
});
