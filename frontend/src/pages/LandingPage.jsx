import { useRef, useState, useEffect, Suspense } from 'react';
import { Canvas, useFrame, useThree, useLoader } from '@react-three/fiber';
import { useGLTF, Stars, Float, Text, Html } from '@react-three/drei';
import { useNavigate } from 'react-router-dom';
import gsap from 'gsap';
import * as THREE from 'three';
import './LandingPage.css';

// Planet Component - GLTF model
function Planet({ planetRef }) {
    // Saturn model
    const { scene } = useGLTF('/Assets/GLTFS/mars.glb');

    useFrame((state) => {
        if (planetRef.current) {
            planetRef.current.rotation.y += 0.0005;
        }
    });

    return (
        <primitive
            ref={planetRef}
            object={scene}
            scale={0.010}
            position={[0, -5.5, 0]}
            rotation={[0.1, 0, 0]}
        />
    );
}

// Animated Stars Background
function AnimatedStars({ starsRef }) {
    useFrame((state) => {
        if (starsRef.current) {
            starsRef.current.rotation.x = state.clock.elapsedTime * 0.02;
            starsRef.current.rotation.y = state.clock.elapsedTime * 0.01;
        }
    });

    return (
        <group ref={starsRef}>
            <Stars
                radius={100}
                depth={50}
                count={5000}
                factor={4}
                saturation={0}
                fade
                speed={1}
            />
        </group>
    );
}

// Camera Controller for Zoom Animation
function CameraController({ isTransitioning, onTransitionComplete }) {
    const { camera } = useThree();

    useEffect(() => {
        if (isTransitioning) {
            // Zoom forward animation
            gsap.to(camera.position, {
                z: -20,
                y: 5,
                duration: 2,
                ease: "power2.inOut",
                onComplete: onTransitionComplete
            });

            gsap.to(camera.rotation, {
                x: -0.3,
                duration: 2,
                ease: "power2.inOut"
            });
        }
    }, [isTransitioning, camera, onTransitionComplete]);

    return null;
}

// Floating Astronaut as 2D Sprite
function Astronaut({ astronautRef }) {
    const texture = useLoader(THREE.TextureLoader, '/Assets/Images/Picture1.png');

    return (
        <sprite ref={astronautRef} position={[0, 0.5, 2]} scale={[4.5, 4.5, 1]}>
            <spriteMaterial map={texture} transparent={true} />
        </sprite>
    );
}

// Main 3D Scene
function Scene({ isTransitioning, onTransitionComplete }) {
    const planetRef = useRef();
    const astronautRef = useRef();
    const starsRef = useRef();

    useEffect(() => {
        if (isTransitioning) {
            // Animate Planet down
            if (planetRef.current) {
                gsap.to(planetRef.current.position, {
                    y: -15,
                    z: 5,
                    duration: 2,
                    ease: "power2.inOut"
                });
                gsap.to(planetRef.current.scale, {
                    x: 8,
                    y: 8,
                    z: 8,
                    duration: 2,
                    ease: "power2.inOut"
                });
            }

            // Animate Astronaut up and fade
            if (astronautRef.current) {
                gsap.to(astronautRef.current.position, {
                    y: 10,
                    duration: 2,
                    ease: "power2.inOut"
                });
                gsap.to(astronautRef.current.material, {
                    opacity: 0,
                    duration: 1,
                    ease: "power2.inOut"
                });
            }

            // Speed up stars
            if (starsRef.current) {
                gsap.to(starsRef.current.rotation, {
                    z: Math.PI * 2,
                    duration: 2,
                    ease: "power2.inOut"
                });
            }
        }
    }, [isTransitioning]);

    return (
        <>
            <ambientLight intensity={0.3} />
            <directionalLight position={[10, 10, 5]} intensity={1} />
            <pointLight position={[-10, -10, -10]} intensity={0.5} color="#4444ff" />

            <AnimatedStars starsRef={starsRef} />

            <Suspense fallback={null}>
                <Planet planetRef={planetRef} />
                <Astronaut astronautRef={astronautRef} />
            </Suspense>

            <CameraController
                isTransitioning={isTransitioning}
                onTransitionComplete={onTransitionComplete}
            />
        </>
    );
}

// Main Landing Page Component
function LandingPage() {
    const [isTransitioning, setIsTransitioning] = useState(false);
    const [showOverlay, setShowOverlay] = useState(false);
    const navigate = useNavigate();
    const overlayRef = useRef();

    const handleEnterClick = () => {
        setIsTransitioning(true);

        // Start overlay fade in
        setTimeout(() => {
            setShowOverlay(true);
        }, 1500);
    };

    const handleTransitionComplete = () => {
        // Navigate to login page
        setTimeout(() => {
            navigate('/login');
        }, 500);
    };

    return (
        <div className="landing-container">
            {/* 3D Canvas */}
            <Canvas
                camera={{ position: [0, 0, 8], fov: 60 }}
                className="landing-canvas"
            >
                <Scene
                    isTransitioning={isTransitioning}
                    onTransitionComplete={handleTransitionComplete}
                />
            </Canvas>

            {/* UI Overlay */}
            <div className={`landing-overlay ${isTransitioning ? 'transitioning' : ''}`}>
                {/* Logo / Title */}
                <div className="landing-title-container">
                    <h1 className="landing-title">
                        <span className="title-cosmic">COSMIC</span>
                    </h1>
                    <p className="landing-subtitle">Data Fusion Platform</p>
                    <p className="landing-tagline">Explore the infinite.</p>
                </div>

                {/* Enter Button */}
                <button
                    className={`enter-button ${isTransitioning ? 'hidden' : ''}`}
                    onClick={handleEnterClick}
                >
                    <span>Enter COSMIC</span>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M7 17L17 7M17 7H7M17 7V17" />
                    </svg>
                </button>
            </div>

            {/* Transition Overlay */}
            <div
                ref={overlayRef}
                className={`transition-overlay ${showOverlay ? 'active' : ''}`}
            />
        </div>
    );
}

export default LandingPage;
