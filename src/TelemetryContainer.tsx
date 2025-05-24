import { Html } from "@react-three/drei";

function TelemetryContainer() {
  // should display plain text telemetry data in top right corner based on the selected target

  return (
    <div id="telemetry-container">
      <p>Telemetry Data</p>
      <p>Target ID: 1</p>
      <p>Altitude: 100 m</p>
      <p>Speed: 50 km/h</p>
      <p>Direction: 45°</p>
      <p>Last Update: 2023-10-01 12:00:00</p>
    </div>
  );
}

export default TelemetryContainer;
