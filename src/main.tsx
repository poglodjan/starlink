import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import CamerasContainer from "./CamerasContainer.tsx";
import TelemetryContainer from "./TelemetryContainer";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <CamerasContainer />
    <TelemetryContainer />

    <App />
  </StrictMode>
);
