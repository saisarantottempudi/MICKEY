import { Canvas, useFrame } from '@react-three/fiber'
import { useRef, useMemo } from 'react'
import * as THREE from 'three'

function Ring({ radius, tubeRadius, speed, color, opacity }) {
  const ref = useRef()
  useFrame((_, delta) => {
    ref.current.rotation.x += delta * speed * 0.3
    ref.current.rotation.y += delta * speed
  })
  return (
    <mesh ref={ref}>
      <torusGeometry args={[radius, tubeRadius, 16, 64]} />
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={1.5}
        transparent
        opacity={opacity}
      />
    </mesh>
  )
}

function CoreGlow({ isThinking }) {
  const ref = useRef()
  useFrame((state) => {
    const scale = isThinking
      ? 1 + Math.sin(state.clock.elapsedTime * 4) * 0.3
      : 1 + Math.sin(state.clock.elapsedTime * 1.5) * 0.1
    ref.current.scale.set(scale, scale, scale)
  })
  return (
    <mesh ref={ref}>
      <sphereGeometry args={[0.15, 32, 32]} />
      <meshStandardMaterial
        color="#00f0ff"
        emissive="#00f0ff"
        emissiveIntensity={isThinking ? 3 : 1.5}
        transparent
        opacity={0.8}
      />
    </mesh>
  )
}

function Particles({ count = 40 }) {
  const ref = useRef()
  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3)
    for (let i = 0; i < count; i++) {
      const angle = (i / count) * Math.PI * 2
      const r = 1.2 + Math.random() * 0.3
      pos[i * 3] = Math.cos(angle) * r
      pos[i * 3 + 1] = (Math.random() - 0.5) * 0.3
      pos[i * 3 + 2] = Math.sin(angle) * r
    }
    return pos
  }, [count])

  useFrame((_, delta) => {
    ref.current.rotation.y += delta * 0.2
  })

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial color="#00f0ff" size={0.03} transparent opacity={0.6} sizeAttenuation />
    </points>
  )
}

export default function ArcReactor({ isThinking = false }) {
  return (
    <div style={{ width: '100%', height: '100%', minHeight: 200 }}>
      <Canvas camera={{ position: [0, 0, 3.5], fov: 50 }}>
        <ambientLight intensity={0.2} />
        <pointLight position={[0, 0, 2]} intensity={1} color="#00f0ff" />
        <Ring radius={1.0} tubeRadius={0.02} speed={0.8} color="#00f0ff" opacity={0.6} />
        <Ring radius={0.75} tubeRadius={0.015} speed={-1.2} color="#0080ff" opacity={0.5} />
        <Ring radius={0.5} tubeRadius={0.01} speed={1.5} color="#00f0ff" opacity={0.4} />
        <CoreGlow isThinking={isThinking} />
        <Particles />
      </Canvas>
    </div>
  )
}
