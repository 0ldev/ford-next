import { useEffect, useState } from "react";
import { Animated, type StyleProp, type ViewStyle } from "react-native";
import { cores } from "../theme";

export interface EsqueletoPulsanteProps {
  style?: StyleProp<ViewStyle>;
}

export default function EsqueletoPulsante({ style }: EsqueletoPulsanteProps) {
  const [opacidade] = useState(() => new Animated.Value(0.4));

  useEffect(() => {
    const animacao = Animated.loop(
      Animated.sequence([
        Animated.timing(opacidade, { toValue: 1, duration: 650, useNativeDriver: true }),
        Animated.timing(opacidade, { toValue: 0.4, duration: 650, useNativeDriver: true })
      ])
    );
    animacao.start();
    return () => animacao.stop();
  }, [opacidade]);

  return (
    <Animated.View
      style={[{ opacity: opacidade, backgroundColor: cores.neutro200, borderRadius: 6 }, style]}
    />
  );
}
