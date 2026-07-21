import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import React from 'react';
import { ActivityIndicator, View } from 'react-native';
import { useAuth } from '../context/AuthContext';
import ConfirmationScreen from '../screens/ConfirmationScreen';
import EmployeeDetailScreen from '../screens/EmployeeDetailScreen';
import EmployeeSearchScreen from '../screens/EmployeeSearchScreen';
import LoginScreen from '../screens/LoginScreen';
import ShiftActivityScreen from '../screens/ShiftActivityScreen';
import VerifyFaceScreen from '../screens/VerifyFaceScreen';
import { colors } from '../theme';
import { RootStackParamList } from './types';

const Stack = createNativeStackNavigator<RootStackParamList>();

export default function RootNavigator() {
  const { guard, isLoading } = useAuth();

  if (isLoading && !guard) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
        <ActivityIndicator color={colors.primary} />
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator
        screenOptions={{
          headerStyle: { backgroundColor: colors.primary },
          headerTintColor: '#fff',
          headerTitleStyle: { fontWeight: '700' },
        }}
      >
        {!guard ? (
          <Stack.Screen name="Login" component={LoginScreen} options={{ headerShown: false }} />
        ) : (
          <>
            <Stack.Screen
              name="EmployeeSearch"
              component={EmployeeSearchScreen}
              options={{ title: 'Find employee' }}
            />
            <Stack.Screen
              name="EmployeeDetail"
              component={EmployeeDetailScreen}
              options={{ title: 'Record attendance' }}
            />
            <Stack.Screen
              name="VerifyFace"
              component={VerifyFaceScreen}
              options={{ title: 'Face verification' }}
            />
            <Stack.Screen
              name="Confirmation"
              component={ConfirmationScreen}
              options={{ title: 'Confirmation', headerBackVisible: false, gestureEnabled: false }}
            />
            <Stack.Screen
              name="ShiftActivity"
              component={ShiftActivityScreen}
              options={{ title: 'Shift activity' }}
            />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
