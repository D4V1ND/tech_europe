'use client'
import { useState, useEffect, useRef } from 'react'

const STEPS = [
  { id: 'load',     label: 'Load' },
  { id: 'extract',  label: 'Extract' },
  { id: 'generate', label: 'Generate' },
  { id: 'validate', label: 'Validate' },
]

interface PipelineStatusProps {
  activeStep: number  // 0-3, -1 = done
}

export function PipelineStatus({ activeStep }: PipelineStatusProps) {
  const [displayStep, setDisplayStep] = useState(activeStep)
  const [finalStrike, setFinalStrike] = useState(false)
  const mounted = useRef(false)

  useEffect(() => {
    if (!mounted.current) { mounted.current = true; return }
    if (activeStep === -1) {
      setFinalStrike(true)
      const t = setTimeout(() => {
        setFinalStrike(false)
        setDisplayStep(-1)
      }, 950)
      return () => clearTimeout(t)
    }
    setDisplayStep(activeStep)
  }, [activeStep])

  const nodeX = [62, 162, 262, 362]
  const nodeY  = 40
  const stickPositions = [18, 118, 218, 318]

  const isDone      = displayStep === -1 && !finalStrike
  const isExtract   = !isDone && !finalStrike && displayStep === 1
  const isGenerate  = !isDone && !finalStrike && displayStep === 2
  const isValidate  = displayStep === 3 || finalStrike
  const stickX      = isDone ? 318 : (stickPositions[Math.max(0, displayStep)] ?? 318)

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '4px 0' }}>
      <style>{`
        /* Running */
        @keyframes rLL { 0%,100%{transform:rotate(28deg)} 50%{transform:rotate(-28deg)} }
        @keyframes rLR { 0%,100%{transform:rotate(-28deg)} 50%{transform:rotate(28deg)} }
        @keyframes rAL { 0%,100%{transform:rotate(22deg)} 50%{transform:rotate(-18deg)} }
        @keyframes rAR { 0%,100%{transform:rotate(-22deg)} 50%{transform:rotate(18deg)} }

        /* Extract: hold image */
        @keyframes examHold {
          0%,100% { transform: rotate(0deg); }
          40%     { transform: rotate(4deg); }
          70%     { transform: rotate(-3deg); }
        }
        /* Extract: magnifying glass arm sweeps left-right */
        @keyframes examScan {
          0%      { transform: rotate(-30deg); }
          45%     { transform: rotate(10deg); }
          100%    { transform: rotate(-30deg); }
        }
        /* Scan beam travels top→bottom through the image */
        @keyframes scanBeam {
          0%        { transform: translateY(0px);  opacity: 0.85; }
          72%       { transform: translateY(11px); opacity: 0.85; }
          85%       { transform: translateY(13px); opacity: 0; }
          90%,100%  { transform: translateY(0px);  opacity: 0; }
        }
        /* Lens pulse */
        @keyframes lensPulse {
          0%,100% { opacity:0.55; }
          50%     { opacity:1; filter:drop-shadow(0 0 4px #4d9aff); }
        }

        /* Generate: hammering a box into existence */
        @keyframes hammerSwing {
          0%        { transform: rotate(-68deg); }
          30%       { transform: rotate(-72deg); }
          54%       { transform: rotate(24deg);  }
          65%       { transform: rotate(20deg);  }
          82%       { transform: rotate(-52deg); }
          100%      { transform: rotate(-68deg); }
        }
        @keyframes hammerSpark {
          0%, 51%   { opacity: 0; transform: scale(0);   }
          57%       { opacity: 1; transform: scale(1);   }
          70%       { opacity: 0; transform: scale(1.9); }
          100%      { opacity: 0; }
        }
        @keyframes buildBrace {
          0%, 100%  { transform: rotate(28deg); }
          57%       { transform: rotate(33deg); }
        }
        @keyframes buildLegL {
          0%, 100%  { transform: rotate(15deg); }
          57%       { transform: rotate(16deg); }
        }
        @keyframes buildLegR {
          0%, 100%  { transform: rotate(-15deg); }
          57%       { transform: rotate(-17deg); }
        }
        /* Box face flashes orange on impact then settles blue */
        @keyframes boxFlash {
          0%, 50%   { fill: rgba(77,154,255,0.13); stroke: rgba(77,154,255,0.55); }
          57%       { fill: rgba(255,170,50,0.35);  stroke: rgba(255,200,80,0.9); }
          72%       { fill: rgba(77,154,255,0.13); stroke: rgba(77,154,255,0.55); }
          100%      { fill: rgba(77,154,255,0.13); stroke: rgba(77,154,255,0.55); }
        }
        @keyframes boxTopFlash {
          0%, 50%   { fill: rgba(77,154,255,0.2);  stroke: rgba(77,154,255,0.75); }
          57%       { fill: rgba(255,200,80,0.5);   stroke: rgba(255,220,100,1);  }
          72%       { fill: rgba(77,154,255,0.2);  stroke: rgba(77,154,255,0.75); }
          100%      { fill: rgba(77,154,255,0.2);  stroke: rgba(77,154,255,0.75); }
        }

        /* Whip */
        @keyframes whipSwing {
          0%        { transform: rotate(0deg); }
          28%       { transform: rotate(-70deg); }
          45%       { transform: rotate(-72deg); }
          55%       { transform: rotate(48deg); }
          68%       { transform: rotate(32deg); }
          88%, 100% { transform: rotate(0deg); }
        }
        @keyframes whipShow {
          0%,50% { opacity:0; } 55% { opacity:1; } 63% { opacity:0; } 100% { opacity:0; }
        }
        @keyframes crackSpark {
          0%,52% { opacity:0; transform:scale(0); }
          56%    { opacity:1; transform:scale(1); }
          64%    { opacity:0; transform:scale(1.4); }
          100%   { opacity:0; }
        }
        @keyframes wLegL { 0%,100%{transform:rotate(18deg)} 50%{transform:rotate(-18deg)} }
        @keyframes wLegR { 0%,100%{transform:rotate(-18deg)} 50%{transform:rotate(18deg)} }

        /* Final strike */
        @keyframes finalPunch {
          0%   { transform: rotate(-80deg); }
          28%  { transform: rotate(75deg);  }
          55%  { transform: rotate(45deg);  }
          100% { transform: rotate(12deg);  }
        }
        @keyframes finalLegL { 0%,100% { transform: rotate(22deg); } }
        @keyframes finalLegR { 0%,100% { transform: rotate(-22deg); } }
        @keyframes finalBurst {
          0%         { opacity:0; transform:scale(0); }
          22%, 55%   { opacity:1; transform:scale(1); }
          100%       { opacity:0; transform:scale(2.2); }
        }
        @keyframes nodeBlast {
          0%        { fill:rgba(255,255,255,0.04); stroke:rgba(255,255,255,0.2); filter:none; }
          25%, 65%  { fill:rgba(77,154,255,0.95);  stroke:#4d9aff; filter:drop-shadow(0 0 14px #4d9aff); }
          100%      { fill:rgba(77,154,255,0.72);  stroke:#4d9aff; filter:none; }
        }
        @keyframes edgeBlast {
          0%        { stroke:rgba(255,255,255,0.14); }
          25%, 65%  { stroke:#4d9aff; filter:drop-shadow(0 0 6px #4d9aff); }
          100%      { stroke:#4d9aff; filter:none; }
        }
        @keyframes nGlow {
          0%,100%{ opacity:0.5; } 50%{ opacity:1; filter:drop-shadow(0 0 6px #4d9aff); }
        }
      `}</style>

      <svg viewBox="0 0 420 92" width="420" height="92" style={{ overflow: 'visible' }}>

        {/* ── Edges ── */}
        {nodeX.slice(0, -1).map((x, i) => (
          <line key={i}
            x1={x} y1={nodeY} x2={nodeX[i + 1]} y2={nodeY}
            style={finalStrike ? { animation: `edgeBlast 0.95s ease-out forwards` } : undefined}
            stroke={
              finalStrike ? undefined :
              (isDone || i < displayStep) ? '#4d9aff' : 'rgba(255,255,255,0.14)'
            }
            strokeWidth="1.5"
          />
        ))}

        {/* ── Nodes ── */}
        {nodeX.map((x, i) => {
          const done   = !finalStrike && (isDone || i < displayStep)
          const active = !isDone && !finalStrike && i === displayStep
          return (
            <g key={i} transform={`translate(${x},${nodeY})`}
              style={
                finalStrike ? { animation: `nodeBlast 0.95s ease-out forwards` } :
                active      ? { animation: 'nGlow 1s ease-in-out infinite' } :
                undefined
              }>
              <circle cx="0" cy="0"
                r={active ? 9 : 7}
                fill={finalStrike ? undefined : done ? 'rgba(77,154,255,0.7)' : active ? 'rgba(77,154,255,0.2)' : 'rgba(255,255,255,0.04)'}
                stroke={finalStrike ? undefined : done ? '#4d9aff' : active ? 'rgba(77,154,255,0.7)' : 'rgba(255,255,255,0.2)'}
                strokeWidth="1.7"
              />
              {!finalStrike && done && (
                <text x="0" y="4.5" textAnchor="middle" fill="white" fontSize="7" fontWeight="bold">✓</text>
              )}
              {!finalStrike && !done && !active && (
                <text x="0" y="4" textAnchor="middle" fill="rgba(255,255,255,0.28)" fontSize="7">{i + 1}</text>
              )}
              <text x="0" y="22" textAnchor="middle" fontSize="8.5" fontFamily="system-ui,sans-serif"
                fontWeight={active ? '600' : '400'}
                fill={active ? 'white' : (done || finalStrike) ? 'rgba(255,255,255,0.5)' : 'rgba(255,255,255,0.22)'}>
                {STEPS[i].label}
              </text>
            </g>
          )
        })}

        {/* ── Stickman ── */}
        {!isDone && (
          <g style={{
            transform: `translateX(${finalStrike ? 318 : stickX}px)`,
            transition: finalStrike ? 'none' : 'transform 0.65s cubic-bezier(0.4,0,0.2,1)',
          }}>
            {/* Head */}
            <circle cx="0" cy="11" r="8" stroke="white" strokeWidth="2.2" fill="none" />
            {/* Body */}
            <line x1="0" y1="19" x2="0" y2="52" stroke="white" strokeWidth="2.2" strokeLinecap="round" />

            {finalStrike ? (
              /* ── Final strike ── */
              <>
                <line x1="0" y1="34" x2="-16" y2="44" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
                <g transform="translate(0,34)">
                  <g style={{ transformOrigin: '0 0', animation: 'finalPunch 0.95s cubic-bezier(0.2,0,0.1,1) forwards' }}>
                    <line x1="0" y1="0" x2="16" y2="-8"  stroke="white" strokeWidth="2.2" strokeLinecap="round" />
                    <line x1="16" y1="-8" x2="30" y2="-14" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
                    <g transform="translate(30,-14)" style={{ animation: 'finalBurst 0.95s ease-out forwards' }}>
                      <circle cx="0" cy="0" r="8" fill="rgba(77,154,255,0.3)" stroke="#4d9aff" strokeWidth="1.5" />
                      <line x1="-7" y1="0"  x2="7"  y2="0"  stroke="#4d9aff" strokeWidth="2" strokeLinecap="round" />
                      <line x1="0"  y1="-7" x2="0"  y2="7"  stroke="#4d9aff" strokeWidth="2" strokeLinecap="round" />
                      <line x1="-5" y1="-5" x2="5"  y2="5"  stroke="#4d9aff" strokeWidth="1.5" strokeLinecap="round" />
                      <line x1="5"  y1="-5" x2="-5" y2="5"  stroke="#4d9aff" strokeWidth="1.5" strokeLinecap="round" />
                    </g>
                  </g>
                </g>
                <g transform="translate(0,52)">
                  <g style={{ transformOrigin: '0 0', animation: 'finalLegL 0.95s forwards' }}>
                    <line x1="0" y1="0" x2="-13" y2="24" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
                  </g>
                </g>
                <g transform="translate(0,52)">
                  <g style={{ transformOrigin: '0 0', animation: 'finalLegR 0.95s forwards' }}>
                    <line x1="0" y1="0" x2="13" y2="24" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
                  </g>
                </g>
              </>
            ) : isValidate ? (
              /* ── Validate: whip ── */
              <>
                <line x1="0" y1="34" x2="-14" y2="46" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
                <g transform="translate(0,34)">
                  <g style={{ transformOrigin: '0 0', animation: 'whipSwing 1.9s cubic-bezier(0.4,0,0.2,1) infinite' }}>
                    <line x1="0" y1="0" x2="16" y2="-9"  stroke="white" strokeWidth="2.2" strokeLinecap="round" />
                    <line x1="16" y1="-9" x2="28" y2="-17" stroke="white" strokeWidth="2" strokeLinecap="round" />
                    <path d="M28,-17 Q46,-29 64,-14 Q71,-9 77,-16"
                      stroke="rgba(255,255,255,0.88)" strokeWidth="1.7" fill="none" strokeLinecap="round"
                      style={{ animation: 'whipShow 1.9s ease-in-out infinite' }} />
                    <g transform="translate(77,-16)" style={{ animation: 'crackSpark 1.9s ease-out infinite' }}>
                      <line x1="-5" y1="0"  x2="5"  y2="0"  stroke="#ffdd55" strokeWidth="2" strokeLinecap="round" />
                      <line x1="0"  y1="-5" x2="0"  y2="5"  stroke="#ffdd55" strokeWidth="2" strokeLinecap="round" />
                      <line x1="-4" y1="-4" x2="4"  y2="4"  stroke="#ffdd55" strokeWidth="1.5" strokeLinecap="round" />
                      <line x1="4"  y1="-4" x2="-4" y2="4"  stroke="#ffdd55" strokeWidth="1.5" strokeLinecap="round" />
                    </g>
                  </g>
                </g>
                <g transform="translate(0,52)">
                  <g style={{ transformOrigin: '0 0', animation: 'wLegL 1.9s ease-in-out infinite' }}>
                    <line x1="0" y1="0" x2="-11" y2="24" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
                  </g>
                </g>
                <g transform="translate(0,52)">
                  <g style={{ transformOrigin: '0 0', animation: 'wLegR 1.9s ease-in-out infinite' }}>
                    <line x1="0" y1="0" x2="11" y2="24" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
                  </g>
                </g>
              </>
            ) : isExtract ? (
              /* ── Extract: hold image + magnifying glass scan ── */
              <>
                {/* Left arm raised — holds the drawing up */}
                <g transform="translate(0,32)">
                  <g style={{ transformOrigin: '0 0', animation: 'examHold 3s ease-in-out infinite' }}>
                    <line x1="0" y1="0" x2="-11" y2="-9"  stroke="white" strokeWidth="2.1" strokeLinecap="round" />
                    <line x1="-11" y1="-9" x2="-20" y2="-18" stroke="white" strokeWidth="2" strokeLinecap="round" />
                    {/* Drawing / image held at arm tip */}
                    <g transform="translate(-20,-18)">
                      {/* Frame */}
                      <rect x="-9" y="-8" width="18" height="14" rx="1.5"
                        fill="rgba(8,10,28,0.92)" stroke="rgba(77,154,255,0.9)" strokeWidth="1.5" />
                      {/* Static content lines */}
                      <line x1="-6" y1="-3.5" x2="6"  y2="-3.5" stroke="rgba(255,255,255,0.22)" strokeWidth="0.9" />
                      <line x1="-6" y1="0"    x2="4"  y2="0"    stroke="rgba(255,255,255,0.22)" strokeWidth="0.9" />
                      <line x1="-6" y1="3.5"  x2="5"  y2="3.5"  stroke="rgba(255,255,255,0.22)" strokeWidth="0.9" />
                      {/* Scan beam sweeping top→bottom */}
                      <rect x="-9" y="-8" width="18" height="3"
                        fill="rgba(77,154,255,0.45)"
                        style={{ animation: 'scanBeam 1.7s linear infinite' }} />
                    </g>
                  </g>
                </g>

                {/* Right arm — magnifying glass sweeping across the image */}
                <g transform="translate(0,32)">
                  <g style={{ transformOrigin: '0 0', animation: 'examScan 2.2s ease-in-out infinite' }}>
                    <line x1="0" y1="0" x2="-13" y2="-6" stroke="white" strokeWidth="2.1" strokeLinecap="round" />
                    {/* Magnifying glass lens at arm tip */}
                    <g transform="translate(-13,-6)"
                      style={{ animation: 'lensPulse 2.2s ease-in-out infinite' }}>
                      <circle cx="0" cy="0" r="5.5"
                        fill="rgba(77,154,255,0.12)" stroke="#4d9aff" strokeWidth="1.4" />
                      {/* Handle */}
                      <line x1="3.8" y1="3.8" x2="7" y2="7"
                        stroke="#4d9aff" strokeWidth="1.6" strokeLinecap="round" />
                    </g>
                  </g>
                </g>

                {/* Legs — standing still */}
                <line x1="0" y1="52" x2="-10" y2="76" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
                <line x1="0" y1="52" x2="10"  y2="76" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
              </>
            ) : isGenerate ? (
              /* ── Generate: hammering a box into existence ── */
              <>
                {/* Right arm — hammer swing */}
                <g transform="translate(0,34)">
                  <g style={{ transformOrigin: '0 0', animation: 'hammerSwing 1.35s cubic-bezier(0.4,0,0.2,1) infinite' }}>
                    <line x1="0" y1="0" x2="20" y2="0" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
                    {/* Hammer head — rect perpendicular at arm tip */}
                    <rect x="18" y="-5" width="8" height="5" rx="1"
                      fill="rgba(255,255,255,0.92)" stroke="none" />
                  </g>
                </g>

                {/* Left arm — bracing the workpiece */}
                <g transform="translate(0,34)">
                  <g style={{ transformOrigin: '0 0', animation: 'buildBrace 1.35s ease-in-out infinite' }}>
                    <line x1="0" y1="0" x2="-15" y2="10" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
                  </g>
                </g>

                {/* Isometric box being built — flashes orange on hammer impact */}
                <g>
                  {/* Top face */}
                  <polygon points="8,44 18,39 30,44 20,49"
                    style={{ animation: 'boxTopFlash 1.35s ease-out infinite' }}
                    strokeWidth="1.3" />
                  {/* Left face */}
                  <polygon points="8,44 8,57 20,62 20,49"
                    style={{ animation: 'boxFlash 1.35s ease-out infinite' }}
                    strokeWidth="1.3" />
                  {/* Right face */}
                  <polygon points="20,49 20,62 30,57 30,44"
                    style={{ animation: 'boxFlash 1.35s ease-out infinite 0.05s' }}
                    strokeWidth="1.3" />
                </g>

                {/* Impact sparks at top of box */}
                <g transform="translate(19,44)"
                  style={{ animation: 'hammerSpark 1.35s ease-out infinite' }}>
                  <line x1="-5" y1="0"  x2="5"  y2="0"  stroke="#ffaa33" strokeWidth="2" strokeLinecap="round" />
                  <line x1="0"  y1="-5" x2="0"  y2="3"  stroke="#ffaa33" strokeWidth="2" strokeLinecap="round" />
                  <line x1="-4" y1="-4" x2="3"  y2="2"  stroke="#ffaa33" strokeWidth="1.5" strokeLinecap="round" />
                  <line x1="4"  y1="-3" x2="-2" y2="3"  stroke="#ffaa33" strokeWidth="1.5" strokeLinecap="round" />
                </g>

                {/* Legs — planted wide, slight recoil */}
                <g transform="translate(0,52)">
                  <g style={{ transformOrigin: '0 0', animation: 'buildLegL 1.35s ease-in-out infinite' }}>
                    <line x1="0" y1="0" x2="-12" y2="24" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
                  </g>
                </g>
                <g transform="translate(0,52)">
                  <g style={{ transformOrigin: '0 0', animation: 'buildLegR 1.35s ease-in-out infinite' }}>
                    <line x1="0" y1="0" x2="12" y2="24" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
                  </g>
                </g>
              </>
            ) : (
              /* ── Steps 0: running ── */
              <>
                <g transform="translate(0,32)">
                  <g style={{ transformOrigin: '0 0', animation: 'rAR 0.44s ease-in-out infinite' }}>
                    <line x1="0" y1="0" x2="14" y2="7" stroke="white" strokeWidth="2.1" strokeLinecap="round" />
                  </g>
                </g>
                <g transform="translate(0,32)">
                  <g style={{ transformOrigin: '0 0', animation: 'rAL 0.44s ease-in-out infinite' }}>
                    <line x1="0" y1="0" x2="-14" y2="7" stroke="white" strokeWidth="2.1" strokeLinecap="round" />
                  </g>
                </g>
                <g transform="translate(0,52)">
                  <g style={{ transformOrigin: '0 0', animation: 'rLL 0.44s ease-in-out infinite' }}>
                    <line x1="0" y1="0" x2="-11" y2="24" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
                  </g>
                </g>
                <g transform="translate(0,52)">
                  <g style={{ transformOrigin: '0 0', animation: 'rLR 0.44s ease-in-out infinite' }}>
                    <line x1="0" y1="0" x2="11" y2="24" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
                  </g>
                </g>
              </>
            )}
          </g>
        )}

      </svg>
    </div>
  )
}
