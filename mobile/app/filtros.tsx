import { useRouter } from "expo-router";
import FiltrosModal from "../src/presentation/components/FiltrosModal";

export default function Filtros() {
  const router = useRouter();
  return <FiltrosModal onFechar={() => router.back()} />;
}
