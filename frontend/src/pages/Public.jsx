import { useEffect, useState } from "react";
import AboutPage from "@/pages/AboutPage";
import { Link, useParams } from "react-router-dom";
import { toast } from "sonner";
import { ArrowRight, Video, Brain, FileText, LineChart, Users, ShieldCheck, Target, Layers, CheckCircle2 } from "lucide-react";
import { LEGAL, LEGAL_UPDATED, COMPANY } from "@/constants/legal";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { api, errMsg, inr, SITE } from "@/lib/api";
import { Seo, Card, Badge } from "@/components/Common";
import { Tilt, HeroBatter } from "@/components/Fx3D";
import { SampleReport, Measures, FilmingGuide, AcademySection, Journey, Marquee3D, ExplodedReport } from "@/pages/HomeSections";
import { useAuth } from "@/context/AuthContext";
import { PostCard } from "@/pages/Blog";

const ORG = { "@context": "https://schema.org", "@type": "Organization", name: "CricAnalyze", legalName: "Buddy Innovations and Technologies Private Limited", url: SITE, email: "noreply@cricanalyze.in" };
const WEBSITE = { "@context": "https://schema.org", "@type": "WebSite", name: "CricAnalyze", url: SITE };
const Section = ({ children, className = "" }) => <section data-s3d className={`sec-3d max-w-7xl mx-auto px-4 sm:px-6 py-16 md:py-24 ${className}`}>{children}</section>;
const H2 = ({ eyebrow, title, desc, h1 }) => { const H = h1 ? "h1" : "h2"; return (<div className="mb-12 max-w-2xl"><div className="eyebrow mb-3">{eyebrow}</div><H className="text-3xl sm:text-4xl font-bold">{title}</H>{desc && <p className="text-slate-400 mt-3">{desc}</p>}</div>); };

const FEATURES = [
  [Video, "Batting analysis", "Stance, head position, trigger, footwork, weight transfer, bat path and follow-through — assessed from frames of your video."],
  [Target, "Bowling analysis", "Run-up rhythm, gather, front-arm action, alignment, release and follow-through, with up to three camera angles on eligible plans."],
  [Brain, "Honest AI observations", "Every observation is tagged observed or inferred with a confidence level. Areas the camera can't show are marked not assessable."],
  [FileText, "Structured reports & PDF", "Strengths, areas to improve, timestamped evidence frames, linked drills and a weekly practice plan."],
  [LineChart, "Progress timeline", "Compare reports of the same type over time. Missing values stay missing — never shown as zero."],
  [Users, "Academy workspace", "Invite coaches and players, assign coaches, track attendance and share reports only with player consent."],
];

const WHO = [["Players", "Specific, evidence-linked feedback and a plan for your next sessions.", ["Technique score /100", "Weight transfer & head position", "Drills + weekly plan", "Join your academy with a code"]],
  ["Parents", "Support young players with guardian consent and privacy built in.", ["Guardian consent for under-18s", "Private video storage", "Reports emailed to you", "Delete data anytime"]],
  ["Coaches", "Review your players' shared reports and add your own feedback.", ["Start right after sign-up", "Reports players share with you", "Leaderboards with nicknames", "Attendance & feedback"]],
  ["Academies", "Manage batches, coaches and progress in one private workspace.", ["Unique academy join code", "Approve join requests", "Referral commission", "Coach & Academy plans"]]];

export const Home = () => {
  const [posts, setPosts] = useState([]);
  useEffect(() => { api.get("/blog/posts", { params: { limit: 3 } }).then(({ data }) => setPosts(data.posts)).catch(() => {}); }, []);
  return (
    <>
      <Seo title="CricAnalyze — AI Cricket Batting & Bowling Video Analysis" path="/" description="Upload a batting or bowling video and get an AI-assisted technique report with evidence frames, drills and a practice plan." jsonLd={[ORG, WEBSITE]} />
      <section className="relative overflow-hidden" data-testid="hero-3d">
        <div className="floor-grid" aria-hidden="true" />
        <div className="glow-orb w-96 h-96 bg-[#00B4D8] -top-20 right-10" aria-hidden="true" />
        <div className="glow-orb w-80 h-80 bg-[#10B981] bottom-0 left-0" style={{ animationDelay: "-6s" }} aria-hidden="true" />
        <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 pt-16 pb-20 md:pt-24 grid lg:grid-cols-12 gap-12 items-center w-full">
          <div className="lg:col-span-6 fade-up">
            <div className="eyebrow mb-5">AI cricket video analysis</div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold leading-[1.05]" data-testid="hero-title"><span className="flip-word " style={{ animationDelay: "0.00s" }}>See</span> <span className="flip-word " style={{ animationDelay: "0.08s" }}>your</span> <span className="flip-word " style={{ animationDelay: "0.16s" }}>technique</span> <span className="flip-word text-[#10B981]" style={{ animationDelay: "0.24s" }}>frame</span> <span className="flip-word text-[#10B981]" style={{ animationDelay: "0.32s" }}>by</span> <span className="flip-word text-[#10B981]" style={{ animationDelay: "0.40s" }}>frame.</span></h1>
            <p className="text-slate-300 mt-6 text-base sm:text-lg max-w-xl leading-relaxed">Upload a short batting or bowling clip. CricAnalyze reviews key frames, explains what it can see, flags what it can't, and turns it into drills you can practise this week.</p>
            <div className="flex flex-wrap gap-3 mt-8">
              <Button size="lg" asChild className="btn-3d bg-[#10B981] hover:bg-[#059669] text-[#0B132B] rounded-full px-7" data-testid="hero-cta-btn"><Link to="/app/upload">Analyse a video <ArrowRight className="ml-1" size={18} /></Link></Button>
              <Button size="lg" variant="outline" asChild className="rounded-full px-7 border-white/20 bg-transparent" data-testid="hero-how-btn"><Link to="/how-it-works">How it works</Link></Button>
            </div>
            <p className="text-xs text-slate-500 mt-5">For players, parents, coaches and academies. Guardian consent required for players under 18.</p>
          </div>
          <div className="lg:col-span-6 relative fade-up" style={{ animationDelay: ".15s" }}><HeroBatter /></div>
        </div>
      </section>
      <Marquee3D />
      <Journey />
      <ExplodedReport />
      <SampleReport />
      <Measures />
      <Section><H2 eyebrow="What it analyses" title="Batting and bowling, explained clearly" desc="Built around what a single phone camera can reliably show." />
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5 s3d-tilt" data-s3d>{FEATURES.map(([I, t, d], i) => <Tilt key={t} className="glass rounded-xl p-5 reveal-3d hover:border-[#00B4D8]/40" style={{ transitionDelay: `${i * 60}ms` }} data-testid={`feature-card-${i}`}><I className="text-[#00B4D8] mb-4 depth-pop" /><h3 className="font-semibold text-lg mb-2 depth-pop">{t}</h3><p className="text-sm text-slate-400 leading-relaxed">{d}</p></Tilt>)}</div>
      </Section>
      <Section className="!pt-0"><H2 eyebrow="Who it's for" title="One platform, four kinds of cricketers" />
        <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-4 s3d-tilt" data-s3d>{WHO.map(([t, d, back], i) => <div key={t} tabIndex={0} onClick={(e) => e.currentTarget.classList.toggle("flipped")} className="flip-card h-56 reveal-3d cursor-pointer" style={{ transitionDelay: `${i * 80}ms` }} data-testid={`who-card-${i}`}>
          <div className="flip-inner"><div className="flip-face glass p-7 flex flex-col justify-between"><h3 className="font-display font-bold text-2xl">{t}</h3><p className="text-sm text-slate-400">{d}</p><span className="text-[11px] text-[#00B4D8]">Hover or tap to flip ↻</span></div>
            <div className="flip-face flip-back p-7 bg-gradient-to-br from-[#10B981]/25 to-[#00B4D8]/15 border border-[#10B981]/40 flex flex-col justify-center"><ul className="space-y-2 text-sm">{back.map((x) => <li key={x} className="flex gap-2"><CheckCircle2 size={15} className="text-[#10B981] shrink-0 mt-0.5" />{x}</li>)}</ul></div></div></div>)}</div>
      </Section>
      <FilmingGuide />
      <AcademySection />
      <Section className="!pt-0"><H2 eyebrow="Pricing" title="Choose the analysis you need" desc="Prices are set by CricAnalyze and may change; the checkout shows the final amount." /><PlanGrid /></Section>
      {posts.length > 0 && <Section className="!pt-0"><div className="flex justify-between items-end"><H2 eyebrow="From the blog" title="Latest articles" /><Link to="/blog" className="text-[#00B4D8] text-sm mb-12">All articles →</Link></div>
        <div className="grid md:grid-cols-3 gap-5">{posts.map((p) => <PostCard key={p.id} p={p} />)}</div></Section>}
      <Section className="!pt-0"><H2 eyebrow="FAQ" title="Common questions" /><FaqList limit={5} /></Section>
    </>
  );
};

export const ExampleReport = ({ className = "" }) => (
  <div className={`glass rounded-xl p-4 shadow-2xl ${className}`} data-testid="example-report-preview">
    <div className="flex justify-between items-center mb-3"><Badge tone="amber">EXAMPLE REPORT</Badge><span className="font-mono text-[10px] text-slate-400">BATTING · SIDE-ON</span></div>
    {[["Head position", 4, "high"], ["Front-foot stride", 3, "medium"], ["Bat path", null, "low"]].map(([a, r, c]) => (
      <div key={a} className="mb-2"><div className="flex justify-between text-xs"><span>{a}</span><span className="text-slate-400">{r ? `${r}/5 · ${c}` : "Not assessable"}</span></div>
        <div className="h-1.5 bg-white/10 rounded mt-1"><div className="h-full rounded bg-[#10B981]" style={{ width: r ? `${r * 20}%` : 0 }} /></div></div>))}
    <p className="text-[11px] text-slate-400 mt-3">Illustrative sample only — not a real player's result.</p>
  </div>
);

const PRODUCTS = [["batting", "Batting"], ["bowling", "Bowling"], ["combined", "Batting + Bowling"], ["academy", "Coach & Academy"]];

export const PlanGrid = ({ onSelect }) => {
  const [plans, setPlans] = useState([]);
  const { user } = useAuth();
  const coach = ["coach", "academy_admin"].includes(user?.role);
  const [prod, setProd] = useState(coach ? "academy" : "batting");
  useEffect(() => { api.get("/plans").then(({ data }) => setPlans(data)).catch(() => {}); }, []);
  const shown = plans.filter((p) => (p.product || "batting") === prod);
  return (
    <div data-testid="plan-grid">
      <div className="flex flex-wrap gap-2 mb-6" role="tablist">{PRODUCTS.map(([v, l]) => <button key={v} onClick={() => setProd(v)} role="tab" aria-selected={prod === v} data-testid={`plan-tab-${v}`}
        className={`px-4 py-2 rounded-full text-sm border transition-colors ${prod === v ? "border-[#10B981] bg-[#10B981]/10 text-white" : "border-white/10 text-slate-300 hover:border-white/30"}`}>{l}</button>)}</div>
      <div className="grid md:grid-cols-3 gap-5">
      {shown.map((p, i) => (
        <Tilt key={p.id} max={6} style={{ transitionDelay: `${i * 120}ms` }} className={`plan-pop rounded-2xl p-7 border backdrop-blur-xl ${i === 1 ? "border-[#10B981]/50 bg-[#10B981]/10" : "border-white/10 bg-[#0B132B]/80"}`} data-testid={`plan-card-${p.slug}`}>
          <div className="eyebrow">{p.tier || p.billing}</div>
          <h3 className="text-2xl font-bold mt-2">{p.name}</h3>
          <div className="text-4xl font-display font-extrabold mt-4">{inr(p.price_inr)}<span className="text-sm text-slate-400 font-normal"> / {p.period_days} days</span></div>
          <p className="text-sm text-slate-400 mt-2 min-h-[40px]">{p.description}</p>
          <ul className="mt-5 space-y-2 text-sm">
            {[`${p.credits} analysis credits`, `${p.analysis_types.join(" + ")} analysis`, `${p.videos_per_analysis} ${p.videos_per_analysis === 1 ? "video" : "videos"} per analysis, any length`, `${p.report_level} report`,
              p.academy_features && "Academy workspace, join codes & leaderboard", p.multi_angle && "Multi-angle input", p.pdf_export && "PDF export + emailed reports", p.comparisons && "Before/after comparisons", p.ai_coach && "AI coach", p.training_planner && "Training planner"].filter(Boolean)
              .map((x) => <li key={x} className="flex gap-2"><CheckCircle2 size={16} className="text-[#10B981] shrink-0 mt-0.5" /><span className="capitalize-first">{x}</span></li>)}
          </ul>
          {onSelect ? <Button className="w-full mt-7 rounded-full" variant={i === 1 ? "default" : "secondary"} onClick={() => onSelect(p.id)} data-testid={`select-plan-${p.slug}`}>Choose {p.name}</Button> :
            <Button asChild className="w-full mt-7 rounded-full" variant={i === 1 ? "default" : "secondary"} data-testid={`plan-buy-${p.slug}`}><Link to={user ? `/app/billing?plan=${p.id}` : `/signup`}>Choose {p.name}</Link></Button>}
        </Tilt>))}
      {!shown.length && <p className="text-sm text-slate-500">No plans in this group yet.</p>}
      </div>
    </div>
  );
};

export const Features = () => (<><Seo title="Features" path="/features" description="Batting and bowling analysis, evidence frames, drills, AI coach, training planner, academy tools and more." />
  <Section><H2 h1 eyebrow="Features" title="Everything in CricAnalyze" />
    <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">{[...FEATURES, [MessageIcon, "AI Coach & Ask CricAnalyze", "Ask questions about your own reports. Answers cite report evidence and say so when data is missing."],
      [Layers, "Multi-angle input", "Label side-on, front-on and behind angles. Each angle gets its own visibility check; no 3D reconstruction is claimed."],
      [ShieldCheck, "Privacy first", "Private video storage, expiring links, guardian consent for minors, data export and account deletion."]].map(([I, t, d]) => <Tilt key={t} className="glass rounded-xl p-5 reveal-3d"><I className="text-[#10B981] mb-4 depth-pop" /><h3 className="font-semibold text-lg mb-2">{t}</h3><p className="text-sm text-slate-400">{d}</p></Tilt>)}</div>
  </Section><Measures /><AcademySection /></>);
function MessageIcon(p) { return <Brain {...p} />; }

export const HowItWorks = () => (<><Seo title="How it works" path="/how-it-works" description="Record, upload, get an AI-assisted report and practise with linked drills." />
  <Section><H2 h1 eyebrow="How it works" title="From clip to practice plan in four steps" />
    <ol className="grid md:grid-cols-4 gap-5">{[["Record", "Film side-on or front-on, in good light, whole body in frame, 30fps or higher. Any length works — we find the main shot or delivery."], ["Upload", "Choose batting or bowling, label the camera angle and confirm consent. We check the file is a real, readable video."],
      ["Analyse", "We sample frames and an AI vision model describes what it can see, with timestamps and confidence. Usually takes 1–3 minutes."], ["Practise", "Follow the linked drills, generate a training plan, and compare your next video with this one."]]
      .map(([t, d], i) => <li key={t} className="glass rounded-xl p-6 reveal-3d"><div className="font-mono text-[#00B4D8] text-sm">0{i + 1}</div><h3 className="text-xl font-bold mt-2 mb-2">{t}</h3><p className="text-sm text-slate-400">{d}</p></li>)}</ol>
    <Card className="mt-10"><h3 className="font-semibold mb-2">What the AI can and can't do</h3><p className="text-sm text-slate-400 leading-relaxed">Body tracking measures 2D joint angles, weight transfer, head position and foot landings on the exact frames shown in your report, and an AI vision model adds coaching notes. It does not measure bat speed, ball speed or forces, and it is not calibrated 3D biomechanics. Anything the camera can't see clearly is marked unavailable. It is not medical advice.</p></Card>
  </Section><FilmingGuide /><SampleReport /></>);

export const Pricing = () => (<><Seo title="Pricing" path="/pricing" description="Batting, bowling and all-rounder plans with analysis credits. Pay securely with Razorpay." />
  <Section><H2 h1 eyebrow="Pricing" title="Simple plans, clear limits" desc="Credits are reserved when an analysis starts and refunded automatically if processing fails." /><PlanGrid /></Section></>);

export const About = () => (<><Seo title="About" path="/about" description="CricAnalyze is built by Buddy Innovations and Technologies Private Limited, founded by Adithya AG and Chandru H." /><AboutPage /></>);

const FAQS = [["What videos work best?", "Clips of any length filmed side-on or front-on, whole body visible, steady camera, good light, 480p or higher. For long clips we find the main shot or delivery and analyse it frame by frame. MP4, MOV and WEBM are supported."],
  ["Is the analysis done by a real AI model?", "Yes. Frames from your video are analysed by a hosted AI vision model. If the AI service is unavailable the job fails clearly and your credit is refunded — we never show made-up results."],
  ["Does it measure bat speed or bowling speed?", "No. Speeds, forces and exact angles need calibrated equipment. Reports show only visual observations with confidence levels."],
  ["Who can see my videos?", "Only you, unless you are in an academy and explicitly turn on report sharing. Videos are stored privately and served through short-lived links."],
  ["Can players under 18 use CricAnalyze?", "Yes, with verified guardian consent. A parent or guardian confirms by email code before any video is uploaded."],
  ["What happens if an analysis fails?", "The reserved credit is refunded automatically and you can retry."],
  ["How do payments work?", "Payments are processed by Razorpay. A plan activates only after the payment is verified on our server."],
  ["Can I delete my data?", "Yes. You can export your data or permanently delete your account from Settings."]];
export const FaqList = ({ limit }) => (
  <Accordion type="single" collapsible className="max-w-3xl" data-testid="faq-list">
    {FAQS.slice(0, limit || FAQS.length).map(([q, a], i) => <AccordionItem key={q} value={`f${i}`}><AccordionTrigger className="text-left">{q}</AccordionTrigger><AccordionContent className="text-slate-400">{a}</AccordionContent></AccordionItem>)}
  </Accordion>
);
export const Faq = () => (<><Seo title="FAQ" path="/faq" description="Answers about video requirements, AI analysis, privacy, minors and payments." jsonLd={{ "@context": "https://schema.org", "@type": "FAQPage", mainEntity: FAQS.map(([q, a]) => ({ "@type": "Question", name: q, acceptedAnswer: { "@type": "Answer", text: a } })) }} />
  <Section><H2 h1 eyebrow="FAQ" title="Frequently asked questions" /><FaqList /></Section></>);

export const Contact = () => {
  const [f, setF] = useState({ name: "", email: "", subject: "", message: "", website: "" });
  const [busy, setBusy] = useState(false);
  const submit = async (e) => {
    e.preventDefault(); setBusy(true);
    try { const { data } = await api.post("/contact", f); toast.success(data.message); setF({ name: "", email: "", subject: "", message: "", website: "" }); } catch (err) { toast.error(errMsg(err)); } finally { setBusy(false); }
  };
  return (<><Seo title="Contact" path="/contact" description="Contact the CricAnalyze team." />
    <Section><H2 h1 eyebrow="Contact" title="Talk to us" desc="Questions about plans, academies or your account? Send a message and we'll reply by email." />
      <form onSubmit={submit} className="glass rounded-2xl p-6 max-w-2xl grid gap-4" data-testid="contact-form">
        <div className="grid sm:grid-cols-2 gap-4"><Input placeholder="Your name" required value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} data-testid="contact-name" aria-label="Name" />
          <Input type="email" placeholder="Email" required value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} data-testid="contact-email" aria-label="Email" /></div>
        <Input placeholder="Subject" required value={f.subject} onChange={(e) => setF({ ...f, subject: e.target.value })} data-testid="contact-subject" aria-label="Subject" />
        <Textarea placeholder="Message (at least 10 characters)" required minLength={10} rows={6} value={f.message} onChange={(e) => setF({ ...f, message: e.target.value })} data-testid="contact-message" aria-label="Message" />
        <input className="hidden" tabIndex={-1} autoComplete="off" value={f.website} onChange={(e) => setF({ ...f, website: e.target.value })} aria-hidden="true" />
        <Button type="submit" disabled={busy} className="justify-self-start" data-testid="contact-submit-btn">Send message</Button>
      </form></Section></>);
};

export const Legal = ({ slug }) => {
  const params = useParams();
  const [title, sections] = LEGAL[slug || params.slug] || LEGAL.disclaimer;
  return (<><Seo title={title} path={`/${slug}`} description={`${title} for CricAnalyze, a product of ${COMPANY}.`} />
    <Section className="max-w-3xl"><div className="eyebrow mb-3">Legal</div><h1 className="text-4xl font-bold mb-3" data-testid="legal-title">{title}</h1>
      <p className="text-sm text-slate-400 mb-10" data-testid="legal-updated">Last updated: {LEGAL_UPDATED}</p>
      <div className="space-y-8 text-slate-300 leading-relaxed" data-testid="legal-content">{sections.map(([h, paras]) => (
        <section key={h}><h2 className="text-lg font-semibold text-white mb-2">{h}</h2><div className="space-y-2">{paras.map((p) => <p key={p}>{p}</p>)}</div></section>))}</div>
      <p className="text-sm text-slate-500 mt-12" data-testid="legal-company">CricAnalyze is a product of {COMPANY} · cricanalyze.in</p></Section></>);
};

export const NotFound = () => (<><Seo title="Page not found" path="/404" noindex /><Section className="text-center"><div className="font-mono text-[#00B4D8]">404</div><h1 className="text-4xl font-bold mt-2">This page isn't here</h1>
  <p className="text-slate-400 mt-3">The link may be broken or the page may have moved.</p><Button asChild className="mt-6" data-testid="notfound-home-btn"><Link to="/">Go home</Link></Button></Section></>);
