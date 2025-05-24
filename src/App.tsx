import { Canvas } from "@react-three/fiber";
import { OrbitControls, useGLTF } from "@react-three/drei";
import {
  Bloom,
  DepthOfField,
  EffectComposer,
  Noise,
  Vignette,
} from "@react-three/postprocessing";
import { Suspense, useState, useEffect } from "react";
import TargetsContainer from "./TargetsContainer";
import CamerasContainer from "./CamerasContainerCanvas";

import * as THREE from "three"; // Import THREE for MathUtils

// Component to load and display the city model
function CityModel() {
  // Make sure 'city.glb' is in your 'public' folder
  const { scene } = useGLTF("/maps/stalowa_wola.glb");
  return <primitive object={scene} scale={1} position={[0, 0, 0]} />;
}

// Preload the model for better performance
useGLTF.preload("/maps/stalowa_wola.glb");

interface Target {
  id: string;
  x: number;
  y: number;
  z: number;
  // For simulation purposes
  vx: number;
  vz: number;
}

// Define an interface for Camera data
interface Camera {
  id: string;
  x: number;
  y: number;
  z: number;
  rx: number; // Rotation around X in radians
  ry: number; // Rotation around Y in radians
  rz: number; // Rotation around Z in radians
}

// Define an interface for the raw camera data from JSON
interface RawCameraData {
  name: string;
  location: {
    x: number;
    y: number;
    z: number;
  };
  rotation_euler: {
    x: number;
    y: number;
    z: number;
  };
}

function App() {
  const [targets, setTargets] = useState<Target[]>([
    { id: "target1", x: 5, y: 1, z: 5, vx: 1.5, vz: 0.2 },
    { id: "target2", x: -5, y: 1.5, z: -5, vx: -1.3, vz: 0.4 },
  ]);

  // Initialize camera state
  const [cameras, setCameras] = useState<Camera[]>([]);

  useEffect(() => {
    // Fetch camera data from the JSON file
    fetch("/camera_data.json")
      .then((response) => response.json())
      .then((data: RawCameraData[]) => {
        const formattedCameras: Camera[] = data.map((camData) => ({
          id: camData.name,
          x: camData.location.x, // Blender X to Three.js X
          y: camData.location.z, // Blender Z (up) to Three.js Y (up)
          z: -camData.location.y, // Blender Y (forward) to Three.js -Z (forward)
          rx: camData.rotation_euler.y, // Blender X rotation to Three.js X rotation
          ry: -camData.rotation_euler.z, // Blender Z rotation (yaw) to Three.js Y rotation (yaw)
          rz: -camData.rotation_euler.x, // Blender Y rotation (roll) to Three.js Z rotation (roll), negated
        }));
        setCameras(formattedCameras);
      })
      .catch((error) => console.error("Error loading camera data:", error));

    const interval = setInterval(() => {
      setTargets((prevTargets) =>
        prevTargets.map((t) => {
          const newX = t.x + t.vx;
          const newZ = t.z + t.vz;
          let newVx = t.vx;
          let newVz = t.vz;

          // Simple boundary bounce for simulation
          if (newX > 20 || newX < -20) newVx = -newVx;
          if (newZ > 20 || newZ < -20) newVz = -newVz;

          return { ...t, x: newX, z: newZ, vx: newVx, vz: newVz };
        })
      );
    }, 100); // Update every 100ms

    return () => clearInterval(interval); // Cleanup on unmount
  }, []);

  return (
    <div id="canvas-container">
      <Canvas camera={{ position: [100, 100, 100], fov: 70, far: 10000 }}>
        {/* Add some lighting */}
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 5]} intensity={1} />
        {/* Suspense fallback while the model is loading */}
        <Suspense fallback={null}>
          <CityModel />
        </Suspense>
        <CamerasContainer cameras={cameras} /> {/* Pass cameras data */}
        <TargetsContainer targets={targets} />
        {/* OrbitControls for camera manipulation */}
        <OrbitControls />
        <EffectComposer>
          <Bloom luminanceThreshold={0} luminanceSmoothing={1.3} height={500} />
          <Vignette eskil={false} offset={0.1} darkness={0.5} />
        </EffectComposer>
      </Canvas>
    </div>
  );
}

export default App;
