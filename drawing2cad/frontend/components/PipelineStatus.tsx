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
  // Internal display step — we intercept the -1 transition to play the final strike first
  const [displayStep, setDisplayStep] = useState(activeStep)
  const [finalStrike, setFinalStrike] = useState(false)
  const mounted = useRef(false)

  useEffect(() => {
    // Skip on mount
    if (!mounted.current) { mounted.current = true; return }

    if (activeStep === -1) {
      // Play final strike, then flip to done
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

  const isDone     = displayStep === -1 && !finalStrike
  const isValidate = (displayStep === 3 || finalStrike)
  const stickX     = isDone ? 318 : (stickPositions[Math.max(0, displayStep)] ?? 318)

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '4px 0' }}>
      <style>{`
        /* Running */
        @keyframes rLL { 0%,100%{transform:rotate(28deg)} 50%{transform:rotate(-28deg)} }
        @keyframes rLR { 0%,100%{transform:rotate(-28deg)} 50%{transform:rotate(28deg)} }
        @keyframes rAL { 0%,100%{transform:rotate(22deg)} 50%{transform:rotate(-18deg)} }
        @keyframes rAR { 0%,100%{transform:rotate(-22deg)} 50%{transform:rotate(18deg)} }

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

        /* Final strike — one-shot */
        @keyframes finalPunch {
          0%   { transform: rotate(-80deg); }
          28%  { transform: rotate(75deg);  }
          55%  { transform: rotate(45deg);  }
          100% { transform: rotate(12deg);  }
        }
        @keyframes finalLegL {
          0%, 100% { transform: rotate(22deg); }
        }
        @keyframes finalLegR {
          0%, 100% { transform: rotate(-22deg); }
        }
        @keyframes finalBurst {
          0%         { opacity:0; transform:scale(0); }
          22%, 55%   { opacity:1; transform:scale(1); }
          100%       { opacity:0; transform:scale(2.2); }
        }

        /* All nodes blast on final strike */
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

        /* Active node glow */
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
              /* ── Final strike: one big punch ── */
              <>
                {/* Left arm braced back */}
                <line x1="0" y1="34" x2="-16" y2="44" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
                {/* Right punch arm */}
                <g transform="translate(0,34)">
                  <g style={{ transformOrigin: '0 0', animation: 'finalPunch 0.95s cubic-bezier(0.2,0,0.1,1) forwards' }}>
                    <line x1="0" y1="0" x2="16" y2="-8"  stroke="white" strokeWidth="2.2" strokeLinecap="round" />
                    <line x1="16" y1="-8" x2="30" y2="-14" stroke="white" strokeWidth="2.2" strokeLinecap="round" />
                    {/* Punch burst at fist tip */}
                    <g transform="translate(30,-14)" style={{ animation: 'finalBurst 0.95s ease-out forwards' }}>
                      <circle cx="0" cy="0" r="8" fill="rgba(77,154,255,0.3)" stroke="#4d9aff" strokeWidth="1.5" />
                      <line x1="-7" y1="0"  x2="7"  y2="0"  stroke="#4d9aff" strokeWidth="2" strokeLinecap="round" />
                      <line x1="0"  y1="-7" x2="0"  y2="7"  stroke="#4d9aff" strokeWidth="2" strokeLinecap="round" />
                      <line x1="-5" y1="-5" x2="5"  y2="5"  stroke="#4d9aff" strokeWidth="1.5" strokeLinecap="round" />
                      <line x1="5"  y1="-5" x2="-5" y2="5"  stroke="#4d9aff" strokeWidth="1.5" strokeLinecap="round" />
                    </g>
                  </g>
                </g>
                {/* Legs — planted wide stance */}
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
            ) : (
              /* ── Steps 0-2: running ── */
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
