export function PerspectiveGrid({ clipFraction = 0.50 }: { clipFraction?: number }) {
  const W = 1440
  const H = 900
  const clipY = H * clipFraction

  // Perspective lines: wide at clipY (top), converge slightly toward center going up
  // Bottom: full width 0→W. At clipY: slightly narrower (80%) → creates depth illusion
  // VP above the screen — lines start full-width at clipY and diverge beyond screen edges below
  const vpY  = clipY - H * 0.85
  const spread = (H - vpY) / (clipY - vpY)   // factor by which lines fan out going down

  const vCount = 15
  const perspLines = Array.from({ length: vCount }, (_, i) => {
    const topX = (i / (vCount - 1)) * W                    // 0..W full width at clipY
    const botX = W / 2 + (topX - W / 2) * spread           // diverges off-screen at H
    return { topX, botX }
  })

  // Horizontal lines: DENSE near top (far), SPARSE near bottom (near)
  // p > 1 packs lines toward clipY
  const hCount = 9
  const hLines = Array.from({ length: hCount }, (_, i) => {
    const t = Math.pow((i + 1) / (hCount + 1), 2.2)   // p=2.2 → dense at top
    const y = clipY + t * (H - clipY)
    const opacity = 0.07 + (1 - t) * 0.06 + t * 0.22  // brighter at bottom
    return { y, opacity }
  })

  return (
    <div
      className="pointer-events-none"
      aria-hidden
      style={{ position: 'absolute', inset: 0, overflow: 'hidden' }}
    >
      <svg
        style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}
        viewBox={`0 0 ${W} ${H}`}
        preserveAspectRatio="xMidYMid slice"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <radialGradient id="horizGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%"   stopColor="rgba(210,190,255,0.45)" />
            <stop offset="35%"  stopColor="rgba(170,150,240,0.15)" />
            <stop offset="100%" stopColor="rgba(0,0,0,0)" />
          </radialGradient>
          {/* Mask: fade in from top (transparent) to ~40% down (opaque) */}
          <linearGradient id="fadeGrad" x1="0" y1={clipY} x2="0" y2={clipY + (H - clipY) * 0.42} gradientUnits="userSpaceOnUse">
            <stop offset="0%"   stopColor="white" stopOpacity="0" />
            <stop offset="100%" stopColor="white" stopOpacity="1" />
          </linearGradient>
          <mask id="gridFade">
            <rect x={0} y={clipY} width={W} height={H - clipY} fill="url(#fadeGrad)" />
          </mask>
        </defs>

        <g mask="url(#gridFade)">
          {/* Perspective lines — narrower at top (far), wider at bottom (near) */}
          {perspLines.map(({ topX, botX }, i) => (
            <line
              key={`v${i}`}
              x1={topX} y1={clipY}
              x2={botX} y2={H}
              stroke="rgba(255,255,255,0.22)"
              strokeWidth="1"
            />
          ))}

          {/* Horizontal lines — dense at top (far away), sparse at bottom (close) */}
          {hLines.map(({ y, opacity }, i) => (
            <line
              key={`h${i}`}
              x1={0} y1={y}
              x2={W} y2={y}
              stroke={`rgba(255,255,255,${opacity.toFixed(2)})`}
              strokeWidth="1"
            />
          ))}
        </g>

        {/* Horizon glow — sits on top of the mask for a soft bloom at the edge */}
        <ellipse
          cx={W / 2}    cy={clipY}
          rx={W * 0.42} ry={H * 0.13}
          fill="url(#horizGlow)"
        />
      </svg>
    </div>
  )
}
