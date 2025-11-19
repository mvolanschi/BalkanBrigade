"use client";

import ColorBends from "../components/ColorBends";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function HomePage() {
  return (
    <div className="relative w-full h-screen overflow-hidden bg-black">
      {/* Full-screen ColorBends background */}
      <ColorBends
        className="absolute inset-0 w-full h-full"
        style={{ zIndex: 0 }}
        colors={["#00cc00", "#00aa00", "#00dd44", "#00bb55"]}
        rotation={45}
        autoRotate={1}
        speed={0.2}
        scale={1.0}
        frequency={1.2}
        warpStrength={1.0}
        mouseInfluence={0.8}
        parallax={0.5}
        noise={0.05}
        transparent={false}
      />

      {/* Content */}
      <div
        className="absolute inset-0 w-full h-full flex flex-col items-center justify-center pointer-events-none"
        style={{ zIndex: 999 }}
      >
        {/* Main heading */}
        <h1 className="text-white text-4xl md:text-5xl lg:text-6xl font-bold text-center mb-8 px-4 drop-shadow-2xl pointer-events-auto">
          AI-powered career prep
          <br />
          with an energy-aware edge.
        </h1>

        {/* Get Started Button -> routes to /upload */}
        <Button
          asChild
          size="lg"
          className="bg-white text-black hover:bg-gray-200 font-semibold px-8 py-6 text-lg rounded-full shadow-2xl pointer-events-auto"
        >
          <Link href="/upload">Get Started</Link>
        </Button>
      </div>

      {/* Powered by GreenPT - Bottom Left */}
      <div className="absolute bottom-6 left-6" style={{ zIndex: 999 }}>
        <p className="text-white/95 text-2xl md:text-3xl font-extrabold drop-shadow-[0_0_15px_rgba(0,255,100,0.5)] tracking-wide">
          Powered by <span className="text-green-300 font-black">GreenPT</span>
        </p>
      </div>
    </div>
  );
}
