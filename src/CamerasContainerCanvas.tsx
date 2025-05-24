import { Sphere, Line } from "@react-three/drei"; // Ensure Line is imported
import * as THREE from "three";

interface Camera {
  id: string;
  x: number;
  y: number;
  z: number;
  rx: number; // Rotation around X in radians
  ry: number; // Rotation around Y in radians
  rz: number; // Rotation around Z in radians
}

interface CamerasContainerProps {
  cameras: Camera[];
}

const FOV_DEGREES = 75;
const CONE_VISUAL_HEIGHT = 50; // Visual length of the FOV lines - increased for "much longer"
const coneRadius =
  CONE_VISUAL_HEIGHT * Math.tan(THREE.MathUtils.degToRad(FOV_DEGREES / 2));
const CAMERA_BLOB_RADIUS = 3.5; // Size of the camera sphere - increased for "much bigger"

function CamerasContainer({ cameras }: CamerasContainerProps) {
  return (
    <group>
      {cameras.map((cam) => {
        // Define points for the FOV lines
        // Camera group is rotated; cone points along the group's local -Z axis.
        const linePointsPositiveX: [number, number, number][] = [
          [0, 0, 0],
          [coneRadius, 0, -CONE_VISUAL_HEIGHT], // Changed to -CONE_VISUAL_HEIGHT
        ];
        const linePointsNegativeX: [number, number, number][] = [
          [0, 0, 0],
          [-coneRadius, 0, -CONE_VISUAL_HEIGHT], // Changed to -CONE_VISUAL_HEIGHT
        ];

        return (
          <group
            key={cam.id}
            position={[cam.x, cam.y, cam.z]}
            rotation={[cam.rx, cam.ry, cam.rz]}
          >
            {/* Camera Blob */}
            <Sphere args={[CAMERA_BLOB_RADIUS, 16, 16]}>
              <meshStandardMaterial
                color="yellow" // Changed to yellow
                emissive="yellow" // Changed to yellow
                emissiveIntensity={2}
              />
            </Sphere>

            {/* FOV Lines */}
            <Line
              points={linePointsPositiveX}
              color="yellow" // Changed to yellow
              lineWidth={2}
              transparent
              opacity={0.75} // Slightly more opaque for better visibility
            />
            <Line
              points={linePointsNegativeX}
              color="yellow" // Changed to yellow
              lineWidth={2}
              transparent
              opacity={0.75} // Slightly more opaque for better visibility
            />
          </group>
        );
      })}
    </group>
  );
}

export default CamerasContainer;
