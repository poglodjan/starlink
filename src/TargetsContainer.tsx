import React, { useState, useEffect } from "react";
import { Line } from "@react-three/drei";
import * as THREE from "three";

interface Target {
  id: string;
  x: number;
  y: number;
  z: number;
}

interface TargetsContainerProps {
  targets: Target[];
}

const MAX_TRAIL_POINTS = 50; // Max number of points in a trail

function TargetsContainer({ targets }: TargetsContainerProps) {
  const [targetHistories, setTargetHistories] = useState<
    Record<string, THREE.Vector3[]>
  >({});

  useEffect(() => {
    setTargetHistories((prevHistories) => {
      const newHistories = { ...prevHistories };
      const activeTargetIds = new Set(targets.map((t) => t.id));

      // Add current positions to history
      for (const target of targets) {
        const history = newHistories[target.id] || [];
        const newPosition = new THREE.Vector3(target.x, target.y, target.z);

        // Avoid adding duplicate points if position hasn't changed
        if (
          history.length > 0 &&
          history[history.length - 1].equals(newPosition)
        ) {
          newHistories[target.id] = history;
          continue;
        }

        const newHistory = [...history, newPosition];
        if (newHistory.length > MAX_TRAIL_POINTS) {
          newHistory.shift(); // Remove the oldest point
        }
        newHistories[target.id] = newHistory;
      }

      // Clean up histories for targets that no longer exist
      for (const id in newHistories) {
        if (!activeTargetIds.has(id)) {
          delete newHistories[id];
        }
      }

      return newHistories;
    });
  }, [targets]);

  return (
    <group>
      {targets.map((target) => (
        <React.Fragment key={target.id}>
          {/* Target Blob */}
          <mesh position={[target.x, target.y, target.z]}>
            <sphereGeometry args={[4, 20, 20]} /> {/* Large red sphere */}
            <meshStandardMaterial
              color="red"
              emissive="red"
              emissiveIntensity={2}
            />
          </mesh>

          {/* Target Trail */}
          {targetHistories[target.id] &&
            targetHistories[target.id].length > 1 && (
              <Line
                points={targetHistories[target.id]}
                color="red"
                lineWidth={2}
              />
            )}
        </React.Fragment>
      ))}
    </group>
  );
}

export default TargetsContainer;
