
import React, { useRef, useMemo } from 'react';
import { useFrame, extend } from '@react-three/fiber';
import { shaderMaterial, Sparkles } from '@react-three/drei';
import * as THREE from 'three';

// --- GLSL SHADERS ---

const StarMaterial = shaderMaterial(
    {
        uTime: 0,
        uColorA: new THREE.Color('#ff0000'), // Deep Red
        uColorB: new THREE.Color('#ff8c00'), // Bright Orange
        uRimColor: new THREE.Color('#ffffff'),
    },
    // Vertex Shader
    `
    varying vec2 vUv;
    varying vec3 vNormal;
    varying vec3 vPosition;
    varying vec3 vViewPosition;

    uniform float uTime;

    // Simple noise for displacement (optional, kept simple for performance)
    float random(vec2 st) {
        return fract(sin(dot(st.xy, vec2(12.9898,78.233))) * 43758.5453123);
    }

    void main() {
      vUv = uv;
      vNormal = normalize(normalMatrix * normal);
      vPosition = position;

      // Pulse effect: displace vertices along normal based on time
      float pulse = sin(uTime * 2.0) * 0.02; 
      vec3 pos = position + normal * pulse;

      vec4 modelViewPosition = modelViewMatrix * vec4(pos, 1.0);
      vViewPosition = -modelViewPosition.xyz;
      
      gl_Position = projectionMatrix * modelViewPosition;
    }
  `,
    // Fragment Shader
    `
    varying vec2 vUv;
    varying vec3 vNormal;
    varying vec3 vPosition;
    varying vec3 vViewPosition;

    uniform float uTime;
    uniform vec3 uColorA;
    uniform vec3 uColorB;
    uniform vec3 uRimColor;

    // Simplex 3D Noise 
    // (Source: https://github.com/stegu/webgl-noise/blob/master/src/noise3D.glsl)
    vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
    vec4 mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
    vec4 permute(vec4 x) { return mod289(((x*34.0)+1.0)*x); }
    vec4 taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }

    float snoise(vec3 v) {
      const vec2  C = vec2(1.0/6.0, 1.0/3.0) ;
      const vec4  D = vec4(0.0, 0.5, 1.0, 2.0);

      // First corner
      vec3 i  = floor(v + dot(v, C.yyy) );
      vec3 x0 = v - i + dot(i, C.xxx) ;

      // Other corners
      vec3 g = step(x0.yzx, x0.xyz);
      vec3 l = 1.0 - g;
      vec3 i1 = min( g.xyz, l.zxy );
      vec3 i2 = max( g.xyz, l.zxy );

      //   x0 = x0 - 0.0 + 0.0 * C.xxx;
      //   x1 = x0 - i1  + 1.0 * C.xxx;
      //   x2 = x0 - i2  + 2.0 * C.xxx;
      //   x3 = x0 - 1.0 + 3.0 * C.xxx;
      vec3 x1 = x0 - i1 + C.xxx;
      vec3 x2 = x0 - i2 + C.yyy; // 2.0*C.x = 1/3 = C.y
      vec3 x3 = x0 - D.yyy;      // -1.0+3.0*C.x = -0.5 = -D.y

      // Permutations
      i = mod289(i); 
      vec4 p = permute( permute( permute( 
                 i.z + vec4(0.0, i1.z, i2.z, 1.0 ))
               + i.y + vec4(0.0, i1.y, i2.y, 1.0 )) 
               + i.x + vec4(0.0, i1.x, i2.x, 1.0 ));

      // Gradients: 7x7 points over a square, mapped onto an octahedron.
      // The ring size 17*17 = 289 is close to a multiple of 49 (49*6 = 294)
      float n_ = 0.142857142857; // 1.0/7.0
      vec3  ns = n_ * D.wyz - D.xzx;

      vec4 j = p - 49.0 * floor(p * ns.z * ns.z);  //  mod(p,7*7)

      vec4 x_ = floor(j * ns.z);
      vec4 y_ = floor(j - 7.0 * x_ );    // mod(j,N)

      vec4 x = x_ *ns.x + ns.yyyy;
      vec4 y = y_ *ns.x + ns.yyyy;
      vec4 h = 1.0 - abs(x) - abs(y);

      vec4 b0 = vec4( x.xy, y.xy );
      vec4 b1 = vec4( x.zw, y.zw );

      //vec4 s0 = vec4(lessThan(b0,0.0))*2.0 - 1.0;
      //vec4 s1 = vec4(lessThan(b1,0.0))*2.0 - 1.0;
      vec4 s0 = floor(b0)*2.0 + 1.0;
      vec4 s1 = floor(b1)*2.0 + 1.0;
      vec4 sh = -step(h, vec4(0.0));

      vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy ;
      vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww ;

      vec3 p0 = vec3(a0.xy,h.x);
      vec3 p1 = vec3(a0.zw,h.y);
      vec3 p2 = vec3(a1.xy,h.z);
      vec3 p3 = vec3(a1.zw,h.w);

      //Normalise gradients
      vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2, p2), dot(p3,p3)));
      p0 *= norm.x;
      p1 *= norm.y;
      p2 *= norm.z;
      p3 *= norm.w;

      // Mix final noise value
      vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
      m = m * m;
      return 42.0 * dot( m*m, vec4( dot(p0,x0), dot(p1,x1), 
                                    dot(p2,x2), dot(p3,x3) ) );
    }

    void main() {
      // Noise animation
      float noiseVal = snoise(vPosition * 2.0 + uTime * 0.5); // "Boiling" speed and scale
      
      // Normalize noise from [-1, 1] to [0, 1] for mixing
      float n = (noiseVal + 1.0) * 0.5;

      // Mix colors based on noise
      vec3 color = mix(uColorA, uColorB, n);

      // Fresnel effect for glowing rim
      vec3 viewDir = normalize(vViewPosition);
      float fresnel = pow(1.0 - dot(viewDir, vNormal), 2.0); // Rim intensity

      // Add rim glow to base color
      vec3 finalColor = color + uRimColor * fresnel * 1.5;

      gl_FragColor = vec4(finalColor, 1.0);
    }
  `
)

// Register the custom shader material as a JSX element
extend({ StarMaterial });

const Star3D = ({
    temperature = 5778,
    size = 1,
    color // Optional override
}) => {
    const materialRef = useRef();

    // Determine colors based on temperature/magnitude logic from props
    // Or just use the user-requested "plasma" defaults if no specific color is passed
    const { colorA, colorB } = useMemo(() => {
        // Defaults for the "plasma" effect requested
        // Made these significantly warmer (more yellow/orange) as requested
        let primary = new THREE.Color('#ff4500'); // OrangeRed (was Deep Red)
        let secondary = new THREE.Color('#ffcc00'); // Gold/Yellow (was Bright Orange)

        if (color) {
            // If a specific color is passed (e.g. from magnitude), make a palette around it
            const base = new THREE.Color(color);
            // Make the "hot" color (B) slightly lighter/yellow-shifted version of base
            secondary = base.clone().offsetHSL(0.05, 0, 0.1);
            // Make the "cool" color (A) the base color itself (instead of darkening it too much)
            primary = base;
        } else if (temperature > 10000) {
            // Blue star
            primary = new THREE.Color('#0047AB');
            secondary = new THREE.Color('#00BFFF');
        } else if (temperature > 6000) {
            // White/Yellow star
            primary = new THREE.Color('#FFA500');
            secondary = new THREE.Color('#FFFFE0');
        }

        return { colorA: primary, colorB: secondary };
    }, [color, temperature]);

    useFrame((state, delta) => {
        if (materialRef.current) {
            materialRef.current.uTime = state.clock.elapsedTime;
        }
    });

    return (
        <group dispose={null} scale={size}>
            {/* The Star Mesh */}
            <mesh>
                {/* Increased size from 1.5 to 2.2 for "bigger" look */}
                <sphereGeometry args={[2.2, 64, 64]} />
                {/* 
                  @ts-ignore - 'starMaterial' is generated by extend 
                  Using key to force re-render if colors change 
                */}
                <starMaterial
                    ref={materialRef}
                    key={colorA.getHexString()}
                    uColorA={colorA}
                    uColorB={colorB}
                    uRimColor={new THREE.Color('#FFFFFF')}
                />
            </mesh>

            {/* Outer Glow Sprite (Billboarding) could be added here for extra bloom */}

            {/* Ambient Sparkles */}
            <Sparkles
                count={40}
                scale={5}
                size={3}
                speed={0.4}
                opacity={0.5}
                color={colorB}
            />
        </group>
    );
};

export default Star3D;
