'use client'
import { useState } from 'react'
import {
  AreaChart, Area, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from 'recharts'
import { Button } from '@/components/ui/Button'
import { PerspectiveGrid } from '@/components/ui/PerspectiveGrid'
import { NewAnalysisModal } from '@/components/NewAnalysisModal'

const TABS = ['Overview', 'Projects', 'Plans', 'API Access', 'Settings'] as const
type Tab = typeof TABS[number]

// ── Glass card style ──────────────────────────────────────────────────────────

const glass: React.CSSProperties = {
  background: 'rgba(10, 8, 30, 0.55)',
  backdropFilter: 'blur(24px)',
  WebkitBackdropFilter: 'blur(24px)',
  border: '1px solid rgba(255,255,255,0.10)',
  borderRadius: 18,
}

const glassSubtle: React.CSSProperties = {
  background: 'rgba(255,255,255,0.04)',
  backdropFilter: 'blur(12px)',
  WebkitBackdropFilter: 'blur(12px)',
  border: '1px solid rgba(255,255,255,0.07)',
  borderRadius: 14,
}

// ── Chart data ────────────────────────────────────────────────────────────────

const API_USAGE_DATA = [
  { month: 'Jul', calls: 4100 },
  { month: 'Aug', calls: 6500 },
  { month: 'Sep', calls: 5000 },
  { month: 'Oct', calls: 8000 },
  { month: 'Nov', calls: 7200 },
  { month: 'Dec', calls: 9100 },
  { month: 'Jan', calls: 6000 },
  { month: 'Feb', calls: 8500 },
  { month: 'Mar', calls: 7800 },
  { month: 'Apr', calls: 9400 },
  { month: 'May', calls: 7000 },
  { month: 'Jun', calls: 8800 },
]

const ACCURACY_DATA = [
  { week: 'W1', accuracy: 96.1 },
  { week: 'W2', accuracy: 97.4 },
  { week: 'W3', accuracy: 96.8 },
  { week: 'W4', accuracy: 98.0 },
  { week: 'W5', accuracy: 97.5 },
  { week: 'W6', accuracy: 98.2 },
  { week: 'W7', accuracy: 98.1 },
  { week: 'W8', accuracy: 98.4 },
]

const PASS_FAIL_DATA = [
  { name: 'Passed', value: 84 },
  { name: 'Failed', value: 16 },
]

// ── Shared tooltip ─────────────────────────────────────────────────────────────

function ChartTooltip({ active, payload, label, unit = '' }: any) {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      ...glass,
      padding: '8px 12px',
      fontSize: 12,
    }}>
      <div style={{ color: 'rgba(255,255,255,0.5)', marginBottom: 2 }}>{label}</div>
      <div style={{ color: '#4d9aff', fontWeight: 600 }}>
        {payload[0].value.toLocaleString()}{unit}
      </div>
    </div>
  )
}

// ── Activity feed ─────────────────────────────────────────────────────────────

const ACTIVITY: { date: string; items: { text: string; sub: string; dot: string }[] }[] = [
  {
    date: 'Today',
    items: [
      { text: 'BRACKET-XY-300 validated', sub: '2:52 PM · 1 error open', dot: '#ff6060' },
      { text: 'turbine_blade_v3.step exported', sub: '1:10 PM · via API', dot: '#4d9aff' },
      { text: 'Text-to-CAD job started', sub: '11:44 AM · "mounting bracket for servo motor"', dot: '#f59e0b' },
    ],
  },
  {
    date: 'Yesterday',
    items: [
      { text: 'sarah@spacex.com invited', sub: 'Team · invite pending', dot: 'rgba(255,255,255,0.25)' },
      { text: 'Manufacturing validation failed', sub: 'thickness 8mm ≠ 5mm', dot: '#ff6060' },
    ],
  },
]

// ── Overview ──────────────────────────────────────────────────────────────────

function Overview({ onNewAnalysis }: { onNewAnalysis: () => void }) {
  return (
    <div className="flex flex-col gap-6">

      {/* Stats row */}
      <div
        className="grid grid-cols-4"
        style={{ ...glass, overflow: 'hidden' }}
      >
        {[
          { n: '94,231', label: 'API calls', note: '↑ 12% vs. last month' },
          { n: '1,847',  label: 'Models generated', note: '+23 this week' },
          { n: '98.4%',  label: 'Avg. accuracy', note: 'last 30 days' },
          { n: '12',     label: 'Team members', note: '3 invites pending' },
        ].map((s, i) => (
          <div
            key={s.label}
            className="px-6 py-6"
            style={{ borderRight: i < 3 ? '1px solid rgba(255,255,255,0.07)' : 'none' }}
          >
            <div style={{ fontSize: 30, fontWeight: 700, color: 'white', lineHeight: 1, marginBottom: 6 }}>{s.n}</div>
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.5)', marginBottom: 4 }}>{s.label}</div>
            <div style={{ fontSize: 11, color: '#4d9aff' }}>{s.note}</div>
          </div>
        ))}
      </div>

      {/* Quick actions */}
      <div className="flex gap-3">
        <button
          onClick={onNewAnalysis}
          className="flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors"
          style={{ background: 'rgba(77,154,255,0.15)', border: '1px solid rgba(77,154,255,0.3)', color: '#4d9aff', backdropFilter: 'blur(12px)' }}
        >
          ✦ New Analysis
        </button>
        {['API docs ↗', 'Invite teammate +'].map(a => (
          <button key={a} className="flex items-center gap-2 px-4 py-2 rounded-full text-sm"
            style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.45)', backdropFilter: 'blur(12px)', cursor: 'default' }}>
            {a}
          </button>
        ))}
      </div>

      {/* API Usage chart */}
      <div style={{ ...glass, padding: '20px 24px 16px' }}>
        <div className="flex items-baseline justify-between mb-4">
          <span style={{ color: 'white', fontWeight: 500, fontSize: 14 }}>API Usage</span>
          <span style={{ color: 'rgba(255,255,255,0.35)', fontSize: 12 }}>Jul 2024 – Jun 2025</span>
        </div>
        <ResponsiveContainer width="100%" height={160}>
          <AreaChart data={API_USAGE_DATA} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="apiGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#3e3281" stopOpacity={0.8} />
                <stop offset="100%" stopColor="#3e3281" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="month" tick={{ fill: 'rgba(255,255,255,0.35)', fontSize: 11 }} axisLine={false} tickLine={false} />
            <YAxis hide />
            <Tooltip content={<ChartTooltip unit=" calls" />} cursor={{ stroke: 'rgba(77,154,255,0.2)' }} />
            <Area type="monotone" dataKey="calls" stroke="#4d9aff" strokeWidth={2} fill="url(#apiGradient)" dot={false} activeDot={{ r: 4, fill: '#4d9aff', stroke: '#0a081e', strokeWidth: 2 }} />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Accuracy + Activity */}
      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">

        <div style={{ ...glass, padding: '20px 24px 16px' }}>
          <div className="flex items-baseline justify-between mb-4">
            <span style={{ color: 'white', fontWeight: 500, fontSize: 14 }}>Model Accuracy</span>
            <span style={{ color: 'rgba(255,255,255,0.35)', fontSize: 12 }}>last 8 weeks</span>
          </div>
          <ResponsiveContainer width="100%" height={120}>
            <LineChart data={ACCURACY_DATA} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
              <CartesianGrid vertical={false} stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="week" tick={{ fill: 'rgba(255,255,255,0.35)', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis hide domain={[95, 100]} />
              <Tooltip content={<ChartTooltip unit="%" />} cursor={{ stroke: 'rgba(77,154,255,0.2)' }} />
              <Line type="monotone" dataKey="accuracy" stroke="#4d9aff" strokeWidth={2} dot={{ r: 3, fill: '#4d9aff', stroke: '#0a081e', strokeWidth: 2 }} activeDot={{ r: 5, fill: '#4d9aff', stroke: '#0a081e', strokeWidth: 2 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div style={{ ...glass, padding: '20px 20px' }}>
          <div style={{ color: 'white', fontWeight: 500, fontSize: 14, marginBottom: 16 }}>Activity</div>
          <div className="flex flex-col gap-5">
            {ACTIVITY.map(group => (
              <div key={group.date}>
                <div style={{ fontSize: 10, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'rgba(255,255,255,0.3)', marginBottom: 10 }}>
                  {group.date}
                </div>
                <div className="flex flex-col gap-3 pl-3" style={{ borderLeft: '1px solid rgba(255,255,255,0.07)' }}>
                  {group.items.map((item, i) => (
                    <div key={i}>
                      <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full flex-shrink-0 -ml-[4.75px]" style={{ background: item.dot }} />
                        <span style={{ fontSize: 12, color: 'white' }}>{item.text}</span>
                      </div>
                      <div style={{ fontSize: 11, marginLeft: 14, marginTop: 2, color: 'rgba(255,255,255,0.35)' }}>{item.sub}</div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Donut */}
      <div style={{ ...glass, padding: '20px 24px', display: 'flex', alignItems: 'center', gap: 32 }}>
        <div>
          <div style={{ color: 'white', fontWeight: 500, fontSize: 14, marginBottom: 4 }}>Validation Results</div>
          <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: 12 }}>Last 30 days · 1,847 models</div>
        </div>
        <div style={{ position: 'relative', width: 80, height: 80, flexShrink: 0 }}>
          <PieChart width={80} height={80}>
            <Pie data={PASS_FAIL_DATA} cx={35} cy={35} innerRadius={25} outerRadius={37} startAngle={90} endAngle={-270} dataKey="value" strokeWidth={0}>
              <Cell fill="#4d9aff" />
              <Cell fill="#ff6060" />
            </Pie>
          </PieChart>
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, color: '#4d9aff' }}>84%</div>
        </div>
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#4d9aff' }} />
            <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.7)' }}>Passed — 1,551 models</span>
          </div>
          <div className="flex items-center gap-2">
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#ff6060' }} />
            <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.7)' }}>Failed — 296 models</span>
          </div>
        </div>
      </div>

    </div>
  )
}

// ── Projects ──────────────────────────────────────────────────────────────────

const FAKE_PROJECTS = [
  { name: 'turbine_blade_v3', meta: 'Today, 11:44 AM · IN-718 Nickel alloy', status: 'Processing…', statusColor: '#f59e0b' },
  { name: 'servo_mount_mk2',  meta: 'Yesterday · AL-6061',                   status: 'Pending',      statusColor: 'rgba(255,255,255,0.2)' },
  { name: 'heat_sink_array',  meta: 'Jun 10 · CU-101 Copper',                status: 'Pending',      statusColor: 'rgba(255,255,255,0.2)' },
  { name: 'gearbox_housing',  meta: 'Jun 8 · ST-52 Steel',                   status: 'Pending',      statusColor: 'rgba(255,255,255,0.2)' },
]

function Projects({ onNewAnalysis }: { onNewAnalysis: () => void }) {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-end justify-between">
        <div>
          <h2 style={{ fontSize: 20, fontWeight: 600, color: 'white' }}>Projects</h2>
          <p style={{ fontSize: 13, marginTop: 4, color: 'rgba(255,255,255,0.4)' }}>5 total · 1 active · 1 error open</p>
        </div>
        <Button onClick={onNewAnalysis}>✦ New Analysis</Button>
      </div>

      <a href="/result/demo" style={{ textDecoration: 'none' }}>
        <div className="flex items-center gap-5 px-6 py-5 rounded-2xl transition-all hover:brightness-110"
          style={{ background: 'rgba(77,154,255,0.1)', border: '1px solid rgba(77,154,255,0.2)', backdropFilter: 'blur(20px)' }}>
          <div className="w-10 h-10 rounded-xl flex items-center justify-center text-base flex-shrink-0" style={{ background: 'rgba(77,154,255,0.15)' }}>📐</div>
          <div className="flex-1 min-w-0">
            <div style={{ fontSize: 15, fontWeight: 600, color: 'white' }}>BRACKET-XY-300</div>
            <div style={{ fontSize: 12, marginTop: 2, color: 'rgba(255,255,255,0.4)' }}>Today, 2:52 PM · AL-6061 · 50 × 30 × 5 mm</div>
          </div>
          <div className="flex items-center gap-3 flex-shrink-0">
            <span style={{ fontSize: 12, padding: '3px 10px', borderRadius: 100, background: 'rgba(255,96,96,0.15)', color: '#ff6060' }}>1 error</span>
            <span style={{ fontSize: 13, color: '#4d9aff' }}>View →</span>
          </div>
        </div>
      </a>

      <div style={{ ...glass, overflow: 'hidden' }}>
        {FAKE_PROJECTS.map((p, i) => (
          <div key={p.name} className="flex items-center gap-5 px-6 py-4" style={{ borderTop: '1px solid rgba(255,255,255,0.06)', opacity: 0.45 }}>
            <div className="w-9 h-9 rounded-xl flex items-center justify-center text-base flex-shrink-0" style={{ background: 'rgba(255,255,255,0.05)' }}>⏳</div>
            <div className="flex-1 min-w-0">
              <div style={{ fontSize: 13, fontWeight: 500, color: 'white' }}>{p.name}</div>
              <div style={{ fontSize: 11, marginTop: 2, color: 'rgba(255,255,255,0.35)' }}>{p.meta}</div>
            </div>
            <span style={{ fontSize: 12, flexShrink: 0, color: p.statusColor }}>{p.status}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Plans ─────────────────────────────────────────────────────────────────────

const PLANS = [
  {
    name: 'Starter',
    price: '€49', sub: 'per month',
    features: ['50 models / month', 'Drawing-to-CAD', 'STEP export', 'Email support'],
    active: false,
  },
  {
    name: 'Pro',
    price: '€299', sub: 'per month',
    features: ['500 models / month', 'Drawing-to-CAD', 'Text-to-CAD', 'API access (10k calls)', 'Manufacturing validation', 'Priority support'],
    active: false,
  },
  {
    name: 'Enterprise',
    price: 'Custom', sub: 'contact us',
    features: ['Unlimited models', 'Drawing-to-CAD', 'Text-to-CAD', 'Unlimited API', 'Manufacturing validation', 'Team management', 'Dedicated support', 'SLA 99.9%'],
    active: true,
  },
]

function Plans() {
  return (
    <div className="flex flex-col gap-8">
      <div>
        <h2 style={{ fontSize: 20, fontWeight: 600, color: 'white' }}>Plans</h2>
        <p style={{ fontSize: 13, marginTop: 4, color: 'rgba(255,255,255,0.4)' }}>
          Kyrall · AI-powered CAD · From idea to manufacturable model in seconds
        </p>
      </div>
      <div className="grid gap-4 lg:grid-cols-3">
        {PLANS.map(plan => (
          <div key={plan.name} className="rounded-2xl p-6 flex flex-col gap-5"
            style={plan.active ? {
              background: 'rgba(10, 8, 30, 0.65)',
              backdropFilter: 'blur(24px)',
              WebkitBackdropFilter: 'blur(24px)',
              border: '1px solid rgba(77,154,255,0.25)',
              borderRadius: 20,
              boxShadow: '0 0 40px rgba(62,50,129,0.4)',
            } : {
              ...glass,
            }}
          >
            <div className="flex items-start justify-between">
              <div>
                <div style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8, color: plan.active ? '#4d9aff' : 'rgba(255,255,255,0.4)' }}>{plan.name}</div>
                <div style={{ fontSize: 26, fontWeight: 700, color: 'white', lineHeight: 1 }}>{plan.price}</div>
                <div style={{ fontSize: 12, marginTop: 4, color: 'rgba(255,255,255,0.4)' }}>{plan.sub}</div>
              </div>
              {plan.active && (
                <span style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', padding: '3px 8px', borderRadius: 100, background: 'rgba(77,154,255,0.15)', color: '#4d9aff' }}>
                  Active
                </span>
              )}
            </div>
            <ul className="flex flex-col gap-2 flex-1">
              {plan.features.map(f => (
                <li key={f} className="flex items-baseline gap-2" style={{ fontSize: 13, color: plan.active ? 'rgba(255,255,255,0.75)' : 'rgba(255,255,255,0.35)' }}>
                  <span style={{ fontSize: 11, flexShrink: 0, color: plan.active ? '#4d9aff' : 'rgba(255,255,255,0.15)' }}>✓</span>
                  {f}
                </li>
              ))}
            </ul>
            <button disabled className="w-full py-2.5 rounded-full text-sm font-medium mt-auto"
              style={{ background: 'rgba(255,255,255,0.06)', color: plan.active ? 'rgba(255,255,255,0.4)' : 'rgba(255,255,255,0.15)', border: '1px solid rgba(255,255,255,0.08)', cursor: 'default' }}>
              {plan.active ? 'Current plan' : 'Downgrade'}
            </button>
          </div>
        ))}
      </div>
      <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.3)' }}>
        Member of Bavaria Makes e.V. · Bayern Innovativ · Bavarian Ministry of Economic Affairs
      </p>
    </div>
  )
}

// ── API Access ────────────────────────────────────────────────────────────────

const FAKE_KEY = 'ky_live_sk_eM9x2Rtz8wKLpNvYQf7JbA3dCuXiOhGs'

function ApiAccess() {
  const [copied, setCopied] = useState(false)
  const [revealed, setRevealed] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(FAKE_KEY)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="flex flex-col gap-8 max-w-2xl">
      <div>
        <h2 style={{ fontSize: 20, fontWeight: 600, color: 'white' }}>API Access</h2>
        <p style={{ fontSize: 13, marginTop: 4, color: 'rgba(255,255,255,0.4)' }}>Enterprise · unlimited calls</p>
      </div>

      <div className="flex flex-col gap-2">
        <label style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'rgba(255,255,255,0.4)' }}>API Key</label>
        <div className="flex items-center gap-2">
          <code className="flex-1 px-4 py-3 rounded-xl text-sm font-mono"
            style={{ ...glassSubtle, color: 'rgba(255,255,255,0.75)' }}>
            {revealed ? FAKE_KEY : FAKE_KEY.slice(0, 12) + '•'.repeat(26)}
          </code>
          <button onClick={() => setRevealed(r => !r)} className="px-3 py-3 text-xs rounded-xl whitespace-nowrap"
            style={{ ...glassSubtle, color: 'rgba(255,255,255,0.5)' }}>
            {revealed ? 'Hide' : 'Reveal'}
          </button>
          <button onClick={handleCopy} className="px-3 py-3 text-xs rounded-xl font-medium whitespace-nowrap transition-colors"
            style={{ ...glassSubtle, color: copied ? '#4d9aff' : 'rgba(255,255,255,0.5)' }}>
            {copied ? '✓ Copied' : 'Copy'}
          </button>
        </div>
      </div>

      <div className="flex flex-col gap-3">
        <div style={{ ...glass, padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div className="flex justify-between items-baseline">
            <span style={{ color: 'white', fontWeight: 500 }}>Monthly usage</span>
            <span className="text-sm tabular-nums" style={{ color: 'rgba(255,255,255,0.4)' }}>94,231 <span style={{ opacity: 0.4 }}>/ 100,000</span></span>
          </div>
          <div className="h-1.5 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.08)' }}>
            <div className="h-full rounded-full" style={{ width: '94.2%', background: 'linear-gradient(90deg, #3e3281, #4d9aff)' }} />
          </div>
          <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.35)' }}>Resets in 17 days</p>
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <label style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.1em', color: 'rgba(255,255,255,0.4)' }}>Example request</label>
        <pre className="text-xs p-5 rounded-xl overflow-x-auto"
          style={{ ...glassSubtle, color: '#7dd3fc', lineHeight: 1.8 }}
        >{`curl -X POST https://api.kyrall.com/v1/reconstruct \\
  -H "Authorization: Bearer ${FAKE_KEY.slice(0, 18)}..." \\
  -F "file=@drawing.png" \\
  -F "output_format=step"`}</pre>
      </div>
    </div>
  )
}

// ── Settings ──────────────────────────────────────────────────────────────────

const PROFILE_FIELDS = [
  { label: 'Name',         value: 'Elon Musk' },
  { label: 'Email',        value: 'elon@x.com' },
  { label: 'Organization', value: 'X Corp · SpaceX · Tesla · Boring Company' },
  { label: 'Plan',         value: 'Enterprise' },
  { label: 'Member since', value: 'March 14, 2025' },
]

function Settings() {
  return (
    <div className="flex flex-col gap-10 max-w-lg">
      <div>
        <h2 style={{ fontSize: 20, fontWeight: 600, color: 'white' }}>Settings</h2>
        <p style={{ fontSize: 13, marginTop: 4, color: 'rgba(255,255,255,0.4)' }}>Profile & account</p>
      </div>
      <div style={{ ...glass, padding: '24px', display: 'flex', flexDirection: 'column', gap: 20 }}>
        {PROFILE_FIELDS.map(f => (
          <div key={f.label}>
            <label style={{ display: 'block', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 8, color: 'rgba(255,255,255,0.4)' }}>
              {f.label}
            </label>
            <input readOnly value={f.value} className="w-full px-4 py-3 rounded-xl text-sm text-white"
              style={{ ...glassSubtle }} />
          </div>
        ))}
        <button disabled className="self-start px-6 py-2.5 rounded-full text-sm font-medium mt-2"
          style={{ background: 'rgba(255,255,255,0.06)', color: 'rgba(255,255,255,0.25)', border: '1px solid rgba(255,255,255,0.08)', cursor: 'default' }}>
          Save changes
        </button>
      </div>
      <div className="flex flex-col gap-3 pt-6" style={{ borderTop: '1px solid rgba(255,60,60,0.15)' }}>
        <p style={{ fontSize: 13, fontWeight: 500, color: '#ff6060' }}>Danger Zone</p>
        <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.4)' }}>Permanently delete your account and all associated data.</p>
        <button disabled className="self-start px-5 py-2 rounded-full text-sm"
          style={{ background: 'transparent', color: 'rgba(255,96,96,0.35)', border: '1px solid rgba(255,60,60,0.2)', cursor: 'not-allowed' }}>
          Delete account
        </button>
      </div>
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<Tab>('Overview')
  const [modalOpen, setModalOpen] = useState(false)

  return (
    <>
      <NewAnalysisModal open={modalOpen} onClose={() => setModalOpen(false)} />

      {/* Full-viewport purple background with perspective grid */}
      <div style={{ position: 'relative', minHeight: '100vh', background: '#3e3281', overflow: 'hidden' }}>
        <PerspectiveGrid clipFraction={0.35} />

        {/* Content sits on top of the grid */}
        <div style={{ position: 'relative', zIndex: 10, padding: '40px 24px', maxWidth: 1000, margin: '0 auto' }}>

          {/* User header */}
          <div className="flex items-center gap-4 mb-10">
            <div className="w-14 h-14 rounded-full flex items-center justify-center text-lg font-bold text-white flex-shrink-0"
              style={{ background: 'linear-gradient(135deg, #5a4db0 0%, #3e3281 100%)', border: '2px solid rgba(255,255,255,0.2)' }}>
              EM
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2.5">
                <h1 style={{ fontSize: 20, fontWeight: 600, color: 'white' }}>Welcome back, Elon Musky 🤍</h1>
                <span style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', padding: '3px 8px', borderRadius: 100, background: 'rgba(245,158,11,0.15)', color: '#f59e0b', border: '1px solid rgba(245,158,11,0.25)' }}>
                  Enterprise
                </span>
              </div>
              <p style={{ fontSize: 13, marginTop: 2, color: 'rgba(255,255,255,0.5)' }}>elon@x.com · Munich</p>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-6 mb-8" style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
            {TABS.map(tab => (
              <button key={tab} onClick={() => setActiveTab(tab)}
                style={{
                  fontSize: 14, fontWeight: 500, paddingBottom: 12, marginBottom: -1,
                  color: activeTab === tab ? 'white' : 'rgba(255,255,255,0.45)',
                  background: 'none', border: 'none',
                  borderBottom: activeTab === tab ? '2px solid #4d9aff' : '2px solid transparent',
                  cursor: 'pointer',
                }}
              >
                {tab}
              </button>
            ))}
          </div>

          {activeTab === 'Overview'   && <Overview onNewAnalysis={() => setModalOpen(true)} />}
          {activeTab === 'Projects'   && <Projects onNewAnalysis={() => setModalOpen(true)} />}
          {activeTab === 'Plans'      && <Plans />}
          {activeTab === 'API Access' && <ApiAccess />}
          {activeTab === 'Settings'   && <Settings />}
        </div>
      </div>
    </>
  )
}
