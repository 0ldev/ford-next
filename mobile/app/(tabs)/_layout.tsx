import { Ionicons } from "@expo/vector-icons";
import { Tabs } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { cores } from "../../src/presentation/theme";

const ALTURA_BARRA = 64;

export default function TabsLayout() {
  const insets = useSafeAreaInsets();

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: cores.marca,
        tabBarInactiveTintColor: cores.neutro400,
        tabBarLabelStyle: { fontSize: 11, lineHeight: 14 },
        tabBarItemStyle: { paddingVertical: 4 },
        tabBarStyle: {
          backgroundColor: cores.superficie,
          borderTopColor: cores.borda,
          height: ALTURA_BARRA + insets.bottom,
          paddingBottom: insets.bottom
        }
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: "Painel",
          tabBarIcon: ({ color, size }) => <Ionicons name="speedometer-outline" size={size} color={color} />
        }}
      />
      <Tabs.Screen
        name="tendencia"
        options={{
          title: "Tendência",
          tabBarIcon: ({ color, size }) => <Ionicons name="trending-up-outline" size={size} color={color} />
        }}
      />
      <Tabs.Screen
        name="anomalias"
        options={{
          title: "Anomalias",
          tabBarIcon: ({ color, size }) => <Ionicons name="warning-outline" size={size} color={color} />
        }}
      />
      <Tabs.Screen
        name="leads"
        options={{
          title: "Leads",
          tabBarIcon: ({ color, size }) => <Ionicons name="people-outline" size={size} color={color} />
        }}
      />
    </Tabs>
  );
}
