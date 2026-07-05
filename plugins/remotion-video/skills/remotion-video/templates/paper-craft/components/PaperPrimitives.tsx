// PaperPrimitives — flat SVG "cut paper" starter shapes for the paper-craft
// profile. They stand in for generated PNG art so a diorama can be assembled
// (and moved) with zero external assets. Swap any primitive for a
// <SafeImg src={staticFile("layers/wheat.png")} /> once you have real art; the
// LayeredParallaxScene rig behaves identically either way.
//
// All colors come from `paper` in the profile style-guide so hand-drawn and
// generated layers share one palette. Each primitive fills the 1920×1080 frame
// and is positioned within its own viewBox — depth/parallax is applied by the
// rig, not here.

import React from "react";
import { AbsoluteFill } from "remotion";
import { paper, shadows } from "../style-guide";

const lift = { filter: shadows.paperFilter } as const;

const Svg: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill>
    <svg
      viewBox="0 0 1920 1080"
      width="100%"
      height="100%"
      preserveAspectRatio="xMidYMid slice"
    >
      {children}
    </svg>
  </AbsoluteFill>
);

// Far background: sky + distant navy hill bands.
export const SkyFar: React.FC = () => (
  <Svg>
    <rect width="1920" height="1080" fill={paper.hillFar} />
    <path d="M0 430 Q 480 330 960 400 T 1920 380 V1080 H0 Z" fill={paper.hillFar} style={lift} />
    <path d="M0 560 Q 520 460 1080 540 T 1920 520 V1080 H0 Z" fill={paper.hillMid} style={lift} />
  </Svg>
);

const House: React.FC<{ x: number; y: number; s: number }> = ({ x, y, s }) => (
  <g transform={`translate(${x} ${y}) scale(${s})`} style={lift}>
    <rect x="0" y="40" width="120" height="90" fill={paper.kraft} />
    <path d="M-14 44 L60 0 L134 44 Z" fill={paper.roof} />
    <rect x="20" y="70" width="26" height="26" fill={paper.kraftDark} />
    <rect x="74" y="70" width="26" height="26" fill={paper.kraftDark} />
  </g>
);

// Midground: a scatter of village houses on the hills.
export const Village: React.FC = () => (
  <Svg>
    <House x={150} y={330} s={1.1} />
    <House x={330} y={400} s={0.85} />
    <House x={1280} y={360} s={0.9} />
    <House x={1500} y={420} s={1.05} />
  </Svg>
);

// Center of interest: silos with a warm glow spilling out.
export const Silos: React.FC = () => (
  <Svg>
    <ellipse cx="900" cy="720" rx="360" ry="120" fill={paper.glow} opacity="0.35" />
    {[760, 900, 1040].map((cx, i) => (
      <g key={cx} transform={`translate(${cx} ${540 + (i === 1 ? -20 : 0)})`} style={lift}>
        <rect x="-70" y="0" width="140" height="200" fill={i === 1 ? paper.kraftLite : paper.kraft} />
        <path d="M-70 0 L0 -90 L70 0 Z" fill={paper.kraftDark} />
        <rect x="-3" y="-150" width="6" height="60" fill={paper.kraftDark} />
        <path d="M3 -150 L46 -138 L3 -120 Z" fill={paper.roof} />
      </g>
    ))}
    <circle cx="900" cy="640" r="26" fill="#2a2016" style={lift} />
  </Svg>
);

// Foreground: a swaying wheat field.
export const Wheat: React.FC = () => (
  <Svg>
    <path d="M760 1080 Q 1100 720 1500 760 T 1920 720 V1080 Z" fill={paper.wheat} style={lift} />
    {Array.from({ length: 26 }).map((_, i) => {
      const x = 800 + i * 44;
      const y = 900 - (i % 4) * 24;
      return (
        <g key={i} transform={`translate(${x} ${y})`}>
          <rect x="-2" y="0" width="4" height="150" fill={paper.wheatDark} />
          <ellipse cx="0" cy="-6" rx="12" ry="26" fill={paper.kraftLite} />
        </g>
      );
    })}
  </Svg>
);

// Hero foreground: a cat holding a mouse (left). Crude on purpose — a stand-in
// for a generated character PNG.
export const Cat: React.FC = () => (
  <Svg>
    <g transform="translate(210 470)" style={lift}>
      <ellipse cx="120" cy="420" rx="150" ry="60" fill="rgba(0,0,0,0.25)" />
      <path d="M40 520 Q 20 300 120 240 Q 230 300 210 520 Z" fill={paper.kraft} />
      <circle cx="120" cy="180" r="95" fill={paper.kraft} />
      <path d="M60 120 L40 40 L110 110 Z" fill={paper.kraft} />
      <path d="M180 120 L200 40 L130 110 Z" fill={paper.kraft} />
      <path d="M120 130 Q 100 210 120 250 Q 140 210 120 130 Z" fill={paper.kraftDark} opacity="0.6" />
      <circle cx="92" cy="175" r="12" fill="#3a2f1c" />
      <circle cx="150" cy="175" r="12" fill="#3a2f1c" />
      <ellipse cx="121" cy="205" rx="10" ry="7" fill="#7a6033" />
      <ellipse cx="150" cy="225" rx="26" ry="16" fill="#9a9aa2" />
      <circle cx="150" cy="222" r="5" fill="#c8c8cf" />
    </g>
  </Svg>
);
