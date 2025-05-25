import { Canvas } from "@react-three/fiber";
import { OrbitControls, useGLTF } from "@react-three/drei";
import { Bloom, EffectComposer, Vignette } from "@react-three/postprocessing";
import { Suspense, useEffect, useState } from "react";
import TargetsContainer from "./TargetsContainer";
import CamerasContainer from "./CamerasContainerCanvas";
import { io } from "socket.io-client";
import * as THREE from "three";

function CityModel() {
  const { scene } = useGLTF("/maps/stalowa_wola.glb");
  return <primitive object={scene} scale={1} position={[0, 0, 0]} />;
}

useGLTF.preload("/maps/stalowa_wola.glb");
interface Target {
  id: string;
  x: number;
  y: number;
  z: number;
  vx: number;
  vz: number;
}
interface Camera {
  id: string;
  x: number;
  y: number;
  z: number;
  rx: number;
  ry: number;
  rz: number;
}
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
  const [targets, setTargets] = useState<Target[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);

  useEffect(() => {
    
    fetch("/camera_data.json")
      .then((response) => response.json())
      .then((data: RawCameraData[]) => {
        const formatted: Camera[] = data.map((cam) => ({
          id: cam.name,
          x: cam.location.x,
          y: cam.location.z,
          z: -cam.location.y,
          rx: cam.rotation_euler.y,
          ry: -cam.rotation_euler.z,
          rz: -cam.rotation_euler.x,
        }));
        setCameras(formatted);
      })
      .catch((err) => console.error("Błąd kamery:", err));

    const socket = io("http://localhost:5001");

    socket.on("connect", () => {
      console.log("Połączono z WebSocketem");
    });

    socket.on("frame_data", (data: { frame: number; objects: Record<string, number[]> }) => {
      console.log("📡 Odebrano dane:", data); 
      
      const updatedTargets: Target[] = Object.entries(data.objects).map(([id, coords]) => ({
        id,
        x: coords[0],
        y: coords[2],   // zamiana z->y
        z: -coords[1],  // zamiana y->z i negacja (dostosowanie układu)
        vx: 0,
        vz: 0,
      }));

      setTargets(updatedTargets);
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  return (
    <div id="canvas-container">
      <Canvas camera={{ position: [100, 100, 100], fov: 70, far: 10000 }}>
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 5]} intensity={1} />
        <Suspense fallback={null}>
          <CityModel />
        </Suspense>
        <CamerasContainer cameras={cameras} />
        <TargetsContainer targets={targets} />
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
