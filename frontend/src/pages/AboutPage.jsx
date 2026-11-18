import { Link } from "react-router-dom";
import { Target, ShieldCheck, Eye, HeartHandshake, Video, ScanLine, ClipboardList, Dumbbell, Building2, Globe, MapPin, ArrowRight } from "lucide-react";
import { Tilt } from "@/components/Fx3D";

const FOUNDERS = [
  ["Adithya AG", "Co-founder", "AA", "Drives the product vision and the cricket side of CricAnalyze, turning coaching know-how into measurements players can act on.", "from-[#00B4D8] to-[#10B981]"],
  ["Chandru H", "Co-founder", "CH", "Leads the technology behind CricAnalyze: the body-tracking pipeline, AI coaching engine and the platform that keeps every report fast and private.", "from-[#10B981] to-amber-400"],
];
const VALUES = [
  [Eye, "Honest evidence", "Every number comes from a real video frame. If the camera can't see it clearly, we say so instead of guessing."],
  [Target, "Practical coaching", "Each report ends with drills and a weekly plan, not just charts."],
  [ShieldCheck, "Private by default", "Your videos are stored privately and shared only when you choose."],
  [HeartHandshake, "Built with coaches", "Academies and coaches work alongside the AI, so players get a human view too."],
];
const STEPS = [[Video, "Film", "Record a batting or bowling clip on any phone."], [ScanLine, "Track", "Our AI tracks 17 body joints across every key frame."],
  [ClipboardList, "Measure", "Knee angles, head position, weight transfer and more, all explained in plain words."], [Dumbbell, "Improve", "Get personalised drills, a weekly plan and track progress clip after clip."]];

const Block = ({ eyebrow, title, children }) => (
  <section data-s3d className="sec-3d max-w-7xl mx-auto px-4 sm:px-6 py-14 md:py-20">
    <div className="eyebrow mb-2">{eyebrow}</div><h2 className="font-display text-2xl sm:text-3xl font-bold mb-8 max-w-2xl">{title}</h2>{children}
  </section>
);

const Founder = ([name, role, ini, bio, g], i) => (
  <Tilt key={name} max={8} className="glass rounded-3xl p-7 reveal-3d h-full" style={{ transitionDelay: `${i * 120}ms` }} data-testid={`founder-${i}`}>
    <div className={`w-20 h-20 rounded-2xl bg-gradient-to-br ${g} grid place-items-center font-display font-extrabold text-2xl text-[#04130d] mb-5 depth-pop`}>{ini}</div>
    <h3 className="font-display text-xl font-bold">{name}</h3><div className="text-sm text-[#10B981] mb-3">{role}, CricAnalyze</div><p className="text-slate-300 text-sm leading-relaxed">{bio}</p>
  </Tilt>
);

export default function AboutPage() {
  return (<div data-testid="about-page">
    <section className="max-w-7xl mx-auto px-4 sm:px-6 pt-16 md:pt-24 pb-10 grid lg:grid-cols-2 gap-12 items-center">
      <div className="reveal-3d"><div className="eyebrow mb-3">About CricAnalyze</div>
        <h1 className="font-display text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-tight mb-6">Making good coaching feedback available to every cricketer</h1>
        <p className="text-slate-300 text-base md:text-lg leading-relaxed mb-4">CricAnalyze is a product of <a href="https://biatpl.com" target="_blank" rel="noopener noreferrer" className="text-[#10B981] hover:underline" data-testid="about-company-link"><b>Buddy Innovations and Technologies Private Limited</b></a>. We help batters and bowlers understand their technique from a simple phone video, using AI body tracking and coaching that is clear about what it can and can't see.</p>
        <p className="text-slate-400 leading-relaxed">Most young players only get expert technique feedback now and then. We want every net session to count, whether you train at a top academy or in your backyard.</p></div>
      <div className="relative reveal-3d"><img src="/images/nets.jpg" alt="Cricket practice nets" className="rounded-3xl h-80 md:h-[420px] w-full object-cover" />
        <div className="absolute -bottom-6 left-6 right-6 glass rounded-2xl p-5 grid grid-cols-3 gap-3 text-center"><div><div className="font-display text-2xl font-bold text-[#10B981]">17</div><div className="text-xs text-slate-400">joints tracked</div></div>
          <div><div className="font-display text-2xl font-bold text-[#5fd7ef]">2</div><div className="text-xs text-slate-400">disciplines</div></div><div><div className="font-display text-2xl font-bold text-amber-300">1</div><div className="text-xs text-slate-400">phone needed</div></div></div></div>
    </section>

    <Block eyebrow="Our founders" title="The people building CricAnalyze">
      <div className="grid md:grid-cols-2 gap-6">{FOUNDERS.map(Founder)}</div>
    </Block>

    <Block eyebrow="What we believe" title="Four promises behind every report">
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">{VALUES.map(([I, t, d], i) => <Tilt key={t} max={10} className="glass rounded-2xl p-6 reveal-3d h-full" style={{ transitionDelay: `${i * 80}ms` }}>
        <I className="text-[#10B981] mb-4" size={26} /><h3 className="font-semibold mb-2">{t}</h3><p className="text-sm text-slate-400">{d}</p></Tilt>)}</div>
    </Block>

    <Block eyebrow="How it works" title="From a phone clip to a coaching plan">
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">{STEPS.map(([I, t, d], i) => <div key={t} className="relative rounded-2xl border border-white/10 p-6 reveal-3d" style={{ transitionDelay: `${i * 80}ms` }}>
        <div className="font-mono text-xs text-[#5fd7ef] mb-3">STEP {i + 1}</div><I className="mb-3 text-white" size={24} /><h3 className="font-semibold mb-1">{t}</h3><p className="text-sm text-slate-400">{d}</p></div>)}</div>
    </Block>

    <Block eyebrow="The company" title="Buddy Innovations and Technologies Private Limited">
      <div className="grid md:grid-cols-3 gap-4" data-testid="company-info">
        {[[Building2, "Company", "Buddy Innovations and Technologies Private Limited", "https://biatpl.com"], [Globe, "Company website", "biatpl.com", "https://biatpl.com"], [MapPin, "Based in", "India"]].map(([I, l, v, href]) =>
          <div key={l} className="glass rounded-2xl p-6 flex gap-4 items-start reveal-3d"><I className="text-[#10B981] shrink-0" size={22} /><div><div className="text-xs text-slate-400 mb-1">{l}</div>
            {href ? <a href={href} target="_blank" rel="noopener noreferrer" className="font-semibold hover:text-[#10B981] transition-colors" data-testid={`company-link-${l.replace(/ /g, "-").toLowerCase()}`}>{v}</a> : <div className="font-semibold">{v}</div>}</div></div>)}
      </div>
      <p className="text-slate-400 text-sm mt-6 max-w-3xl">We don't publish fake testimonials or invented statistics, and we never present AI output as an official selection credential. CricAnalyze is a training aid, not a medical assessment.</p>
    </Block>

    <section className="max-w-7xl mx-auto px-4 sm:px-6 pb-20"><div className="rounded-3xl border border-[#10B981]/30 bg-gradient-to-br from-[#10B981]/15 to-[#00B4D8]/10 p-8 md:p-12 flex flex-col md:flex-row gap-6 md:items-center justify-between reveal-3d">
      <div><h2 className="font-display text-2xl sm:text-3xl font-bold mb-2">Ready to see your technique clearly?</h2><p className="text-slate-300">Upload your first clip and get a full report in minutes.</p></div>
      <div className="flex gap-3"><Link to="/signup" className="btn-3d inline-flex items-center gap-2 bg-[#10B981] text-[#04130d] font-semibold rounded-full px-6 py-3" data-testid="about-cta-signup">Get started <ArrowRight size={16} /></Link>
        <Link to="/contact" className="inline-flex items-center rounded-full px-6 py-3 border border-white/20 hover:border-white/40" data-testid="about-cta-contact">Contact us</Link></div>
    </div></section>
  </div>);
}
