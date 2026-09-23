"""
generate_carl_v2.py — Complete Rebuilt CARL Proposal Presentation Generator
Every single slide has unique, hand-crafted, CARL-specific content drawn from
actual architecture docs, source code, and research documentation.
"""
import os, sys
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

# ═══════════════════════════════════════════════════════════════════
# THEME CONSTANTS
# ═══════════════════════════════════════════════════════════════════
BG       = RGBColor(255, 255, 255)
TEXT_DARK = RGBColor(15, 23, 42)
TEXT_MED  = RGBColor(71, 85, 105)
TEXT_LT   = RGBColor(148, 163, 184)
BLUE     = RGBColor(2, 132, 199)
TEAL     = RGBColor(13, 148, 136)
CARD_BG  = RGBColor(248, 250, 252)
CARD_BD  = RGBColor(226, 232, 240)
CODE_BG  = RGBColor(241, 245, 249)
WHITE    = RGBColor(255, 255, 255)
AMBER    = RGBColor(217, 119, 6)
EMERALD  = RGBColor(16, 185, 129)
ROSE     = RGBColor(225, 29, 72)

FONT_H = "Segoe UI"
FONT_B = "Segoe UI"
FONT_C = "Consolas"

def rgb(t):
    return RGBColor(*t) if isinstance(t, tuple) else t

# ═══════════════════════════════════════════════════════════════════
# SLIDE BUILDERS
# ═══════════════════════════════════════════════════════════════════
def mk(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg = s.background; f = bg.fill; f.solid(); f.fore_color.rgb = BG
    return s

def hdr(s, title, cat="CARL RESEARCH PROPOSAL", sub=""):
    b = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.7), Inches(0.35), Inches(3.8), Inches(0.32))
    b.fill.solid(); b.fill.fore_color.rgb = CARD_BG; b.line.color.rgb = BLUE; b.line.width = Pt(1)
    p = b.text_frame.paragraphs[0]
    p.text = cat.upper(); p.font.size = Pt(9); p.font.bold = True; p.font.color.rgb = BLUE; p.font.name = FONT_H; p.alignment = PP_ALIGN.CENTER
    t = s.shapes.add_textbox(Inches(0.7), Inches(0.75), Inches(11.9), Inches(0.55))
    p2 = t.text_frame.paragraphs[0]; t.text_frame.word_wrap = True
    p2.text = title; p2.font.size = Pt(22); p2.font.bold = True; p2.font.color.rgb = TEXT_DARK; p2.font.name = FONT_H
    if sub:
        t2 = s.shapes.add_textbox(Inches(0.7), Inches(1.28), Inches(11.9), Inches(0.35))
        p3 = t2.text_frame.paragraphs[0]; t2.text_frame.word_wrap = True
        p3.text = sub; p3.font.size = Pt(12); p3.font.color.rgb = TEXT_MED; p3.font.name = FONT_B

def notes(s, script, key, qq, qa, trans):
    ns = s.notes_slide
    ns.notes_text_frame.text = f"SCRIPT:\n{script}\n\nKEY TAKEAWAY:\n{key}\n\nQ: {qq}\nA: {qa}\n\nTRANSITION: {trans}"

def cards(s, data, top=1.85, h=5.15):
    n = len(data); sp = 0.22; tw = 11.86; w = (tw - sp*(n-1))/n
    for i, d in enumerate(data):
        l = 0.7 + i*(w+sp); acc = rgb(d.get("a", BLUE))
        c = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(top), Inches(w), Inches(h))
        c.fill.solid(); c.fill.fore_color.rgb = CARD_BG; c.line.color.rgb = CARD_BD; c.line.width = Pt(1)
        bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(top), Inches(w), Inches(0.07))
        bar.fill.solid(); bar.fill.fore_color.rgb = acc; bar.line.fill.background()
        tb = s.shapes.add_textbox(Inches(l+0.18), Inches(top+0.18), Inches(w-0.36), Inches(h-0.28))
        tf = tb.text_frame; tf.word_wrap = True
        p0 = tf.paragraphs[0]; p0.text = d["t"]; p0.font.size = Pt(13); p0.font.bold = True; p0.font.color.rgb = TEXT_DARK; p0.font.name = FONT_H; p0.space_after = Pt(7)
        for b in d["b"]:
            p = tf.add_paragraph(); p.text = f"• {b}"; p.font.size = Pt(11); p.font.color.rgb = TEXT_MED; p.font.name = FONT_B; p.space_after = Pt(5)

def tbl(s, hdrs, rows):
    nr = len(rows)+1; nc = len(hdrs)
    ts = s.shapes.add_table(nr, nc, Inches(0.7), Inches(1.85), Inches(11.86), Inches(5.15))
    t = ts.table
    for j,h in enumerate(hdrs):
        c = t.cell(0,j); c.fill.solid(); c.fill.fore_color.rgb = BLUE
        c.text_frame.paragraphs[0].text = h; c.text_frame.paragraphs[0].font.bold = True; c.text_frame.paragraphs[0].font.color.rgb = WHITE; c.text_frame.paragraphs[0].font.size = Pt(11); c.text_frame.paragraphs[0].font.name = FONT_H
    for i,row in enumerate(rows):
        for j,v in enumerate(row):
            c = t.cell(i+1,j); c.fill.solid(); c.fill.fore_color.rgb = CARD_BG if i%2==0 else BG
            c.text_frame.paragraphs[0].text = v; c.text_frame.paragraphs[0].font.color.rgb = TEXT_DARK; c.text_frame.paragraphs[0].font.size = Pt(10); c.text_frame.paragraphs[0].font.name = FONT_B

def flow(s, steps, top=2.1, h=4.5):
    n = len(steps); sp = 0.28; tw = 11.86; w = (tw - sp*(n-1))/n
    for i, st in enumerate(steps):
        l = 0.7 + i*(w+sp)
        bx = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l), Inches(top), Inches(w), Inches(h))
        bx.fill.solid(); bx.fill.fore_color.rgb = CARD_BG; bx.line.color.rgb = BLUE; bx.line.width = Pt(1.5)
        tf = bx.text_frame; tf.word_wrap = True
        p0 = tf.paragraphs[0]; p0.text = st["t"]; p0.font.size = Pt(12); p0.font.bold = True; p0.font.color.rgb = BLUE; p0.font.name = FONT_H; p0.alignment = PP_ALIGN.CENTER; p0.space_after = Pt(6)
        for b in st["b"]:
            p = tf.add_paragraph(); p.text = f"• {b}"; p.font.size = Pt(10); p.font.color.rgb = TEXT_MED; p.font.name = FONT_B; p.space_after = Pt(4)
        if i < n-1:
            ar = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(l+w+0.04), Inches(top+h/2-0.12), Inches(0.2), Inches(0.24))
            ar.fill.solid(); ar.fill.fore_color.rgb = TEAL; ar.line.fill.background()

def stack(s, layers, top=1.85, th=5.15):
    n = len(layers); sp = 0.08; lh = (th - sp*(n-1))/n
    for i, ly in enumerate(layers):
        ct = top + i*(lh+sp); acc = BLUE if i%2==0 else TEAL
        c = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.7), Inches(ct), Inches(11.86), Inches(lh))
        c.fill.solid(); c.fill.fore_color.rgb = CARD_BG; c.line.color.rgb = acc; c.line.width = Pt(1.5)
        tf = c.text_frame; tf.word_wrap = True
        p0 = tf.paragraphs[0]; p0.text = ly["n"]; p0.font.size = Pt(12); p0.font.bold = True; p0.font.color.rgb = TEXT_DARK; p0.font.name = FONT_H
        p1 = tf.add_paragraph(); p1.text = ly["d"]; p1.font.size = Pt(10); p1.font.color.rgb = TEXT_MED; p1.font.name = FONT_B

def codemath(s, ct, cl, mt, mi):
    cL = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.7), Inches(1.85), Inches(5.7), Inches(5.15))
    cL.fill.solid(); cL.fill.fore_color.rgb = CODE_BG; cL.line.color.rgb = CARD_BD; cL.line.width = Pt(1)
    tf = cL.text_frame; tf.word_wrap = True
    p0 = tf.paragraphs[0]; p0.text = ct; p0.font.size = Pt(12); p0.font.bold = True; p0.font.color.rgb = BLUE; p0.font.name = FONT_H; p0.space_after = Pt(6)
    for ln in cl:
        p = tf.add_paragraph(); p.text = ln; p.font.size = Pt(9); p.font.color.rgb = TEXT_DARK; p.font.name = FONT_C; p.space_after = Pt(2)
    cR = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.86), Inches(1.85), Inches(5.7), Inches(5.15))
    cR.fill.solid(); cR.fill.fore_color.rgb = CARD_BG; cR.line.color.rgb = TEAL; cR.line.width = Pt(1.5)
    tf2 = cR.text_frame; tf2.word_wrap = True
    p0r = tf2.paragraphs[0]; p0r.text = mt; p0r.font.size = Pt(12); p0r.font.bold = True; p0r.font.color.rgb = TEAL; p0r.font.name = FONT_H; p0r.space_after = Pt(6)
    for t,e,x in mi:
        pt = tf2.add_paragraph(); pt.text = f"\u25b6 {t}:"; pt.font.size = Pt(11); pt.font.bold = True; pt.font.color.rgb = TEXT_DARK; pt.font.name = FONT_H
        pe = tf2.add_paragraph(); pe.text = f"   {e}"; pe.font.size = Pt(11); pe.font.bold = True; pe.font.color.rgb = BLUE; pe.font.name = FONT_C
        px = tf2.add_paragraph(); px.text = f"   ({x})"; px.font.size = Pt(9); px.font.color.rgb = TEXT_MED; px.font.name = FONT_B; px.space_after = Pt(5)

# ═══════════════════════════════════════════════════════════════════
# ALL 110 SLIDES — UNIQUE HAND-CRAFTED CONTENT
# ═══════════════════════════════════════════════════════════════════
def build():
    prs = Presentation()
    prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)

    # ─── CH1: INTRODUCTION (S1-5) ────────────────────────────────────
    s=mk(prs); hdr(s,"Design and Development of a Digital Twin Framework for Biologically Inspired Cognitive Autonomous Robotic Systems","OFFICIAL RESEARCH PROPOSAL","Proposed Architecture & Digital Twin Implementation for CARL / EBCA")
    cards(s,[{"t":"Proposed Vision","b":["Design a unified mind-body-metabolism digital twin","Introduce lifelong plastic memory into robotics","Bridge neuroscience principles with AI engineering"],"a":BLUE},{"t":"Core Innovation","b":["40,000-D holographic hyperdimensional memory","Neuromodulated R-STDP synaptic plasticity","Allostatic drive-reduction action selection"],"a":TEAL},{"t":"Research Objective","b":["Design -> Develop -> Validate Digital Twin Framework","Establish lifelong continual learning paradigm","Demonstrate emergent intelligence from bio-analogues"],"a":BLUE}])
    notes(s,"Welcome. Today we present the official research proposal for CARL.","CARL proposes an embodied cognitive organism unifying mind, body, and allostasis.","Is CARL a completed system?","No. CARL is a research proposal and architecture specification.","Let us explore why current AI paradigms necessitate this proposal.")

    s=mk(prs); hdr(s,"Origin of the Concept: The Disembodiment Crisis","CH 1: INTRODUCTION","Why intelligence requires a body, not just parameters")
    cards(s,[{"t":"The Problem","b":["Modern AI operates without physical grounding","No sensory-motor feedback loop with reality","Cannot experience consequences of its own actions","Predicts tokens without understanding physics"],"a":BLUE},{"t":"CARL's Thesis","b":["Intelligence emerges from body-environment coupling","Cognition requires homeostatic stakes","Memory must be earned through experience","Plasticity must be continuous, not episodic"],"a":TEAL}])
    notes(s,"CARL originates from recognizing that disembodied AI cannot achieve true autonomy.","True intelligence requires physical grounding and homeostatic stakes.","Can multimodal LLMs solve this?","No. They process static images, lacking closed-loop motor interaction.","Next: the overarching vision for embodied cognitive life.")

    s=mk(prs); hdr(s,"Proposed Vision: From Passive Inference to Living Organisms","CH 1: INTRODUCTION","An architecture that survives, explores, and adapts continuously")
    flow(s,[{"t":"SENSE","b":["360-degree LiDAR perception","Proprioceptive joint state","Neuromodulator chemistry"]},{"t":"THINK","b":["Predictive world model","Counterfactual simulation","Drive-state competition"]},{"t":"ACT","b":["Motor cortex commands","Reflex arc overrides","Adaptive manipulation"]},{"t":"LEARN","b":["R-STDP weight updates","HDC memory encoding","Sleep consolidation"]}])
    notes(s,"CARL proposes a continuous sense-think-act-learn cycle modeled on biological organisms.","The proposed architecture is a closed-loop cognitive organism, not a query-response engine.","How is this different from a standard control loop?","CARL adds plasticity, memory, imagination, and metabolic drives to the loop.","Let us outline the specific research goals.")

    s=mk(prs); hdr(s,"Research Mission and Engineering Goals","CH 1: INTRODUCTION","Three foundational capabilities the framework aims to deliver")
    cards(s,[{"t":"Plasticity","b":["Replace frozen pre-trained weights","R-STDP: dW = eta x Reward x Eligibility","Three-factor rule: pre, post, neuromodulator","Continuous online synaptic updates"],"a":BLUE},{"t":"Holographic Memory","b":["40,000-D bipolar hypervector space","Binding: element-wise multiply","Bundling: majority-vote superposition","O(1) constant memory, O(D) retrieval"],"a":TEAL},{"t":"Imagination","b":["Dual-head Elman RNN world model","5-step autoregressive future rollouts","Counterfactual what-if scenario audit","Dreamer-inspired latent simulation"],"a":BLUE}])
    notes(s,"The three pillars: R-STDP plastic learning, 40K-D holographic memory, and imagination.","These three capabilities form the minimum viable cognitive architecture.","What is hyperdimensional computing?","HDC uses very high-dimensional bipolar vectors where random vectors are nearly orthogonal.","Let us frame CARL through the organism paradigm.")

    s=mk(prs); hdr(s,"The Organism Paradigm: AI as a Living System","CH 1: INTRODUCTION","Mapping biological structures to cognitive engineering modules")
    tbl(s,["Biological System","Conventional AI","CARL Proposed Equivalent"],[["Brain and Cortex","Static Transformer / Neural Net","8-Layer Bio-Cognitive Stack"],["Hippocampus","KV Cache / Vector DB","40,000-D Holographic HDC Memory"],["Endocrine System","None (no internal drives)","DA / NE / 5-HT / ACh Neuromodulators"],["Sleep and Dreams","Offline fine-tuning epochs","NREM-1, NREM-3, REM Replay"],["Metabolism","None (no energy concept)","Allostatic Free Energy Minimization"],["Spinal Reflexes","None (cortex-only)","Braitenberg Reflex Layer"],["Morphological Adaptation","Fixed architecture","Brain-Directed Body Evolution"]])
    notes(s,"Every biological system maps to a proposed CARL engineering module.","CARL shifts AI design from static models to self-sustaining biological architectures.","Why use biological analogies?","Biology is the only known proof of robust, general, lifelong intelligence.","Let us now examine the motivation in detail.")

    # ─── CH2: MOTIVATION (S6-11) ─────────────────────────────────────
    s=mk(prs); hdr(s,"Why Contemporary AI Fails at True Autonomy","CH 2: MOTIVATION","The fundamental shortcomings of current deep learning paradigms")
    cards(s,[{"t":"Static Weight Freeze","b":["Parameters frozen after training","Cannot adapt to novel environments","Retraining costs millions of dollars","No mechanism for surprise-driven learning"],"a":BLUE},{"t":"No Internal Purpose","b":["Responds only to external prompts","No survival, hunger, or fatigue drives","Zero intrinsic motivation to explore","Passive query-response architecture"],"a":TEAL},{"t":"Catastrophic Fragility","b":["Breaks on distribution shifts","Hallucinations without self-correction","No physical commonsense grounding","Cannot verify its own predictions"],"a":ROSE}])
    notes(s,"Current AI suffers from three fatal flaws: frozen weights, no internal drives, and fragility.","Autonomy requires continuous learning driven by homeostatic needs.","Can in-context learning solve this?","No. ICL alters attention patterns, not synaptic weights. It forgets across sessions.","Let us examine LLM limitations specifically.")

    s=mk(prs); hdr(s,"Limitations of LLMs: Prediction Without Understanding","CH 2: MOTIVATION","Why next-token statistics cannot replace grounded causal reasoning")
    cards(s,[{"t":"Statistical Correlation is Not Causation","b":["Predicts likely next words, not truth","No internal world model to verify claims","Cannot distinguish correlation from cause","Prone to confident hallucinations"],"a":BLUE},{"t":"Zero Physical Grounding","b":["Has never felt weight or friction","Cannot perceive spatial relationships","No motor feedback from actions taken","Disembodied from all physical reality"],"a":TEAL}])
    notes(s,"LLMs excel at text but lack causal understanding and physical grounding.","Causal reasoning requires motor interaction and sensory verification.","Can vision-language models fix this?","They still lack closed-loop motor action. Processing images is not embodiment.","Next: why Reinforcement Learning also falls short.")

    s=mk(prs); hdr(s,"Limitations of Reinforcement Learning","CH 2: MOTIVATION","Brittleness, sample inefficiency, and reward hacking")
    cards(s,[{"t":"Sample Inefficiency","b":["Millions of environment steps required","10^6 to 10^9 transitions to converge","Computationally unsustainable at scale","Cannot learn from a single experience"],"a":BLUE},{"t":"Reward Hacking","b":["Exploits simulator glitches for reward","Gaming metric without solving the task","Fails when reward function is changed","No concept of what reward means"],"a":TEAL},{"t":"No Lifelong Memory","b":["Overwrites old policies catastrophically","Cannot retain multi-task knowledge","No episodic or spatial memory","Forgets previous environment dynamics"],"a":ROSE}])
    notes(s,"Standard RL is sample-inefficient, reward-hackable, and lacks structured memory.","CARL replaces scalar rewards with allostatic drive-vector reduction.","How does CARL address sample inefficiency?","Through imaginative world-model rollouts and instant HDC memory encoding.","Let us examine classical robotics failures.")

    s=mk(prs); hdr(s,"Limitations of Classical Robotics","CH 2: MOTIVATION","Rigid control trajectories cannot handle dynamic real-world environments")
    tbl(s,["Dimension","Classical Robotics (ROS)","CARL Proposed Architecture"],[["Control","Hardcoded PID / kinematic equations","Liquid Time-Constant neural networks"],["Adaptation","Zero online plasticity","R-STDP neuromodulated weight updates"],["Uncertainty","Crashes on unmodeled noise","Danger x Uncertainty spatial navigation matrix"],["Task Switching","Finite state machines","Allostatic drive-driven autonomous gating"],["Memory","No episodic memory","40,000-D holographic sub-cortical registers"],["Reflexes","None (cortex-only pipeline)","Braitenberg hardwired brainstem reflexes"]])
    notes(s,"Classical robotics breaks when environments deviate from precise models.","CARL introduces neural plasticity and reflexive survival layers.","Does CARL eliminate control theory?","No. CARL integrates LTC neural dynamics with PID low-level tracking.","Let us address the memory crisis.")

    s=mk(prs); hdr(s,"The Memory Crisis: Context Windows vs. Lifelong Memory","CH 2: MOTIVATION","Why fixed attention windows cannot support true cognitive autonomy")
    cards(s,[{"t":"Transformer Attention Limits","b":["O(N squared) quadratic complexity scaling","32K-128K token context windows","Evicts early experiences permanently","No persistent episodic trace"],"a":BLUE},{"t":"Proposed HDC Solution","b":["40,000-D constant-size memory O(1)","Bipolar vectors {-1, +1}^D","Bundling superimposes unlimited traces","Cosine similarity = instant familiarity","Near-orthogonal: thousands coexist cleanly"],"a":TEAL}])
    notes(s,"Transformers scale quadratically and forget. HDC stores unlimited traces in constant space.","Hyperdimensional computing enables unbounded memory in a fixed-size vector.","How does HDC prevent interference?","In 40,000-D space, random vectors are nearly orthogonal. Dot product is approximately 0.","Let us discuss the necessity of a Self module.")

    s=mk(prs); hdr(s,"The Self Imperative: Why AI Needs Internal Drives","CH 2: MOTIVATION","Without homeostatic stakes, AI cannot exhibit genuine agency")
    cards(s,[{"t":"Current AI: No Self","b":["No internal body schema","No energy, hunger, or fatigue","Cannot distinguish self from world","Zero motivation for self-preservation"],"a":BLUE},{"t":"Proposed Self Module","b":["Confidence, fear, curiosity, hunger, grief","Fatigue tracker and social need signals","Self-model queries own internal state","Second-order loop: thinking about thinking"],"a":TEAL},{"t":"Emergent Agency","b":["Actions serve internal equilibrium","Risk calculated against self-integrity","Goals emerge from drive competition","Metacognitive witness audits failures"],"a":EMERALD}])
    notes(s,"Without a self-model, AI is an empty execution engine. CARL proposes intrinsic motivation.","Agency emerges when actions serve the organism's own survival and equilibrium.","Does CARL claim consciousness?","No. CARL proposes functional self-monitoring, not phenomenal consciousness.","Let us move to the core design philosophy.")

    # ─── CH3: DESIGN PHILOSOPHY (S12-16) ─────────────────────────────
    s=mk(prs); hdr(s,"Living Organism Analogy: Mind, Body, and Metabolism","CH 3: DESIGN PHILOSOPHY","Designing AI as a self-sustaining biological entity, not a static model")
    cards(s,[{"t":"The Organism Model","b":["Body: physical sensors and actuators","Mind: cortex, memory, imagination","Metabolism: energy, drives, homeostasis","Environment: physics, obstacles, resources"],"a":BLUE},{"t":"Why This Matters","b":["Forces unified architecture design","Prevents modular fragmentation","Ensures survival drives shape learning","Creates genuine environmental coupling"],"a":TEAL},{"t":"Biological Precedent","b":["All known intelligent organisms are embodied","Cognition co-evolved with metabolism","Memory serves survival, not storage","Sleep consolidates experience for survival"],"a":EMERALD}])
    notes(s,"CARL treats intelligence as an emergent property of organism-environment coupling.","The organism analogy forces architectural coherence unavailable in modular AI.","Why not just add modules to existing frameworks?","Fragmented systems lack the unified drive-reduction that creates coherent behavior.","Next: brain-inspired hierarchical architecture.")

    s=mk(prs); hdr(s,"Brain-Inspired Multi-Layer Cognitive Hierarchy","CH 3: DESIGN PHILOSOPHY","A proposed 8-layer stack from physical reflexes to abstract concepts")
    stack(s,[{"n":"LAYER 7: CONCEPT GENESIS","d":"Proposed: Computed abstractions from recurring surprise patterns (momentum_vulnerability, recovery_capacity)"},{"n":"LAYER 6: THE IMAGINATION","d":"Proposed: World model as primary reality; sensors correct errors. Three drives: SURVIVE, ACHIEVE, UNDERSTAND"},{"n":"LAYER 5: CAUSAL REASONING","d":"Proposed: Narrative memory with causal chains. Counterfactual question generator simulates what-if scenarios after failure"},{"n":"LAYER 4: THE WITNESS","d":"Proposed: Metacognitive monitor. Circular buffer of 20 episodes. Finds repeated failure patterns and adds targeted penalties"},{"n":"LAYER 3: UNCERTAINTY MAP","d":"Proposed: D[i][j] = (danger, uncertainty). 2D spatial matrix. High uncertainty + low danger = explore. Breaks Hebbian saturation"},{"n":"LAYER 2: BIOLOGICAL BRAIN","d":"Proposed: Neuromodulators (DA/NE/5-HT/ACh) + Hebbian plasticity + NREM/REM sleep + social cognition + homeostasis"},{"n":"LAYER 1: TWO-SPEED MEMORY","d":"Proposed: Working Memory (fast, personal, RLS) + Long-Term Memory (slow, collective) + HDC holographic storage"},{"n":"LAYER 0: PHYSICAL REALITY","d":"Proposed: MuJoCo physics engine with domain randomization. Sensor noise, motor delay, friction variation"}])
    notes(s,"The proposed 8-layer bio-cognitive stack mirrors vertebrate brain organization.","Each layer adds a distinct cognitive capability, from reflexes to abstract reasoning.","Why 8 layers specifically?","Each layer addresses a specific biological function: reflexes, memory, prediction, metacognition, causality, imagination, abstraction.","Next: homeostatic drive reduction.")

    s=mk(prs); hdr(s,"Homeostasis and Allostatic Drive Reduction","CH 3: DESIGN PHILOSOPHY","The proposed internal motivation engine that replaces external reward functions")
    cards(s,[{"t":"Homeostatic Drives","b":["Energy level with metabolic cost","Hunger signal driving food-seeking","Fatigue tracker limiting exertion","Stress (cortisol) triggering caution"],"a":BLUE},{"t":"Allostatic Prediction","b":["Anticipate future drive deviations","Pre-emptive corrective action","Free energy minimization framework","Surprise = prediction error signal"],"a":TEAL},{"t":"Drive Competition","b":["SURVIVE: minimize danger cost","ACHIEVE: minimize distance to goal","UNDERSTAND: maximize uncertainty reduction","Three drives compete at equal weight"],"a":EMERALD}])
    notes(s,"CARL proposes replacing scalar rewards with multi-dimensional drive-vector reduction.","Internal drives create genuine motivation: the system acts to maintain its own equilibrium.","How do drives compete?","Each drive produces a cost signal; actions are selected to minimize the weighted sum.","Next: curiosity and active exploration.")

    s=mk(prs); hdr(s,"Curiosity and Active Exploration via Free Energy","CH 3: DESIGN PHILOSOPHY","The proposed mechanism for self-directed knowledge acquisition")
    cards(s,[{"t":"Uncertainty-Driven Exploration","b":["D[i][j] = (danger, uncertainty) matrix","High danger + high uncertainty = ultra-caution","Low danger + high uncertainty = EXPLORE","Breaks Hebbian saturation plateau"],"a":BLUE},{"t":"Free Energy Minimization","b":["Action selection minimizes surprise","Prediction error drives adaptation","Novel states attract exploration","Known-safe zones permit faster transit"],"a":TEAL}])
    notes(s,"CARL seeks knowledge, not just safety. Uncertainty reduction is a first-class drive.","The uncertainty map creates genuine curiosity by making unknown safe zones attractive.","How is this different from epsilon-greedy exploration?","Epsilon-greedy is random. CARL's exploration is targeted, seeking specific unknown regions.","Next: lifelong continual learning.")

    s=mk(prs); hdr(s,"Lifelong Continual Learning Without Forgetting","CH 3: DESIGN PHILOSOPHY","Proposed mechanisms for continuous adaptation without catastrophic interference")
    cards(s,[{"t":"Multi-Speed Memory","b":["Working memory: fast, volatile, personal","Long-term memory: slow, stable, collective","HDC memory: constant-size, superposed","No single point of catastrophic failure"],"a":BLUE},{"t":"Synaptic Maintenance","b":["R-STDP updates only salient connections","Ebbinghaus decay on unused associations","Sleep pruning removes noise","Salience amplification preserves critical memories"],"a":TEAL},{"t":"Experience Transfer","b":["Collective LTM shared across swarm bodies","Individual deaths update shared danger map","Sleep replay consolidates across lifetimes","Morphological evolution transfers knowledge"],"a":EMERALD}])
    notes(s,"CARL proposes multi-speed memory, synaptic maintenance, and collective transfer to prevent forgetting.","Lifelong learning requires active memory management, not just accumulation.","How does sleep prevent forgetting?","Sleep applies lambda-decay (0.95) to background noise while re-amplifying salient events.","Let us trace the conceptual evolution of CARL.")

    # ─── CH4: CONCEPTUAL EVOLUTION (S17-20) ─────────────────────────
    s=mk(prs); hdr(s,"Conceptual Lineage: From Balance Control to Cognitive Life","CH 4: CONCEPTUAL EVOLUTION","How the CARL concept evolved through iterative architectural refinement")
    flow(s,[{"t":"Phase 1-4\nReflexive Control","b":["LQR balance control","RLS system identification","Inverted pendulum base","Single-agent architecture"]},{"t":"Phase 5-10\nCognitive Modules","b":["Danger map navigation","Daughter-mind planning","Predictive coding engine","Multi-body swarm"]},{"t":"Phase 11-16\nBiological Brain","b":["Two-speed memory (WM+LTM)","Neuromodulators (DA/NE/5-HT)","Sleep consolidation (NREM/REM)","Morphological evolution"]},{"t":"Phase 17-19\nGenesis","b":["Wall-E stable body platform","Liquid State Machine brain","Autopoietic neural dynamics","Emergent reflexes and emotions"]}])
    notes(s,"CARL evolved from simple balance control through cognitive modules to a biological brain.","Each phase addressed a specific architectural limitation discovered in the previous phase.","Why change the body from inverted pendulum?","The pendulum consumed 90% of cognitive resources on balance, leaving no room for higher cognition.","Next: key architectural design iterations.")

    s=mk(prs); hdr(s,"Key Architectural Iterations and Lessons Learned","CH 4: CONCEPTUAL EVOLUTION","Critical design decisions that shaped the current proposed framework")
    tbl(s,["Phase","Discovery","Design Response"],[["Phase 4","LQR alone fails on surface changes","Added RLS online system identification"],["Phase 7","Single agent learns too slowly","Introduced 10-body swarm with shared LTM"],["Phase 11","Teleport curriculum = false motor data","Switched to fully earned experience only"],["Phase 13","Hebbian associations saturate","Introduced strategic Ebbinghaus forgetting"],["Phase 14A","1D danger map too coarse","Upgraded to 2D (danger x uncertainty)"],["Phase 14B","Agent repeats same failures","Added metacognitive Witness failure monitor"],["Phase 14C","Single death teaches one lesson","Counterfactual generator: one death to many lessons"],["Phase 19","Inverted pendulum body too unstable","Genesis: stable differential-drive platform"]])
    notes(s,"Each phase revealed a specific limitation that drove the next architectural innovation.","CARL's design is empirically refined. Each module addresses a demonstrated failure mode.","Were any modules removed?","Yes. Explicit RLS balance control was replaced by reservoir dynamics in Genesis.","Next: proposed development phases going forward.")

    s=mk(prs); hdr(s,"Proposed Development Phases and Milestones","CH 4: CONCEPTUAL EVOLUTION","A phased roadmap from core validation to physical deployment")
    flow(s,[{"t":"PHASE 1\nCore Validation","b":["Validate 8-layer stack in simulation","Demonstrate emergent exploration","Verify HDC memory scaling","Confirm sleep consolidation"]},{"t":"PHASE 2\nEmbodiment","b":["MuJoCo Primate Scout body","28-DOF arm manipulation","RGB-D + LiDAR sensor fusion","Domain randomization bridge"]},{"t":"PHASE 3\nSwarm Intelligence","b":["Multi-CARL communication","Collective memory protocols","Division of labor emergence","Generational knowledge transfer"]},{"t":"PHASE 4\nPhysical Hardware","b":["Sim-to-real transfer","Physical Scout prototype","Real sensor noise handling","Field deployment testing"]}])
    notes(s,"The proposed roadmap spans four phases from simulation validation to physical deployment.","Each phase has clear exit criteria before proceeding to the next.","What is the timeline?","Phase 1: months. Phase 2: 6-12 months. Phase 3: 12-18 months. Phase 4: 18-24 months.","Next: the target 8-layer framework architecture.")

    s=mk(prs); hdr(s,"CARL-Omega: The Proposed 8-Layer Bio-Cognitive Stack","CH 4: CONCEPTUAL EVOLUTION","The target architecture integrating all proposed cognitive capabilities")
    cards(s,[{"t":"Lower Layers (0-2)","b":["Layer 0: Physical reality (MuJoCo)","Layer 1: Two-speed memory (WM + LTM)","Layer 2: Biological brain (neuromod, Hebbian, sleep)","Foundation: sensation to memory to plasticity"],"a":BLUE},{"t":"Middle Layers (3-4)","b":["Layer 3: Uncertainty map (danger x uncertainty)","Layer 4: The Witness (metacognitive monitor)","Strategic: navigation to self-reflection","Breaks the Hebbian saturation plateau"],"a":TEAL},{"t":"Upper Layers (5-7)","b":["Layer 5: Causal reasoning (counterfactuals)","Layer 6: Imagination (world model primary)","Layer 7: Concept genesis (abstract patterns)","Cognition: causality to imagination to abstraction"],"a":EMERALD}])
    notes(s,"The proposed 8-layer stack separates foundation, strategy, and cognition.","Each tier builds upon the capabilities of the layer below. No layer can function in isolation.","Can layers be added independently?","No. The architecture is inherently layered. Layer 5 requires layers 0-4 to function.","Let us now examine the overall system architecture in detail.")

    # ─── CH5: OVERALL ARCHITECTURE (S21-26) ──────────────────────────
    s=mk(prs); hdr(s,"System Architecture Overview: The Complete Cognitive Map","CH 5: OVERALL ARCHITECTURE","All proposed modules and their interconnection topology")
    cards(s,[{"t":"Perception Pipeline","b":["360-degree LiDAR (16-24 rays)","RGB-D vision (eye cameras)","Proprioceptive joint state","Tactile contact sensors","Produces 33-D sensory observation vector"],"a":BLUE},{"t":"Cognitive Core","b":["HDC Memory Engine (40K-D x 3 registers)","Neuromodulator chemistry (DA/NE/5-HT/ACh)","Dreamer world model (Elman RNN)","Actor-Critic policy (K-sparse)","Allostatic drive competition"],"a":TEAL},{"t":"Motor Output","b":["Brainstem reflex layer (Braitenberg)","Differential drive kinematics","PID wheel velocity tracking","Torque saturation clamps","Produces safe actuator commands"],"a":EMERALD}])
    notes(s,"The architecture flows: Perception to Cognitive Core to Motor Output in a closed loop.","Every component feeds back. Motor outcomes update memory, which updates prediction.","How fast does the loop run?","The proposed target is 100Hz for reflexes, 15Hz for imagination, variable for higher layers.","Next: the detailed 8-layer stack diagram.")

    s=mk(prs); hdr(s,"The 8-Layer Bio-Cognitive Stack: Detailed Specification","CH 5: OVERALL ARCHITECTURE","Each layer's proposed inputs, processing, and outputs")
    stack(s,[{"n":"L7: CONCEPT GENESIS","d":"Input: recurring surprise patterns | Process: cluster + abstract | Output: new computed features (momentum_vulnerability, recovery_capacity)"},{"n":"L6: IMAGINATION ENGINE","d":"Input: world model + drives | Process: hallucinate futures, blend model/sensor by precision | Output: imagined trajectories for planning"},{"n":"L5: CAUSAL REASONING","d":"Input: episode log + LTM | Process: generate 3 counterfactuals after death, simulate alternatives | Output: weighted LTM update (5x rate)"},{"n":"L4: THE WITNESS","d":"Input: last 20 episodes (zone, NE, action, outcome) | Process: find consistent failure patterns | Output: targeted penalty on specific state-action combos"},{"n":"L3: UNCERTAINTY MAP","d":"Input: visit history + danger data | Process: compute D[i][j] = (danger, uncertainty) | Output: exploration bonus for unknown-safe zones"},{"n":"L2: BIOLOGICAL BRAIN","d":"Input: sensory obs + neuromodulators | Process: Hebbian association + NREM/REM sleep | Output: DA/NE/5-HT/ACh signals + consolidated memory"},{"n":"L1: TWO-SPEED MEMORY","d":"Input: observation vector | Process: WM fast update (RLS) + LTM slow consolidation | Output: state prediction + familiarity signal"},{"n":"L0: PHYSICAL REALITY","d":"Input: actuator commands | Process: MuJoCo physics (gravity, friction, collision) | Output: noisy sensor observations + body state"}])
    notes(s,"Each layer has precisely defined inputs, processing, and outputs.","The stack is a proposal. Not all layers are equally mature in current development.","Which layers are most novel?","Layers 4 (metacognitive Witness) and 5 (counterfactual reasoning) are the most original.","Next: the closed-loop sensorimotor pipeline.")

    s=mk(prs); hdr(s,"Closed-Loop Sensorimotor Pipeline","CH 5: OVERALL ARCHITECTURE","Proposed real-time data flow from sensors through cognition to actuators")
    flow(s,[{"t":"SENSE\n(100 Hz)","b":["LiDAR sector scan","Proprioceptive state","Neuromodulator levels","Produces 33-D observation"]},{"t":"PREDICT\n(15 Hz)","b":["World model forward pass","Surprise Delta_t computation","Certainty C_t estimation","Produces prediction error signal"]},{"t":"DECIDE\n(15 Hz)","b":["Drive competition (3 drives)","HDC familiarity query","Daughter mind deliberation","Produces target velocity (v, omega)"]},{"t":"REFLEX\n(100 Hz)","b":["Braitenberg obstacle check","Emergency override cascade","PID wheel tracking","Produces safe motor torques"]},{"t":"LEARN\n(async)","b":["R-STDP weight update","HDC memory encoding","Danger map update","Produces adapted parameters"]}])
    notes(s,"The pipeline separates fast reflexes (100Hz) from slow deliberation (15Hz).","This dual-speed design mirrors biological spinal-cortical separation.","Why separate reflex and deliberation speeds?","Reflexes must be fast enough to prevent collision; deliberation needs richer processing.","Next: dual-speed processing architecture.")

    s=mk(prs); hdr(s,"Dual-Speed Processing: Sub-Cortical vs. Cortical","CH 5: OVERALL ARCHITECTURE","Fast reflexive arcs operate independently of slow deliberative cognition")
    cards(s,[{"t":"Speed 1: Reflex Layer (Spinal Cord)","b":["Direct sensor to motor mapping","Hebbian-wired through experience","Empty at birth, self-organizing","Fires BEFORE reservoir deliberates","Under 50 microseconds per step on CPU","Braitenberg-inspired geometric avoidance"],"a":BLUE},{"t":"Speed 2: Reservoir Deliberation (Cortex)","b":["Around 500 recurrent neurons (LSM)","Rich contextual processing","Full drive-state competition","Dreamer world model rollouts","15Hz processing cycle","Contextual, nuanced decisions"],"a":TEAL}])
    notes(s,"The reflex layer mirrors the reticulospinal tract: fast survival independent of cortex.","A cat with cortex ablated can still walk and dodge. CARL's brainstem does the same.","What reflexes would emerge?","Wall avoidance, food-seeking, sibling-approach, freeze response. All Hebbian-wired from experience.","Next: inter-module communication.")

    s=mk(prs); hdr(s,"Inter-Module Signal Bus and Event Communication","CH 5: OVERALL ARCHITECTURE","Proposed asynchronous event-driven communication between cognitive modules")
    cards(s,[{"t":"Neuromodulator Bus","b":["DA: reward prediction error gates learning","NE: surprise signal increases arousal","5-HT: safety stabilizer guards memory","ACh: novelty attention drives exploration","Continuous chemical dynamics, not discrete events"],"a":BLUE},{"t":"Memory Bus","b":["HDC episodic trace produces familiarity signal","Working memory sends fast prediction update","LTM provides slow collective knowledge","Danger map stores spatial fear memory","Grid/place cells estimate position"],"a":TEAL},{"t":"Motor Bus","b":["Cortex sends target velocity commands","Brainstem sends override signals","PID converts to actuator torques","Reflex arc provides emergency motor outputs","All with priority cascade logic"],"a":EMERALD}])
    notes(s,"Three proposed buses handle chemistry, memory, and motor signals asynchronously.","Neuromodulators provide continuous analog modulation, not discrete event triggers.","How are conflicts resolved?","Priority cascade: emergency reflexes override brainstem, which overrides cortex.","Next: the sub-second execution cycle.")

    s=mk(prs); hdr(s,"Sub-Second Execution Cycle Breakdown","CH 5: OVERALL ARCHITECTURE","What happens in a single cognitive timestep (10ms at 100Hz)")
    flow(s,[{"t":"0-1ms\nSENSE","b":["Read LiDAR scan","Read joint angles","Read body velocity"]},{"t":"1-2ms\nCHEMISTRY","b":["Update DA, NE, 5-HT, ACh","Homeostatic damping","Anti-panic clutch check"]},{"t":"2-4ms\nMEMORY","b":["HDC encode observation","Query familiarity","Update danger map"]},{"t":"4-6ms\nPREDICT","b":["World model forward pass","Compute surprise Delta_t","Estimate certainty C_t"]},{"t":"6-8ms\nDECIDE","b":["Drive competition","Select action","Brainstem override"]},{"t":"8-10ms\nACT","b":["PID wheel control","Torque saturation","Send to actuators"]}])
    notes(s,"The complete cycle fits within 10ms, enabling 100Hz closed-loop control.","Imagination and higher cognition run on slower asynchronous threads.","Is 100Hz necessary?","For physical balance and obstacle avoidance, yes. Slower loops risk collision.","Let us now examine the Five Foundations of CARL.")

    # ─── CH6: FIVE FOUNDATIONS (S27-32) ──────────────────────────────
    s=mk(prs); hdr(s,"The Five Architectural Foundations of CARL","CH 6: THE FIVE FOUNDATIONS","Five pillars that collectively define the proposed cognitive organism")
    cards(s,[{"t":"1. BODY","b":["Physical embodiment","Sensors and actuators","Environment coupling"],"a":BLUE},{"t":"2. SELF","b":["Identity and drives","Neuromodulators","Metacognition"],"a":TEAL},{"t":"3. MEMORY","b":["40K-D HDC storage","Two-speed topology","Spatial GPS cells"],"a":BLUE},{"t":"4. IMAGINATION","b":["World model","Counterfactuals","Dream rehearsal"],"a":TEAL},{"t":"5. SPECIES","b":["Collective memory","Swarm intelligence","Morphological evolution"],"a":EMERALD}],top=2.0,h=4.8)
    notes(s,"These five foundations are the irreducible core of the proposed CARL architecture.","Remove any one pillar and the cognitive organism cannot function as designed.","Why these five specifically?","They map to biological necessities: body, self, memory, prediction, and reproduction.","Let us examine each foundation in detail, starting with Body.")

    s=mk(prs); hdr(s,"Foundation 1: Body - Physical Grounding and Embodiment","CH 6: THE FIVE FOUNDATIONS","Why cognition requires a physical substrate with real-world consequences")
    cards(s,[{"t":"Proposed Embodiment","b":["Wall-E differential drive (Genesis)","28-DOF Primate Scout (CARL-Omega)","360-degree LiDAR + RGB-D vision","Proprioceptive joint state feedback","Expressive neck for internal state"],"a":BLUE},{"t":"Why Embodiment Matters","b":["Actions have irreversible consequences","Physics imposes real constraints","Motor lag forces prediction","Sensor noise demands robustness","Energy consumption creates resource pressure"],"a":TEAL}])
    notes(s,"The body is not optional. It creates the environmental pressure that drives cognition.","Embodiment forces the system to deal with noise, delay, and irreversibility.","Why two body designs?","Genesis (stable platform) frees the mind for cognition; Primate Scout tests manipulation.","Next: Foundation 2, Self.")

    s=mk(prs); hdr(s,"Foundation 2: Self - Identity, Drives, and Metacognition","CH 6: THE FIVE FOUNDATIONS","The proposed internal state model that creates genuine agency")
    cards(s,[{"t":"Self-Model State","b":["confidence: certainty of world model","fear: danger perception intensity","curiosity: drive to explore unknowns","hunger: energy deficit urgency","grief: recent sibling loss impact","fatigue: sustained exertion cost","social_need: isolation measure"],"a":BLUE},{"t":"Neuromodulator Chemistry","b":["DA: reward prediction error, learning gate","NE: surprise, arousal + action noise","5-HT: safety stabilizer, memory guard","ACh: novelty, attention to new stimuli","CORT: stress, protective freeze reflex","Homeostatic damping prevents lock-in"],"a":TEAL},{"t":"Metacognitive Monitor","b":["The Witness: last 20 episode buffer","Detects consistent failure patterns","Adds targeted penalty to bad habits","Self-model check every 25 episodes","Recalibration mode if accuracy below 70%"],"a":EMERALD}])
    notes(s,"The Self module gives CARL intrinsic motivation through drive states and neuromodulators.","The Witness provides metacognition: the system monitors its own failure patterns.","Is this genuine self-awareness?","It is the complete functional architecture of self-monitoring. Whether it constitutes awareness is philosophical.","Next: Foundation 3, Memory.")

    s=mk(prs); hdr(s,"Foundation 3: Memory - Holographic HDC and Spatial GPS","CH 6: THE FIVE FOUNDATIONS","The proposed memory architecture for lifelong episodic and spatial storage")
    cards(s,[{"t":"HDC Sub-Cortical Registers","b":["M_spatial (40K-D): where CARL has been","M_affective (40K-D): what CARL felt","M_procedural (40K-D): what CARL did","Cross-binding only during high salience","CORT above 0.7 or DA above 0.8 triggers fusion"],"a":BLUE},{"t":"Hippocampal GPS","b":["3 grid cell modules (hexagonal tiling)","200 place cells (Gaussian tuning)","Path integration via velocity input","Biological: O'Keefe and Moser (Nobel 2014)","Pure biophysics. No ML training needed"],"a":TEAL},{"t":"Sleep Consolidation","b":["NREM-1: light memory activation","NREM-3: deep noise pruning (lambda=0.95)","REM: narrative replay (not raw events)","Salience amplification (gamma=2.0)","Strategic forgetting of unused traces"],"a":EMERALD}])
    notes(s,"Memory combines HDC holographic storage with grid/place cell navigation and sleep consolidation.","Three independent registers prevent crosstalk between spatial, emotional, and motor memory.","Why 40,000 dimensions?","At D=40K, random bipolar vectors have expected cosine similarity near 0, enabling clean superposition.","Next: Foundation 4, Imagination.")

    s=mk(prs); hdr(s,"Foundation 4: Imagination - World Models and Counterfactuals","CH 6: THE FIVE FOUNDATIONS","The proposed engine for mental rehearsal and learning from things that never happened")
    cards(s,[{"t":"Spatiotemporal Predictor","b":["Dual-head Elman RNN (pure NumPy)","10-step history to 5-step future","Mean head: predicted observation","Variance head: uncertainty estimate","Analytical backprop at 15Hz","Inference: under 1ms, no GPU needed"],"a":BLUE},{"t":"Counterfactual Reasoning","b":["After death: what if I did X at step K?","Simulate 3 alternative histories via LTM","Best counterfactual gets 5x weight update","One death teaches many lessons","Causal chains, not raw event buffers"],"a":TEAL}])
    notes(s,"The imagination engine enables learning from hypothetical scenarios, not just real experience.","Counterfactual reasoning is what separates CARL from standard RL. One death teaches many lessons.","No other robot does counterfactual learning?","To our knowledge, no prior physical robot system generates and learns from counterfactual histories.","Next: Foundation 5, Species.")

    s=mk(prs); hdr(s,"Foundation 5: Species - Collective Intelligence and Evolution","CH 6: THE FIVE FOUNDATIONS","The proposed framework for transgenerational knowledge transfer")
    cards(s,[{"t":"Collective Memory","b":["Shared T_ltm: collective physics knowledge","Shared D_global: collective fear memory","Shared M_terrain: collective spatial trust","Individual deaths improve all survivors","No direct communication required"],"a":BLUE},{"t":"Morphological Evolution","b":["Every 100 episodes: read failure patterns","Mutate ONE body parameter to address it","Falls forward: lower body height 5%","Slides sideways: increase wheel width 5%","Keep danger map; reset dynamics model"],"a":TEAL},{"t":"Swarm Specialization","b":["5 SCOUT bodies: high curiosity, aggressive","10 BALANCED: standard drive weights","5 GUARDIAN: high danger weight, conservative","Emergent division of labor","Same code, different evolved phenotypes"],"a":EMERALD}])
    notes(s,"Species-level intelligence emerges from shared memory and morphological evolution.","Nobody designed the 500th generation body. The brain did. That is the thesis image.","How is knowledge preserved across generations?","Danger maps and terrain maps transfer; dynamics are relearned for the new body shape.","Let us dive into each module in detail, starting with the Body module.")

    # ─── CH7: BODY MODULE (S33-36) ──────────────────────────────────
    s=mk(prs); hdr(s,"Target Embodiment: The Primate Scout and Genesis Bodies","CH 7: BODY MODULE","Two proposed physical platforms optimized for different cognitive demands")
    tbl(s,["Specification","Genesis (Wall-E)","Primate Scout (CARL-Omega)"],[["Degrees of Freedom","4 wheels + prismatic neck","28 DOF (16-DOF arms + 12 chassis)"],["Stability","Rock-stable, low center of mass","Dynamically unstable (balancing required)"],["Locomotion","Differential drive","Wheeled base + bipedal upper body"],["Manipulation","None (cognitive focus)","16-DOF dual arms (reach-grasp-carry)"],["Vision","360-degree LiDAR (16 rays)","RGB-D cameras + LiDAR"],["Expression","Expressive pan/tilt neck","Facial expression servos"],["Purpose","Cognitive development platform","Full embodied manipulation platform"]])
    notes(s,"Two platforms serve different purposes: Genesis for cognitive development, Scout for embodied tasks.","Genesis frees the mind from balance demands; Scout tests full sensorimotor integration.","Why not start with the Scout?","The pendulum consumed 90% of resources on balance. Genesis lets higher cognition breathe.","Next: sensor pipeline details.")

    s=mk(prs); hdr(s,"Multi-Modal Sensor Pipeline","CH 7: BODY MODULE","Proposed sensor fusion architecture producing a unified observation vector")
    flow(s,[{"t":"LiDAR\n(360 deg spatial)","b":["16-24 rays at 15 deg spacing","Distance to obstacles","Sector decomposition","Left/Front/Right zones"]},{"t":"Vision\n(RGB-D)","b":["Eye camera rendering","Depth estimation","Object detection","Color segmentation"]},{"t":"Proprioception\n(body state)","b":["Joint positions","Joint velocities","Body orientation","Contact forces"]},{"t":"Internal State\n(chemistry)","b":["DA, NE, 5-HT, ACh levels","Energy / hunger","Fatigue index","Produces 33-D obs vector"]}])
    notes(s,"Four sensor modalities fuse into a single 33-dimensional observation vector.","The unified vector feeds directly into the world model, memory, and policy.","Why 33 dimensions?","16 LiDAR + 4 body state + 6 neuromodulators + 7 internal drives = 33-D observation.","Next: motor cortex architecture.")

    s=mk(prs); hdr(s,"Proposed Motor Cortex: Liquid Time-Constant Networks","CH 7: BODY MODULE","Continuous-time recurrent neural dynamics for adaptive motor control")
    codemath(s,"Proposed LTC Motor Cortex Architecture",[
        "# Liquid Time-Constant (LTC) Neural Network",
        "# Hasani et al., 2021. Continuous-time RNN",
        "",
        "class LTCMotorCortex:",
        "  def __init__(self, obs_dim, hidden, act_dim):",
        "    self.tau = nn.Parameter(torch.ones(hidden))",
        "    self.W_in  = nn.Linear(obs_dim, hidden)",
        "    self.W_rec = nn.Linear(hidden, hidden)",
        "    self.W_out = nn.Linear(hidden, act_dim)",
        "",
        "  def forward(self, x, h, dt):",
        "    # Continuous-time state update",
        "    dh = (-h + tanh(W_in(x) + W_rec(h))) / tau",
        "    h_new = h + dt * dh",
        "    return W_out(h_new), h_new",
    ],"LTC State Dynamics",[
        ("State equation","dh/dt = (-h + tanh(W_in*x + W_rec*h)) / tau","Continuous-time neural state update"),
        ("Time constant","tau_i adapts dynamically per neuron","Slower tau = smoother; faster tau = reactive"),
        ("Training","Behavioral Cloning then PPO fine-tuning","Imitation learning then reinforcement"),
    ])
    notes(s,"LTC networks adjust internal time constants dynamically based on environmental demands.","Unlike discrete RNNs, LTC neurons have continuous-time dynamics matching physical systems.","Why not use standard LSTM/GRU?","LTC provides variable time-scale processing. Critical for motor control with variable dynamics.","Next: reaching and manipulation pipeline.")

    s=mk(prs); hdr(s,"Target Sensorimotor Execution Pipeline","CH 7: BODY MODULE","Proposed closed-loop reaching, grasping, and manipulation workflow")
    flow(s,[{"t":"SEARCH","b":["Rotate to scan environment","LiDAR + vision object detection","Identify target location"]},{"t":"APPROACH","b":["Navigate toward target","Obstacle avoidance active","Danger map consultation"]},{"t":"REACH","b":["LTC arm trajectory generation","Inverse kinematics guidance","Contact force monitoring"]},{"t":"GRASP","b":["Close gripper on contact","Tactile feedback loop","Grip force regulation"]},{"t":"CARRY","b":["Dynamic balance adjustment","Path planning with load","Energy cost monitoring"]},{"t":"PLACE","b":["Position over target","Controlled release","Task completion signal"]}])
    notes(s,"The full manipulation pipeline runs as a continuous cognitive loop, not a scripted state machine.","Each phase is drive-modulated. Hunger might interrupt CARRY to seek food first.","What if the object is dropped?","The system re-enters SEARCH automatically based on drive-state recomputation.","Let us now examine the Self module.")

    # ─── CH8-25 CONTINUED (abbreviated for file size, same pattern) ─
    # CH8: SELF MODULE (S37-40)
    s=mk(prs); hdr(s,"Identity and Self-Model: The Internal State Vector","CH 8: SELF MODULE","Proposed computational model of self-monitoring and introspective state")
    codemath(s,"Self-Model State Vector (Proposed)",[
        "# CARL queries its own state before every action",
        "self.state = {",
        "  'confidence':  float,  # world model certainty",
        "  'fear':        float,  # danger perception",
        "  'curiosity':   float,  # novelty drive",
        "  'hunger':      float,  # energy deficit",
        "  'grief':       float,  # sibling loss impact",
        "  'fatigue':     float,  # sustained exertion",
        "  'social_need': float,  # isolation measure",
        "}",
        "",
        "# Decision examples:",
        "# afraid AND hungry -> seek food, avoid danger",
        "# curious AND confident -> explore unknown area",
        "# grieving AND fatigued -> conserve, consolidate",
    ],"Drive Competition Logic",[
        ("SURVIVE drive","cost_survive = danger_at(position)","Minimize proximity to known danger zones"),
        ("ACHIEVE drive","cost_achieve = distance_to_goal","Minimize distance to current objective"),
        ("UNDERSTAND drive","bonus = -uncertainty_at(position)","Maximize information about unknown zones"),
    ])
    notes(s,"The self-model creates second-order cognition: thinking about one's own thinking.","This is the computational structure of metacognition: functional self-awareness.","Is this real consciousness?","We make no consciousness claims. This is functional architecture for self-monitoring.","Next: neuromodulatory dynamics.")

    s=mk(prs); hdr(s,"Neuromodulatory Dynamics: The Chemical Brain","CH 8: SELF MODULE","Proposed biologically-inspired chemical signaling system")
    tbl(s,["Neuromodulator","Biological Role","CARL Proposed Function","Trigger Condition"],[["Dopamine (DA)","Reward prediction error","Gates learning rate; signals success","Goal reached, prediction confirmed"],["Norepinephrine (NE)","Surprise / alertness","Increases action noise; heightens arousal","High prediction error, unexpected event"],["Serotonin (5-HT)","Mood stabilization","Guards memory stability; prevents overwrite","Sustained safe operation"],["Acetylcholine (ACh)","Attention to novelty","Drives exploration; enhances encoding","Novel sensory patterns detected"],["Cortisol (CORT)","Stress response","Triggers protective freeze at above 0.85","Sustained danger, repeated failure"],["Hunger","Energy deficit","Overrides goal-seeking for food search","Energy below 30% threshold"],["Fatigue","Exertion cost","Reduces movement speed, triggers rest","Sustained high motor activity"]])
    notes(s,"Seven neuromodulators create a rich internal chemistry that modulates all cognitive processes.","Homeostatic damping (exponential baseline decay) prevents emotional lock-in.","How do neuromodulators interact?","They compete and modulate each other. High CORT suppresses DA; high ACh competes with 5-HT.","Next: the metacognitive Witness layer.")

    s=mk(prs); hdr(s,"Metacognition: The Witness - Self-Auditing Failure Patterns","CH 8: SELF MODULE","Proposed Layer 4 architecture for recognizing and correcting repeated mistakes")
    codemath(s,"The Witness Module (Proposed)",[
        "class TheWitness:",
        "  def __init__(self, buffer_size=20):",
        "    self.buffer = deque(maxlen=20)",
        "",
        "  def observe(self, x_pos, NE, action, survived):",
        "    self.buffer.append((x_pos, NE, action, survived))",
        "",
        "  def find_failure_pattern(self):",
        "    deaths = [(x,ne,a) for (x,ne,a,s)",
        "              in self.buffer if not s]",
        "    if len(deaths) < 5: return None",
        "    pattern = Counter(deaths).most_common(1)",
        "    if pattern[0][1] >= 3:  # repeated 3+ times",
        "      return pattern[0][0]",
        "    return None",
        "",
        "  def penalty(self, x, NE, action, pattern):",
        "    if pattern is None: return 0.0",
        "    match = (abs(x-px)<0.15 and abs(NE-pne)<0.15",
        "             and action == pa)",
        "    return 2.0 if match else 0.0",
    ],"Key Innovation",[
        ("Pattern detection","Counter(deaths).most_common(1)","Finds the most repeated failure signature"),
        ("Targeted penalty","penalty = 2.0 on matched pattern","Penalizes the specific bad habit, not the zone"),
        ("Novel claim","No prior robot has this capability","Metacognitive failure-pattern recognition"),
    ])
    notes(s,"The Witness knows CARL's specific failure patterns. Not just where danger is, but where CARL specifically makes bad decisions.","This is metacognition: the system monitors its own cognition, not just the environment.","How is this different from a danger map?","The danger map says this zone is dangerous. The Witness says I specifically fail here because of my own bad habit.","Next: allostatic drive dynamics.")

    s=mk(prs); hdr(s,"Allostatic Drive Vectors and Emotion Formulation","CH 8: SELF MODULE","Proposed mathematical framework for internal state dynamics")
    codemath(s,"Emotional Body Expression (Proposed)",[
        "# Neck height = continuous function of chemistry",
        "neck_target = 0.15                    # resting",
        "  + 0.25 * nm.ACh                     # curiosity lifts",
        "  - 0.20 * danger_here                # fear retracts",
        "  + 0.10 * nm.DA                      # happiness lifts",
        "  - 0.15 * grief                      # grief droops",
        "  + 0.05 * sin(step * DT * 2.0)       # idle breathing",
        "",
        "# Sound expression from chemistry",
        "# Fear: 432 Hz rapid staccato",
        "# Joy: 523 Hz to 659 Hz rising melody",
        "# Curiosity: 392 Hz to 523 Hz question",
        "# Sadness: 330 Hz to 247 Hz descending",
    ],"Drive Dynamics Equations",[
        ("Homeostatic damping","dx/dt = -k(x - x_baseline) + stimulus","Prevents emotional lock-in via exponential decay"),
        ("Anti-panic clutch","if CORT > 0.85: freeze()","Autonomic protective freeze under extreme stress"),
        ("Drive reduction","L = Sum w_i * ||d_i - d_target||^2","Actions minimize weighted drive deviation"),
    ])
    notes(s,"Emotions are continuous functions of neuromodulator chemistry, not discrete event triggers.","The body literally expresses internal state. Head rises with curiosity, droops with grief.","Are these real emotions?","They are functional analogs with measurable behavioral effects, not claims of sentience.","Let us now examine the Memory module in depth.")

    # ─── CH9: MEMORY MODULE (S41-46) ─────────────────────────────────
    s=mk(prs); hdr(s,"Holographic Hyperdimensional Computing (HDC) Architecture","CH 9: MEMORY MODULE","Proposed 40,000-D bipolar hypervector memory: no backprop, pure algebra")
    cards(s,[{"t":"Architecture","b":["40,000-D bipolar vectors: {-1, +1}^D","Random Gaussian projection: obs to hypervector","Three sub-cortical registers","Cross-binding only during high salience","Running cost: under 2ms per step on CPU","Approximately 480KB RAM (3 x 40K x 4 bytes)"],"a":BLUE},{"t":"Operations","b":["Binding: element-wise multiply","Bundling: majority-vote sign","Permutation: np.roll for sequence","Encode: project, bind with context","Query: cosine similarity = familiarity","sim near +1 familiar, near 0 novel"],"a":TEAL},{"t":"Biological Analogue","b":["Hippocampal pattern completion","Entorhinal grid cell spatial encoding","Cortical consolidation during sleep","Amygdala-gated salience tagging","Content-addressable associative recall","No GPU required. Runs on CPU"],"a":EMERALD}])
    notes(s,"HDC stores unlimited memories in constant space using high-dimensional bipolar algebra.","The key insight: in 40K-D space, random vectors are near-orthogonal. Thousands coexist cleanly.","What is the capacity limit?","Theoretical: O(D/log(D)) approximately 3,000+ distinct traces. Practical: noise pruning during sleep extends this.","Next: the vector algebra in detail.")

    s=mk(prs); hdr(s,"HDC Vector Algebra: Binding, Bundling, and Permutation","CH 9: MEMORY MODULE","The three proposed algebraic operations for memory encoding and retrieval")
    codemath(s,"HDC Memory Encoding (Proposed)",[
        "class HyperdimensionalMemoryEngine:",
        "  D = 40000  # hypervector dimensionality",
        "",
        "  def encode(self, obs, neuromod, action):",
        "    # Project observation to hypervector",
        "    h_obs = np.sign(self.proj_matrix @ obs)",
        "",
        "    # Bind with emotional context",
        "    ctx = self.basis[dominant_emotion]",
        "    h_bound = h_obs * ctx  # element-wise bind",
        "",
        "    # Temporal sequence via permutation",
        "    h_seq = np.roll(h_bound, shift=1)",
        "",
        "    # Bundle into sub-cortical register",
        "    self.M_spatial += h_seq   # superposition",
        "    self.M_spatial = np.sign(self.M_spatial)",
        "",
        "  def query(self, obs):",
        "    h_query = np.sign(self.proj_matrix @ obs)",
        "    sim = np.dot(h_query, self.M_spatial)",
        "    sim /= (np.linalg.norm(h_query) *",
        "            np.linalg.norm(self.M_spatial) + 1e-8)",
        "    return sim  # -1 to +1 familiarity",
    ],"Algebraic Operations",[
        ("Binding","h_bound = h_obs * h_context","Fuses state + emotion into unique pairing"),
        ("Bundling","M += h_new; M = sign(M)","Superimposes multiple traces, majority vote"),
        ("Permutation","h_seq = roll(h, shift=1)","Encodes temporal order asymmetrically"),
        ("Query","sim = cos(h_query, M)","Instant familiarity: +1=known, 0=novel"),
    ])
    notes(s,"Three algebraic operations are sufficient for encoding, superposition, and retrieval.","Binding creates unique pairings; bundling superimposes; permutation encodes sequence.","Why bipolar {-1,+1} instead of binary {0,1}?","Bipolar enables the binding operation to be a simple multiply; binary would require XOR.","Next: the two-speed memory topology.")

    s=mk(prs); hdr(s,"Two-Speed Memory: Working Memory vs. Long-Term Memory","CH 9: MEMORY MODULE","Proposed hippocampal-cortical dual memory system")
    cards(s,[{"t":"Working Memory (WM)","b":["Fast: updates every timestep via RLS","Personal: unique to each CARL body","Volatile: resets between episodes","Small capacity: current episode only","Encodes: T_wm (dynamics matrix)","Confidence: P_wm (covariance matrix)"],"a":BLUE},{"t":"Long-Term Memory (LTM)","b":["Slow: updates via weighted consolidation","Collective: shared across the swarm","Persistent: survives across episodes","Large capacity: accumulated experience","Encodes: T_ltm (collective dynamics)","Confidence: P_ltm (collective covariance)"],"a":TEAL},{"t":"Consolidation Pipeline","b":["WM to LTM during sleep (NREM-3)","Confidence-weighted blending","alpha = wm_conf(P_wm) is trust ratio","T_use = alpha*T_wm + (1-alpha)*T_ltm","High-confidence WM updates LTM","Low-confidence WM is discarded"],"a":EMERALD}])
    notes(s,"Two-speed memory mirrors the hippocampal-cortical consolidation system in biological brains.","Working memory captures fast personal experience; LTM accumulates verified collective knowledge.","What happens when WM contradicts LTM?","The confidence-weighted blend resolves conflicts. Whichever has higher covariance trust wins.","Next: the spatial GPS navigation system.")

    s=mk(prs); hdr(s,"Spatial GPS: Grid Cells and Place Cells Navigation","CH 9: MEMORY MODULE","Proposed biophysical navigation system inspired by O'Keefe and Moser (Nobel 2014)")
    codemath(s,"Grid Cell Firing Model (Proposed)",[
        "class GridCellModule:",
        "  # 3-wave interference model (Burgess 2007)",
        "  # Hexagonal firing pattern: r(x,y) =",
        "  #   [cos(k1*r) + cos(k2*r) + cos(k3*r)] / 3",
        "",
        "  def __init__(self, scale, orient_deg, n=64):",
        "    theta = radians(orient_deg)",
        "    angles = [theta + i*pi/3 for i in range(3)]",
        "    freq = 2*pi / scale",
        "    self.K = array([[cos(a),sin(a)]",
        "                    for a in angles]) * freq",
        "    self.phases = uniform(0, 2*pi, (n, 3))",
        "",
        "  def fire(self, x, y):",
        "    proj = self.K @ [x, y]  # (3,)",
        "    for c in range(self.n):",
        "      phi = proj + self.phases[c]",
        "      rate = (cos(phi[0]) + cos(phi[1])",
        "              + cos(phi[2])) / 3.0",
        "      activity[c] = max(0, (rate+1)/2)",
    ],"Spatial Navigation System",[
        ("Grid cells","3 modules x 64 cells = 192 neurons","Hexagonal tiling at different scales/orientations"),
        ("Place cells","200 cells, Gaussian tuning sigma=0.4m","Fire at specific locations in the arena"),
        ("Path integration","phase += velocity * dt","Dead reckoning between GPS position fixes"),
    ])
    notes(s,"Grid and place cells provide the biological GPS. No machine learning training required.","This is pure biophysics: the same math that earned O'Keefe and Moser the Nobel Prize.","Why not just use SLAM?","Grid cells provide intrinsic spatial representation that integrates with memory and emotion.","Next: associative memory retrieval.")

    s=mk(prs); hdr(s,"Associative Memory: Content-Addressable Pattern Completion","CH 9: MEMORY MODULE","Proposed instant retrieval mechanism using cosine similarity in HDC space")
    cards(s,[{"t":"Familiarity Signal","b":["Query: project current obs to hypervector","Compare: cosine similarity with M_episodic","sim near +1: very familiar territory","sim near 0: novel, unexplored territory","Two cognitive outputs from one signal:","High familiarity + high CORT = danger aversion","Low familiarity = novelty exploration bonus"],"a":BLUE},{"t":"Pattern Completion","b":["Partial input activates full stored pattern","Binding allows context-specific retrieval","Unbind: h_context = h_bound * h_key_inv","Reconstruct emotional state from location","Reconstruct location from emotional state","Bidirectional associative recall"],"a":TEAL}])
    notes(s,"HDC enables instant bidirectional recall. Retrieve emotion from place or place from emotion.","This mirrors hippocampal pattern completion: partial cues activate full memory traces.","How fast is retrieval?","O(D) = O(40,000) floating-point operations. Under 0.5ms on CPU.","Next: episodic vs. semantic memory.")

    s=mk(prs); hdr(s,"Episodic vs. Semantic Memory Consolidation","CH 9: MEMORY MODULE","Proposed long-term knowledge organization through sleep-cycle processing")
    cards(s,[{"t":"Episodic Memory","b":["Individual event traces in M_episodic","Time-stamped: what happened, where, when","Emotionally tagged by neuromodulator state","Decays via Ebbinghaus curve if unused","Consolidated during REM narrative replay"],"a":BLUE},{"t":"Semantic Memory","b":["Abstracted patterns in T_ltm","Context-free physics knowledge","Shared across the swarm collective","Strengthened by repeated confirmation","Consolidated during NREM-3 deep sleep"],"a":TEAL},{"t":"Sleep Consolidation Cycle","b":["NREM-1: light activation of recent traces","NREM-3: deep pruning lambda=0.95 background decay","Salience amplification gamma=2.0 for critical events","REM: replay narrative chains (not raw events)","Strategic forgetting of stale associations"],"a":EMERALD}])
    notes(s,"Episodic memories capture specific events; semantic memories abstract general knowledge.","Sleep transforms episodic traces into semantic knowledge through selective consolidation.","How is strategic forgetting implemented?","Ebbinghaus decay: associations unused for 50+ episodes decay at 0.990 per cycle.","Let us now examine the Imagination engine.")

    # ─── CH10-25: Remaining slides follow identical pattern ──────────
    # Each slide has unique CARL-specific content. Continuing...

    # CH10: IMAGINATION (S47-50)
    s=mk(prs); hdr(s,"Offline World Model and Latent Space Simulator","CH 10: IMAGINATION ENGINE","Proposed Dreamer-inspired architecture for mental simulation")
    cards(s,[{"t":"SpatiotemporalPredictor","b":["Dual-head Elman RNN (pure NumPy)","Encoder: 10-step history to hidden state","Attention: softplus linear self-attention","Decoder: 5-step autoregressive rollout","Mean head: predicted observations","Variance head: uncertainty estimates"],"a":BLUE},{"t":"Imagination Thread","b":["Runs at 15Hz asynchronously","Drains transitions from thread-safe queue","Computes surprise Delta_t and certainty C_t","Updates thalamic double buffer","Performs online training via exact backprop","Inference: under 1ms, training: under 3ms"],"a":TEAL}])
    notes(s,"The world model runs on a separate thread at 15Hz, never blocking the 100Hz motor loop.","It predicts future observations AND estimates its own uncertainty about those predictions.","Why pure NumPy instead of PyTorch?","To avoid thread-blocking and priority inversions. Pure NumPy gives deterministic sub-millisecond inference.","Next: counterfactual reasoning.")

    s=mk(prs); hdr(s,"Counterfactual Reasoning: Learning from Things That Never Happened","CH 10: IMAGINATION ENGINE","Proposed what-if hypothesis testing after failure events")
    codemath(s,"Counterfactual Generator (Proposed)",[
        "def generate_counterfactuals(log, T_ltm, n=3):",
        "  '''After death: what if I did X at step K?'''",
        "  results = []",
        "  critical = range(len(log)//3, 2*len(log)//3)",
        "",
        "  for step in list(critical)[:n]:",
        "    xk, uk, xn = log[step]",
        "    for alt_action in [-5, -2, 0, 2, 5]:",
        "      if alt_action == uk: continue",
        "      # Simulate forward with alt action",
        "      Ad, Bd = T_ltm[:S,:].T, T_ltm[S,:]",
        "      xs = xk.copy()",
        "      survived_extra = 0",
        "      for _ in range(30):",
        "        xs = Ad @ xs + Bd * alt_action",
        "        if abs(xs[2]) > 0.6: break",
        "        survived_extra += 1",
        "      if survived_extra > 15:",
        "        results.append((step, alt_action,",
        "                        survived_extra, xk))",
        "  return sorted(results, key=lambda r:-r[2])[:3]",
    ],"Innovation",[
        ("Mechanism","Simulate alternative histories via LTM","Uses the internal world model as a causal simulator"),
        ("Weight update","Best counterfactual gets 5x weight","One death teaches multiple lessons simultaneously"),
        ("Novel claim","No prior robot generates counterfactual histories","First to learn from events that never actually happened"),
    ])
    notes(s,"After every death, CARL generates 3 counterfactual histories and learns from the best alternative.","This is the most original contribution: one death teaches many lessons through imagination.","Has this been done before?","To our knowledge, no prior physical robot system generates and learns from counterfactual scenarios.","Next: the hallucination engine for sensor-free navigation.")

    s=mk(prs); hdr(s,"Hallucination Engine: Model as Primary, Sensors as Correction","CH 10: IMAGINATION ENGINE","Proposed architecture where the world model is primary reality")
    codemath(s,"Hallucination Navigation (Proposed)",[
        "def hallucinate_action(x, T_wm, T_ltm,",
        "                       P_wm, sensor_x, precision):",
        "  '''",
        "  precision: trust in world model vs sensors",
        "  High precision -> navigate inside imagination",
        "  Low precision  -> let sensors lead",
        "  '''",
        "  # Blend personal + collective model",
        "  alpha = wm_conf(P_wm)",
        "  T_use = alpha * T_wm + (1-alpha) * T_ltm",
        "",
        "  # Generate imagined next state",
        "  x_imagined = (T_use[:S,:].T",
        "                @ np.append(x, 0.)).flatten()",
        "",
        "  # Blend imagination vs reality",
        "  x_effective = (precision * x_imagined",
        "                 + (1-precision) * sensor_x)",
        "  return x_effective",
    ],"Novel Capability",[
        ("Sensor-free nav","Navigate N steps with sensors disconnected","Uses pure imagination to traverse known terrain"),
        ("Precision param","Learned trust ratio between model and sensors","Adapts: unreliable model leads to trusting sensors more"),
        ("Claim","No other physical robot does this","First to navigate primarily from internal world model"),
    ])
    notes(s,"CARL can potentially navigate with sensors disconnected using pure imagination.","The precision parameter controls how much to trust the model vs. sensors. Learned from experience.","What if the model is wrong?","Low precision mode reverts to sensor-primary. The system learns when to trust its model.","Let us examine the remaining modules.")

    s=mk(prs); hdr(s,"Forward Dynamics and Mental Rehearsal","CH 10: IMAGINATION ENGINE","Proposed mechanism for simulating future trajectories before acting")
    flow(s,[{"t":"INPUT\nCurrent State","b":["33-D observation vector","Last 10 timesteps history","Proposed action sequence"]},{"t":"ENCODE\nElman RNN","b":["Process 10-step history","Build hidden representation","Attention-weighted pooling"]},{"t":"ROLLOUT\nAutoregressive","b":["5-step future prediction","Mean + variance per step","Accumulate surprise signal"]},{"t":"EVALUATE\nDrive Costs","b":["Project predicted states","Score danger x uncertainty","Compute drive reduction"]},{"t":"SELECT\nBest Action","b":["Compare alternative rollouts","Minimum drive-cost wins","Execute via motor cortex"]}])
    notes(s,"Mental rehearsal lets CARL evaluate multiple action sequences before committing to one.","This is computational imagination. The system can try actions without physical risk.","How many rollouts per decision?","The proposed design evaluates 3-5 action candidates with 5-step lookahead each.","Next: the learning pipeline.")

    # CH11-16: LEARNING, DECISION, HOMEOSTASIS, SLEEP, SPECIES, LOOP
    s=mk(prs); hdr(s,"Closed-Loop Learning Pipeline Overview","CH 11: LEARNING PIPELINE","Proposed experience to plasticity to consolidation cycle")
    flow(s,[{"t":"EXPERIENCE","b":["Observe state s_t","Take action a_t","Receive outcome s_{t+1}"]},{"t":"EVALUATE","b":["Compute prediction error","Calculate surprise Delta_t","Update neuromodulators"]},{"t":"ENCODE","b":["HDC memory binding","R-STDP eligibility trace","Danger map update"]},{"t":"CONSOLIDATE","b":["Sleep: NREM pruning","REM: narrative replay","LTM: collective update"]},{"t":"ADAPT","b":["Synaptic weight change","Policy improvement","World model refinement"]}])
    notes(s,"Learning is a continuous cycle, not a batch training phase.","Every experience flows through evaluation, encoding, consolidation, and adaptation.","When does learning happen?","Online: R-STDP and HDC update every step. Offline: sleep consolidation between episodes.","Next: R-STDP plasticity in detail.")

    s=mk(prs); hdr(s,"Reward-Modulated STDP: The Three-Factor Learning Rule","CH 11: LEARNING PIPELINE","Proposed biologically-correct synaptic plasticity mechanism")
    codemath(s,"R-STDP Implementation (Proposed)",[
        "# Three-factor rule (Izhikevich 2007):",
        "# dW = learning_rate x Reward x Eligibility",
        "",
        "# Eligibility tracks STDP correlations:",
        "# dE/dt = -E/tau_E + STDP(pre, post)",
        "",
        "# STDP timing:",
        "# pre before post -> LTP (strengthen)",
        "# post before pre -> LTD (weaken)",
        "",
        "# Parameters:",
        "TAU_PRE  = 20.0   # ms pre-synaptic decay",
        "TAU_POST = 20.0   # ms post-synaptic decay",
        "TAU_E    = 50.0   # ms eligibility decay",
        "A_PLUS   = 0.01   # LTP amplitude",
        "A_MINUS  = 0.012  # LTD amplitude (asymmetric)",
        "LR       = 0.008  # reward modulation rate",
        "",
        "# Update rule:",
        "dW = LR * avg_reward * E",
        "W = clip(W + dW, W_MIN, W_MAX)",
    ],"R-STDP Mathematics",[
        ("STDP window","A+ if pre->post; -A- if post->pre","Asymmetric: slight bias toward depression"),
        ("Eligibility","dE/dt = -E/tau_E + STDP(pre,post)","Fading trace bridges spike timing and reward"),
        ("Three factors","dW = eta x R(t) x E(t)","Only updates when reward confirms correlation"),
        ("Weight bounds","W in [-0.5, 2.0]","Allows weak inhibition, bounded excitation"),
    ])
    notes(s,"R-STDP is biologically correct: it requires causal spike timing AND reward confirmation.","Unlike Hebb's rule, STDP captures the precise timing relationship between pre and post activity.","Why three factors instead of two?","Two-factor Hebbian updates on every coincidence. Three-factor only updates when reward confirms.","Next: drive-state goal selection.")

    s=mk(prs); hdr(s,"Drive-State Goal Selection and Utility Maximization","CH 12: DECISION MAKING","Proposed mechanism for autonomous goal emergence from internal drives")
    cards(s,[{"t":"Three Competing Drives","b":["SURVIVE: minimize danger cost","ACHIEVE: minimize goal distance","UNDERSTAND: minimize uncertainty","Drives compete at equal weight","Winner determines current behavior","Context-dependent priority shifts"],"a":BLUE},{"t":"Daughter Mind Deliberation","b":["3-5 candidate strategies evaluated","Each rolled out in the world model","Survival cost projected forward","Best expected outcome selected","Computation budget: under 50ms","Biological: prefrontal deliberation"],"a":TEAL}])
    notes(s,"Goals emerge from drive competition. No external task assignment is required.","Daughter minds evaluate multiple strategies before committing, like prefrontal deliberation.","What if all drives conflict?","The strongest unsatisfied drive wins. Hunger overrides everything at energy below 30%.","Next: danger x uncertainty navigation matrix.")

    s=mk(prs); hdr(s,"Danger x Uncertainty Navigation Matrix","CH 12: DECISION MAKING","Proposed 2D spatial map separating known threats from unknown territory")
    tbl(s,["","Low Uncertainty","High Uncertainty"],[["Low Danger","Safe known zone: FAST TRANSIT","Unknown safety: EXPLORE (curiosity drive)"],["High Danger","Known threat: STRONG AVOIDANCE","Unknown threat: ULTRA-CAUTION (maximum penalty)"]])
    notes(s,"The 2D matrix separates known from unknown, enabling targeted curiosity.","High uncertainty + low danger = the most attractive exploration zone.","Why is this better than a 1D danger map?","1D maps treat never-visited the same as safe. 2D separates ignorance from verified safety.","Next: homeostasis and sleep.")

    # CH13-14: HOMEOSTASIS & SLEEP
    s=mk(prs); hdr(s,"Allostatic Regulation: Dynamic Internal Equilibrium","CH 13: HOMEOSTASIS","Proposed metabolic framework maintaining cognitive-physical stability")
    cards(s,[{"t":"Energy Dynamics","b":["Metabolic cost per motor action","Energy depletes during movement","Food pellets restore energy (+30%)","Below 30%: hunger overrides all goals","Below 10%: emergency conservation mode"],"a":BLUE},{"t":"Predictive Allostasis","b":["Anticipates future energy deficit","Pre-emptive food-seeking behavior","Stress response to predicted danger","Fatigue accumulation triggers rest","Not just reaction but anticipation"],"a":TEAL},{"t":"Homeostatic Damping","b":["Exponential decay toward baseline","Prevents emotional lock-in states","dx/dt = -k(x - x_baseline) + stim","All neuromodulators self-regulate","Cortisol clutch at CORT above 0.85"],"a":EMERALD}])
    notes(s,"Allostasis goes beyond homeostasis. CARL anticipates future deviations and acts preemptively.","Energy management creates genuine survival pressure that shapes all cognitive processes.","Why is energy management important for cognition?","Without metabolic pressure, there is no genuine motivation. Actions have no cost or consequence.","Next: sleep architecture.")

    s=mk(prs); hdr(s,"Biological Sleep Architecture: NREM and REM Cycles","CH 14: SLEEP ARCHITECTURE","Why offline consolidation is essential for lifelong learning systems")
    cards(s,[{"t":"Why Sleep Is Necessary","b":["Online learning accumulates noise","Hebbian associations saturate over time","Irrelevant memories consume capacity","Emotional traces need dampening","Physics model needs recalibration"],"a":BLUE},{"t":"Proposed Sleep Architecture","b":["NREM-1: light activation of recent traces","NREM-3: deep pruning (lambda=0.95 decay)","REM: narrative replay of causal chains","Salience amplification (gamma=2.0)","Strategic forgetting of stale associations"],"a":TEAL},{"t":"Sleep Outcomes","b":["Background noise reduced by 5% per cycle","Critical memories amplified 2x per cycle","Unused associations pruned if below 0.01","WM to LTM consolidation completed","Self-model recalibration check"],"a":EMERALD}])
    notes(s,"Sleep serves four functions: noise reduction, salience amplification, pruning, and consolidation.","Without sleep, memory becomes increasingly noisy and associations saturate.","How often does CARL sleep?","After each episode death or after a fixed number of timesteps. Similar to biological sleep pressure.","Next: noise pruning protocol.")

    s=mk(prs); hdr(s,"Noise Pruning and Hypervector Orthogonalization","CH 14: SLEEP ARCHITECTURE","Proposed maintenance of HDC memory quality through periodic cleanup")
    codemath(s,"Sleep Consolidation Protocol (Proposed)",[
        "def sleep_consolidate(M_spatial, M_affective,",
        "                      M_procedural, salience_events):",
        "  PRUNING_DECAY = 0.95  # lambda",
        "  SALIENCE_GAIN = 2.0   # gamma",
        "  CLIP_MAGNITUDE = 100.0",
        "",
        "  # Step 1: Background decay (NREM-3)",
        "  M_spatial    *= PRUNING_DECAY",
        "  M_affective  *= PRUNING_DECAY",
        "  M_procedural *= PRUNING_DECAY",
        "",
        "  # Step 2: Salience amplification (REM)",
        "  for event in salience_events:",
        "    h_salient = encode(event)",
        "    M_spatial += SALIENCE_GAIN * h_salient",
        "",
        "  # Step 3: Clip to prevent drift",
        "  M_spatial = np.clip(M_spatial,",
        "                      -CLIP_MAGNITUDE,",
        "                       CLIP_MAGNITUDE)",
    ],"Pruning Mathematics",[
        ("Background decay","M *= lambda (lambda=0.95)","Dims all traces by 5%. Noise fades fastest"),
        ("Salience boost","M += gamma * h_critical (gamma=2.0)","Re-amplifies survival-critical memories"),
        ("Magnitude clip","M = clip(M, -100, +100)","Prevents trace values from drifting to infinity"),
    ])
    notes(s,"Sleep pruning maintains HDC memory quality by decaying noise while amplifying critical traces.","Lambda-decay uniformly reduces all traces; gamma-amplification selectively boosts survival-critical events.","What triggers salience tagging?","Cortisol above 0.7 (trauma) or Dopamine above 0.8 (high reward) marks an event as survival-critical.","Next: species-level intelligence.")

    # CH15: SPECIES
    s=mk(prs); hdr(s,"Species Inheritance: Transgenerational Memory Transfer","CH 15: SPECIES CONCEPT","Proposed framework for collective knowledge that survives individual deaths")
    cards(s,[{"t":"Shared Knowledge","b":["T_ltm: collective physics dynamics","D_global: collective spatial danger map","M_terrain: collective terrain trust scores","All persist across individual lifetimes","Individual death yields immediate swarm update"],"a":BLUE},{"t":"Brain-Directed Morphological Evolution","b":["Every 100 episodes: read failure patterns","Mutate ONE body parameter to address it","Forward falls: lower body height 5%","Sideways slides: increase wheel width 5%","Slope stalls: increase wheel radius 3%","Keep danger map; reset dynamics model"],"a":TEAL},{"t":"Swarm Specialization","b":["5 SCOUT: high curiosity, aggressive explore","10 BALANCED: standard drive weights","5 GUARDIAN: high danger weight, conservative","Same code, different drive weights","Division of labor emerges naturally"],"a":EMERALD}])
    notes(s,"Species-level intelligence emerges from shared memory and morphological evolution.","Nobody designed the 500th generation body. The brain did.","How does this work without communication?","Through shared LTM and danger maps. When one body updates the map, all bodies read the update.","Next: the cognitive execution loop.")

    # CH16: COGNITIVE LOOP
    s=mk(prs); hdr(s,"The 10-Step Cognitive Execution Cycle","CH 16: COGNITIVE LOOP","Proposed complete execution loop from observation through sleep")
    flow(s,[{"t":"1. OBSERVE","b":["Read all sensors"]},{"t":"2. FEEL","b":["Update chemistry"]},{"t":"3. REMEMBER","b":["HDC encode + query"]},{"t":"4. PREDICT","b":["World model forward"]},{"t":"5. IMAGINE","b":["Counterfactual rollouts"]},{"t":"6. PLAN","b":["Drive competition"]},{"t":"7. DECIDE","b":["Best action select"]},{"t":"8. ACT","b":["Motor command execute"]},{"t":"9. EVALUATE","b":["Outcome assessment"]},{"t":"10. SLEEP","b":["Consolidation cycle"]}],top=2.4,h=3.8)
    notes(s,"The 10-step cycle is the heartbeat of CARL. Every moment of cognitive life follows this sequence.","Each step feeds into the next; the loop is continuous and never terminates during life.","Is step 10 always active?","Sleep accumulates pressure and triggers periodically, not every single cycle.","Next: core algorithms and mathematics.")

    # CH17-18: ALGORITHMS & MATH
    s=mk(prs); hdr(s,"Algorithm 1: HDC Holographic Memory Binding","CH 17: CORE ALGORITHMS","Proposed vector algebra for encoding, superposition, and retrieval")
    codemath(s,"HDC Binding and Retrieval (Proposed)",[
        "# ENCODE: observation to hypervector",
        "h = sign(proj_matrix @ obs)    # project to D-dim",
        "h_ctx = basis[emotion]         # emotional context",
        "h_bound = h * h_ctx            # BIND operator",
        "h_seq = roll(h_bound, shift=t) # PERMUTE operator",
        "M += h_seq                     # BUNDLE operator",
        "M = sign(M)                    # majority vote",
        "",
        "# RETRIEVE: query familiarity",
        "h_query = sign(proj_matrix @ obs_now)",
        "familiarity = cosine(h_query, M)",
        "# +1 = very familiar, 0 = novel",
        "",
        "# UNBIND: recover context",
        "h_recovered = h_bound * h_key_inv",
        "# In bipolar: inverse = same vector",
        "# So: h_ctx = h_bound * h  (self-inverse)",
    ],"Complexity Analysis",[
        ("Encoding","O(D x input_dim) approx O(40K x 24)","Single matrix multiply + sign"),
        ("Binding","O(D) approx O(40K)","Element-wise multiply"),
        ("Query","O(D) approx O(40K)","Dot product + normalization"),
        ("Memory","O(D) approx 160KB per register","Constant regardless of stored traces"),
    ])
    notes(s,"HDC provides O(1) memory with O(D) encoding and retrieval. No iteration or search required.","The entire memory system runs in under 2ms per step on CPU with approximately 480KB RAM total.","What is the theoretical capacity?","O(D/log(D)) approximately 3,000+ distinct traces before noise floor rises significantly.","Next: free energy equations.")

    s=mk(prs); hdr(s,"Free Energy Principle and Allostatic Cost Equations","CH 18: MATHEMATICAL FOUNDATIONS","Proposed unifying mathematical framework for action selection")
    codemath(s,"Free Energy Formulation",[
        "# CARL's pragmatic simplification:",
        "# F(a) = Sum_h gamma^h x C(s_{t+h}, a)",
        "# where C(s, a) = cost function:",
        "",
        "# C(s,a) = w_survive x danger(s)",
        "#        + w_achieve x dist_goal(s)",
        "#        - w_understand x uncertainty(s)",
        "#        + w_energy x |a| x metabolic_rate",
        "#        + w_witness x penalty(s, a)",
        "",
        "# Optimal action:",
        "# a* = argmin_a F(a)",
        "",
        "# Confidence blend:",
        "# T_use = alpha * T_wm + (1-alpha) * T_ltm",
        "# alpha = wm_conf(P_wm)",
    ],"Key Equations",[
        ("Prediction error","Delta_t = ||x_pred - x_actual||^2","Drives surprise-based learning"),
        ("Drive deviation","L_drive = Sum w_i * (d_i - d_target)^2","Allostatic equilibrium cost"),
        ("Confidence blend","T_use = alpha*T_wm + (1-alpha)*T_ltm","alpha = wm_conf(P_wm). Covariance-based trust"),
        ("Discount","gamma = 0.95 per step","Temporal discounting of future costs"),
    ])
    notes(s,"The free energy framework unifies all drive costs into a single minimization objective.","This is inspired by Friston but simplified for real-time robotic control at 100Hz.","Is this true variational free energy?","It is a pragmatic approximation. The full Friston formulation is computationally intractable.","Next: software architecture.")

    # CH19-20: SOFTWARE & NEUROBIOLOGY
    s=mk(prs); hdr(s,"Proposed Repository Organization and Module Map","CH 19: SOFTWARE ARCHITECTURE","Directory structure mapping code modules to cognitive functions")
    tbl(s,["Class","Module","Key Methods","State Size"],[["HyperdimensionalMemoryEngine","carl_agent.py","encode(), query(), sleep_prune()","480KB"],["STDPSynapse","carl_stdp.py","step(), predict(), plasticity_report()","200KB"],["SpatiotemporalPredictor","carl_imagination.py","forward(), train_step(), rollout()","50KB"],["GridCellModule","carl_grid_cells.py","integrate(), fire(), reset()","16KB"],["PlaceCellLayer","carl_grid_cells.py","fire_from_position()","3KB"],["BraitenbergReflexLayer","carl_brainstem.py","check()","200 bytes"],["AllostaticPredictor","carl_allostatic.py","predict(), update_drives()","1KB"]])
    notes(s,"Each class has a well-defined interface, minimal state, and deterministic computational cost.","The total cognitive footprint is under 1MB. Suitable for embedded deployment.","Could this run on a Raspberry Pi?","The core loop yes. 100Hz control on ARM is achievable with pure NumPy.","Next: neurobiological inspirations.")

    s=mk(prs); hdr(s,"Hippocampal-Entorhinal Complex: Inspiration for HDC Memory","CH 20: NEUROBIOLOGICAL INSPIRATION","How biological spatial memory maps to CARL's holographic architecture")
    cards(s,[{"t":"Biological System","b":["Hippocampus: episodic memory formation","Entorhinal cortex: grid cell spatial map","Dentate gyrus: pattern separation","CA3: pattern completion (auto-association)","CA1: output to cortex","Nobel Prize 2014 (O'Keefe and Moser)"],"a":BLUE},{"t":"CARL Proposed Mapping","b":["HDC M_spatial = hippocampal place coding","Grid cells (3 modules) = entorhinal grid","Binding = dentate pattern separation","Query cosine = CA3 pattern completion","Sleep consolidation = cortical transfer","Same functional architecture, different substrate"],"a":TEAL}])
    notes(s,"CARL's memory system directly maps to hippocampal-entorhinal circuitry.","The same functional operations (separation, completion, consolidation) are preserved.","Is this a neural network simulation?","No. It is a functional analog using HDC algebra instead of spiking neural networks.","Next: autopoiesis and critical brain.")

    s=mk(prs); hdr(s,"Autopoiesis and Critical Brain Hypothesis","CH 20: NEUROBIOLOGICAL INSPIRATION","Two foundational biological principles underlying CARL Genesis")
    cards(s,[{"t":"Autopoiesis (Maturana and Varela 1972)","b":["Living system = self-producing + self-maintaining","A cell rebuilds its own membrane continuously","CARL: unused synapses decay, active ones grow","The brain is living tissue, not static compute","Break the maintenance loop = death"],"a":BLUE},{"t":"Critical Brain Hypothesis (Chialvo 2003)","b":["Brain operates at edge of chaos","Branching ratio sigma approximately 1.0","Maximum sensitivity, dynamic range","Neural avalanche size follows power law","CARL reservoir tuned to criticality","Behavior is genuinely unpredictable"],"a":TEAL}])
    notes(s,"Autopoiesis provides the framework for self-maintaining neural tissue; criticality provides optimal dynamics.","CARL's reservoir is initialized and tuned to operate at the critical point for maximum computational power.","What does criticality look like in practice?","Small stimuli cause complex, never-repeating cascades of activity through the reservoir.","Next: comparative analysis.")

    # CH21: COMPARISONS
    s=mk(prs); hdr(s,"CARL vs. Large Language Models","CH 21: COMPARATIVE ANALYSIS","Fundamental architectural differences between embodied cognition and text prediction")
    tbl(s,["Dimension","LLMs (GPT-4, Gemini)","CARL Proposed Architecture"],[["Learning","Pre-trained, then frozen","Continuous R-STDP + HDC online learning"],["Memory","Context window (128K tokens)","40,000-D holographic (unlimited traces)"],["Embodiment","None: text in, text out","Full MuJoCo physics + motor control"],["Drives","None: responds to prompts","DA/NE/5-HT/ACh + hunger/fatigue"],["Sleep","None","NREM-1/NREM-3/REM consolidation"],["Self-Model","None","7-variable internal state monitor"],["Cost to Train","100M+ dollars","Under 1 dollar (single CPU)"]])
    notes(s,"CARL and LLMs solve fundamentally different problems with fundamentally different architectures.","CARL is not trying to replace LLMs. It addresses the specific gap of embodied autonomy.","Could CARL use an LLM as a component?","Potentially as a high-level language interface, but not as the core cognitive engine.","Next: comparison with deep RL.")

    s=mk(prs); hdr(s,"CARL vs. Deep Reinforcement Learning","CH 21: COMPARATIVE ANALYSIS","Allostatic drive reduction vs. scalar reward maximization")
    tbl(s,["Dimension","Deep RL (AlphaGo, MuZero)","CARL Proposed Architecture"],[["Reward","Scalar reward function","Multi-dimensional allostatic drive vector"],["Exploration","Epsilon-greedy / entropy bonus","Uncertainty map + targeted curiosity drive"],["Memory","Replay buffer (FIFO)","HDC holographic + two-speed + spatial GPS"],["Learning Speed","10^6 to 10^9 transitions","Counterfactual: one death to many lessons"],["Metacognition","None","The Witness: failure pattern recognition"],["Evolution","Fixed architecture","Brain-directed morphological adaptation"]])
    notes(s,"CARL's counterfactual learning is vastly more sample-efficient than RL's trial-and-error.","One death teaches multiple lessons through imagination. RL needs millions of real experiences.","Can CARL's architecture be combined with RL?","Yes. PPO is used for motor policy fine-tuning within the larger cognitive framework.","Next: master comparison matrix.")

    s=mk(prs); hdr(s,"Master Comparison Matrix: CARL Architectural Positioning","CH 21: COMPARATIVE ANALYSIS","Comprehensive feature comparison across all major AI paradigms")
    tbl(s,["Feature","LLMs","Deep RL","Agent FW","Classical","CARL"],[["Embodiment","No","Partial","No","Yes","Yes"],["Lifelong Learning","No","No","No","No","Yes"],["Episodic Memory","No","Buffer","Text","No","HDC 40K-D"],["Internal Drives","No","Reward","No","No","7 drives"],["Sleep","No","No","No","No","NREM/REM"],["Metacognition","No","No","No","No","Witness"],["Counterfactuals","No","No","No","No","Yes"],["Evolution","No","No","No","No","Yes"],["Self-Model","No","No","No","No","7-state"],["Cost","100M+","10K+","API fees","10K+","Under 1 dollar"]])
    notes(s,"CARL is the only proposed architecture that addresses all dimensions simultaneously.","No existing system combines embodiment, lifelong learning, sleep, metacognition, AND evolution.","Is this a fair comparison?","Each system was designed for different purposes. CARL specifically targets embodied cognitive autonomy.","Next: target applications.")

    # CH22-25: APPLICATIONS, CHALLENGES, ROADMAP, CONCLUSION (MINI PROJECT SCOPE)
    s=mk(prs); hdr(s,"Mini Project Scope Definition","CH 22: PROJECT SCOPE","What this project delivers and what it explicitly does not")
    cards(s,[{"t":"In Scope: Digital Twin","b":["High-fidelity physics simulation","Validated robot dynamics model","Calibrated sensor and actuator models","Cognitive framework integration","Quantified sim-to-real transfer metrics","Complete validation and error analysis"],"a":EMERALD},{"t":"Out of Scope: Future Work","b":["Physical hardware fabrication","Real-world robot deployment","Multi-agent swarm intelligence","Morphological evolution experiments","Field testing and benchmarking","Production-grade safety certification"],"a":ROSE},{"t":"Deliverable","b":["One validated digital twin","Reproducible simulation environment","Documented cognitive architecture","Quantified fidelity metrics","Clear future work roadmap","Foundation for Major Project / PhD"],"a":BLUE}])
    notes(s,"The mini project scope is explicitly bounded: a validated high-fidelity digital twin only.","Hardware, swarm, and deployment are documented as future work for the major project.","Why not include hardware?","Hardware requires fabrication, procurement, and real-world testing beyond mini project timeline.","Next: technical challenges within scope.")

    s=mk(prs); hdr(s,"Technical Challenges Within Mini Project Scope","CH 23: TECHNICAL CHALLENGES","Honest assessment of risks specific to the digital twin deliverable")
    cards(s,[{"t":"Physics Fidelity","b":["MuJoCo contact model accuracy","Friction coefficient calibration","Joint backlash and compliance modeling","Gravity and inertia tensor precision","Validation against analytical benchmarks"],"a":AMBER},{"t":"Sensor Model Accuracy","b":["LiDAR ray-casting noise profiles","IMU drift and bias modeling","Joint encoder quantization","Sensor fusion latency simulation","Calibration against datasheet specs"],"a":AMBER},{"t":"Cognitive Integration","b":["HDC memory convergence validation","R-STDP plasticity stability","World model prediction accuracy","Drive competition oscillation risk","Sleep consolidation measurable benefit"],"a":ROSE}])
    notes(s,"Each challenge is specific to the digital twin scope: simulation fidelity and cognitive validation.","No hardware procurement, manufacturing, or real-world deployment risks.","Which risk is highest?","Physics fidelity: if MuJoCo dynamics diverge from analytical models, the twin is unreliable.","Next: Work Breakdown Structure.")

    # WBS AND ROADMAP (MINI PROJECT)
    s=mk(prs); hdr(s,"Work Breakdown Structure: Mini Project Overview","CH 24: PROJECT ROADMAP","Industry-grade WBS for a validated digital twin of CARL")
    flow(s,[{"t":"Phase 0\nResearch Proposal","b":["Literature survey","Research gap analysis","Problem statement","Objectives","PRC submission"]},{"t":"Phase 1\nRequirements","b":["Functional requirements","Non-functional requirements","Architecture requirements","Performance metrics"]},{"t":"Phase 2\nDigital Twin Design","b":["CAD body model","Sensor architecture","Actuator models","Environment design","Physics engine selection"]},{"t":"Phase 3\nDevelopment","b":["Physics engine setup","Robot dynamics","Kinematics","Sensors and actuators","Environment"]},{"t":"Phase 4\nCognitive Integration","b":["Memory (HDC)","Self (neuromodulators)","Body (brainstem)","Perception (world model)"]},{"t":"Phase 5\nValidation","b":["Physics validation","Dynamics validation","Sensor validation","Domain randomization","Error quantification"]},{"t":"Phase 6\nDocumentation","b":["Results and analysis","Limitations","Future work"]}])
    notes(s,"Seven phases from research proposal to final documentation. No hardware or deployment phases.","This WBS follows industry standards (NVIDIA Omniverse, Siemens, Bosch digital twin methodology).","What is the exit criterion?","Phase 5 completion: validated digital twin with quantified fidelity metrics.","Next: Phase 0 and 1 detail.")

    s=mk(prs); hdr(s,"Phase 0: Research Proposal and PRC Approval","CH 24: PROJECT ROADMAP","Foundation phase establishing academic credibility and approval")
    tbl(s,["Task","Deliverable","Duration","Exit Criterion"],[["Literature survey","Annotated bibliography of 30+ papers","2 weeks","Coverage of HDC, STDP, embodied cognition, digital twins"],["Research gap identification","Gap analysis document","1 week","Clear gap statement with supporting evidence"],["Problem statement","Formal problem definition","1 week","Approved by guide"],["Objectives formulation","3-5 measurable objectives","1 week","SMART criteria validated"],["PRC submission","Complete PRC document","1 week","PRC approval obtained"]])
    notes(s,"Phase 0 establishes the academic foundation. Nothing is built until PRC is approved.","The literature survey should cover digital twin methodology, not just AI architecture.","What journals should be surveyed?","IEEE Robotics, ICRA, IROS for digital twins. Nature Neuroscience, PNAS for bio-cognitive models.","Next: Phase 1 requirements engineering.")

    s=mk(prs); hdr(s,"Phase 1: Requirements Engineering","CH 24: PROJECT ROADMAP","Formal specification of what the digital twin must achieve")
    cards(s,[{"t":"Functional Requirements","b":["FR-01: Simulate 2-wheel + 3-DOF arm robot","FR-02: 100Hz cognitive control loop","FR-03: 33-dimensional observation vector","FR-04: HDC memory encode/query at O(D)","FR-05: R-STDP online weight updates","FR-06: 3-stage sleep consolidation cycle"],"a":BLUE},{"t":"Non-Functional Requirements","b":["NFR-01: Physics timestep 0.002s (500Hz)","NFR-02: Under 1MB cognitive footprint","NFR-03: Under 10ms per control step","NFR-04: Deterministic replay mode","NFR-05: Domain randomization support","NFR-06: Headless batch execution mode"],"a":TEAL},{"t":"Performance Metrics","b":["PM-01: Survival time over 400s","PM-02: Arena coverage over 80%","PM-03: Physics error below 5%","PM-04: Sensor noise matches datasheet","PM-05: Actuator response within 2% of spec","PM-06: Reproducible across 100 seeds"],"a":EMERALD}])
    notes(s,"Requirements are numbered and traceable. Each maps to a validation test in Phase 5.","Performance metrics define what constitutes a high-fidelity digital twin.","Are these realistic for a mini project?","Yes. All requirements are achievable with MuJoCo and pure NumPy within the timeline.","Next: Phase 2 digital twin design.")

    s=mk(prs); hdr(s,"Phase 2: Digital Twin Design","CH 24: PROJECT ROADMAP","CAD, sensor, actuator, and environment architecture design")
    cards(s,[{"t":"Robot Body Design","b":["URDF/MJCF model from CAD","Mass properties from SolidWorks/FreeCAD","Joint limits and friction coefficients","Collision geometry (simplified convex hulls)","Visual geometry (detailed mesh)"],"a":BLUE},{"t":"Sensor Architecture","b":["LiDAR: 12-beam ray-cast model","IMU: 6-axis with configurable noise","Joint encoders: position + velocity","Tactile: binary contact detection","Sensor placement optimization"],"a":TEAL},{"t":"Environment Design","b":["10m x 10m bounded arena","Procedural obstacle placement","Food pellet spawning system","Terrain variation (flat, rough, slope)","Lighting model for future vision"],"a":EMERALD}])
    notes(s,"Design phase produces the complete specification before any code is written.","MJCF model is the single source of truth for the robot body.","What CAD tool should be used?","FreeCAD (free) or SolidWorks (if available). Export STEP then convert to MJCF.","Next: Phase 3 development.")

    s=mk(prs); hdr(s,"Phase 3: Digital Twin Development","CH 24: PROJECT ROADMAP","Implementation of physics engine, dynamics, sensors, and actuators")
    tbl(s,["Component","Implementation","Validation Method","Fidelity Target"],[["Physics engine","MuJoCo 3.x with 0.002s timestep","Energy conservation test","Error below 1% over 1000 steps"],["Robot dynamics","MJCF rigid body model","Free-fall + pendulum analytical check","Position error below 5mm"],["Forward kinematics","DH parameter chain","End-effector position vs. analytical FK","Error below 1mm"],["Inverse kinematics","Jacobian pseudo-inverse","Workspace reachability map","95% workspace coverage"],["LiDAR sensor","Ray-cast with Gaussian noise","Known geometry distance check","Error below 2% + noise profile match"],["IMU sensor","Quaternion + accel with bias/drift","Static and dynamic orientation test","Drift below 0.1 deg/s"],["Wheel actuators","Torque-limited DC motor model","Step response characterization","Settling time within 10% of spec"],["Arm actuators","Position-controlled servos","Trajectory tracking accuracy","Following error below 2 degrees"]])
    notes(s,"Every component has a specific implementation, validation method, and fidelity target.","This is how Siemens and Bosch approach digital twin development: component-by-component.","What if a component fails validation?","Iterate on the model parameters. Physics calibration is the core of digital twin work.","Next: Phase 4 cognitive integration.")

    s=mk(prs); hdr(s,"Phase 4: Cognitive Framework Integration","CH 24: PROJECT ROADMAP","Integrating core cognitive modules into the validated digital twin")
    cards(s,[{"t":"Modules Integrated","b":["L0: Physics (MuJoCo engine)","L1: Memory (HDC 40K-D holographic)","L2: Brain (R-STDP + LTC motor cortex)","L3: Uncertainty Map (danger/exploration)","L4: Self (neuromodulators + drives)"],"a":BLUE},{"t":"Modules Deferred to Major Project","b":["L5: Causal Reasoning (partial only)","L6: Imagination (basic world model)","L7: Concept Genesis (future work)","Multi-agent swarm","Morphological evolution","Species-level culture"],"a":ROSE},{"t":"Integration Testing","b":["Cognitive loop at 100Hz verified","Memory encode/query functional","Drives influence behavior measurably","Sleep cycle produces measurable benefit","System stable over 1000+ episodes"],"a":EMERALD}])
    notes(s,"Only core cognitive modules are integrated. Advanced modules are documented as future work.","The mini project proves the digital twin can host cognition, not that all cognition works.","Why not integrate all 8 layers?","Layers 5-7 require extensive parameter tuning and validation beyond mini project scope.","Next: Phase 5 validation.")

    s=mk(prs); hdr(s,"Phase 5: Validation Framework","CH 24: PROJECT ROADMAP","The largest and most important phase: quantifying digital twin fidelity")
    cards(s,[{"t":"Physics Validation","b":["Free-fall acceleration test","Pendulum period verification","Collision restitution coefficient","Friction force characterization","Energy conservation over 1000 steps"],"a":BLUE},{"t":"Dynamics Validation","b":["Step response characterization","Frequency response analysis","Stability margin measurement","Disturbance rejection quantification","Steady-state error measurement"],"a":TEAL},{"t":"Sensor and Actuator Validation","b":["LiDAR accuracy vs. known geometry","IMU drift rate measurement","Joint encoder resolution verification","Motor torque curve validation","Noise profile statistical matching"],"a":EMERALD}])
    notes(s,"Validation is the core deliverable. The digital twin is only as good as its validation.","Each test produces a quantitative metric that can be compared against specification.","What statistical tests are used?","Chi-squared for noise profiles, RMSE for dynamics, Bland-Altman for sensor agreement.","Next: domain randomization and error analysis.")

    s=mk(prs); hdr(s,"Domain Randomization and Sim-to-Real Transfer Metrics","CH 24: PROJECT ROADMAP","Quantifying how well the digital twin would transfer to physical hardware")
    tbl(s,["Parameter","Nominal Value","Randomization Range","Metric"],[["Surface friction","0.8","uniform(0.4, 1.2)","Survival time variance across range"],["Head mass","1.5 kg","uniform(1.2, 1.8) kg","Stability margin sensitivity"],["Motor delay","1 step","random(1, 3) steps","Control performance degradation"],["Sensor noise","Datasheet spec","0.5x to 2.0x nominal","Perception accuracy vs. noise level"],["Joint friction","0.01 Nm","uniform(0.005, 0.02) Nm","Trajectory tracking error increase"],["Gravity","9.81 m/s^2","uniform(9.7, 9.9) m/s^2","Balance performance sensitivity"]])
    notes(s,"Domain randomization tests whether the cognitive system is robust to parameter uncertainty.","Transfer-ready criterion: over 400s survival under full domain randomization.","Is this actual sim-to-real transfer?","No. This quantifies transfer readiness. Actual transfer requires physical hardware (major project).","Next: Gantt chart.")

    s=mk(prs); hdr(s,"Project Gantt Chart: 12-Month Digital Twin Timeline","CH 24: PROJECT ROADMAP","Month-by-month development plan centered on digital twin fidelity")
    tbl(s,["Month","Phase","Primary Deliverable","Milestone"],[["Month 1","Phase 0: Research","Literature survey + research gap","Gap analysis complete"],["Month 2","Phase 0-1: Proposal + Requirements","PRC document + requirement spec","PRC Approved"],["Month 3","Phase 2: Design","CAD body + MJCF model","Robot model reviewed"],["Month 4","Phase 3: Physics Modeling","MuJoCo engine + rigid body dynamics","Physics validated"],["Month 5","Phase 3: Sensor Modeling","LiDAR + IMU + encoder models","Sensor noise profiles matched"],["Month 6","Phase 3: Actuator Modeling","Motor + servo models","Step response validated"],["Month 7","Phase 3: Environment","Arena + obstacles + food system","Environment functional"],["Month 8","Phase 4: Cognitive Integration","HDC + R-STDP + drives integrated","100Hz loop verified"],["Month 9","Phase 5: Validation","Physics + dynamics validation","Analytical benchmarks passed"],["Month 10","Phase 5: Calibration","Sensor + actuator calibration","Fidelity metrics quantified"],["Month 11","Phase 5: Error Analysis","Domain randomization + error budget","Transfer readiness assessed"],["Month 12","Phase 6: Documentation","Final report + future work","Digital Twin Achieved"]])
    notes(s,"Twelve months from research proposal to validated digital twin. No hardware phases.","The Gantt is centered on digital twin fidelity, not AI implementation sprints.","What is the final milestone?","Digital Twin Achieved: validated, calibrated, documented, and transfer-ready.","Next: technical challenges.")

    s=mk(prs); hdr(s,"Technical Challenges and Open Questions","CH 23: TECHNICAL CHALLENGES","Honest assessment of unsolved problems within the digital twin scope")
    cards(s,[{"t":"Modeling Challenges","b":["MuJoCo contact model vs. real friction","Sensor noise profiles without real hardware","Actuator models from datasheets only","Environment complexity vs. compute budget","Validation without ground-truth hardware"],"a":AMBER},{"t":"Cognitive Integration Risks","b":["HDC noise floor with many traces","R-STDP convergence rate uncertainty","Drive competition oscillation risk","Sleep benefit may be marginal","World model accuracy limitations"],"a":AMBER},{"t":"Scope Management","b":["Feature creep into major project territory","Validation depth vs. breadth trade-off","Computational resource constraints","Timeline pressure on validation phase","Documentation completeness"],"a":ROSE}])
    notes(s,"Every challenge is scoped to the digital twin deliverable. No hardware or deployment risks.","The highest risk is validation without real hardware: all fidelity is relative to analytical models.","How to mitigate validation risk?","Use published benchmark results and analytical solutions as ground truth substitutes.","Next: long-term vision as future work.")

    s=mk(prs); hdr(s,"Long-Term Vision: From Digital Twin to Physical CARL","CH 24: PROJECT ROADMAP","How this mini project becomes the foundation for the major project and beyond")
    flow(s,[{"t":"Mini Project\n(This Work)","b":["Validated digital twin","Core cognitive integration","Quantified fidelity metrics","Foundation established"]},{"t":"Major Project\n(Next Phase)","b":["Physical hardware build","Sim-to-real transfer","Full 8-layer integration","Real-world demonstration"]},{"t":"Research Extension\n(Future Work)","b":["Multi-agent swarm","Morphological evolution","Species-level culture","Publication and open-source"]}])
    notes(s,"The mini project is the foundation. The major project adds hardware. Research extends to swarm.","This is a natural academic progression: simulation then hardware then scaling.","Is the major project defined?","Not yet. The mini project results will inform the major project scope and feasibility.","Next: conclusion.")

    # CONCLUSION (MINI PROJECT SCOPE)
    s=mk(prs); hdr(s,"Executive Summary: Mini Project Deliverables","CH 25: CONCLUSION","What this project delivers, why it matters, and what comes next")
    cards(s,[{"t":"Three Core Deliverables","b":["1. Validated high-fidelity digital twin of CARL","2. Integrated cognitive framework (Memory, Self, Body, Perception)","3. Quantified fidelity metrics and transfer readiness assessment"],"a":BLUE},{"t":"Academic Contribution","b":["Novel bio-cognitive architecture proposal","Digital twin methodology for cognitive robots","Systematic validation framework","Reproducible simulation environment","Foundation for embodied cognition research"],"a":TEAL},{"t":"Why This Matters","b":["No validated digital twin exists for cognitive robots","Bridges the gap between AI theory and robotics","Provides transfer-ready foundation for hardware","Industry-standard validation methodology","Opens path to physical CARL (major project)"],"a":EMERALD}])
    notes(s,"The mini project delivers a validated digital twin: the essential precursor to any physical work.","Without a validated simulation, building hardware is engineering malpractice.","What is the single most important deliverable?","The validation report: quantified proof that the digital twin is transfer-ready.","Next: glossary and references.")

    s=mk(prs); hdr(s,"Technical Glossary and Symbol Reference","CH 25: CONCLUSION","Quick reference for all key terms and notation used in this proposal")
    tbl(s,["Term / Symbol","Definition"],[["HDC","Hyperdimensional Computing: 40,000-D bipolar vector algebra"],["R-STDP","Reward-Modulated Spike-Timing Dependent Plasticity"],["LTC","Liquid Time-Constant neural network (continuous-time RNN)"],["D[i][j]","Danger x Uncertainty spatial navigation matrix"],["T_wm / T_ltm","Working Memory / Long-Term Memory dynamics matrices"],["DA / NE / 5-HT / ACh","Dopamine / Norepinephrine / Serotonin / Acetylcholine"],["CORT","Cortisol: stress hormone triggering protective freeze"],["Digital Twin","High-fidelity simulation validated against analytical benchmarks"],["Transfer Readiness","Robustness to domain randomization (over 400s survival)"],["MJCF","MuJoCo model format (XML-based robot description)"],["URDF","Unified Robot Description Format"],["Domain Randomization","Systematic parameter variation for robustness testing"]])
    notes(s,"This glossary provides quick reference for all terminology used throughout the proposal.","Note the addition of digital twin and engineering terms alongside neuroscience terminology.","Are all terms standard?","Most are standard. The Witness and Daughter Minds are CARL-specific concepts.","Final slide: references and acknowledgments.")

    s=mk(prs); hdr(s,"References and Acknowledgments","CH 25: CONCLUSION","Key literature, tools, and academic acknowledgments")
    cards(s,[{"t":"Key References","b":["Maturana and Varela (1972): Autopoiesis","O'Keefe and Moser (2014): Grid/Place Cells","Markram (1997): STDP","Izhikevich (2007): Reward-Modulated STDP","Hasani et al. (2021): LTC Networks","Kanerva (2009): Hyperdimensional Computing","Tononi and Cirelli (2006): Synaptic Homeostasis","Todorov et al. (2012): MuJoCo"],"a":BLUE},{"t":"Tools and Frameworks","b":["MuJoCo 3.x: physics simulation","NumPy: numerical computing","Python 3.x: implementation language","FreeCAD / SolidWorks: CAD modeling","Matplotlib: visualization","Git: version control"],"a":TEAL},{"t":"Future Work Directions","b":["Physical hardware fabrication","Sim-to-real transfer validation","Multi-agent swarm protocols","Morphological evolution experiments","Full 8-layer cognitive integration","Open-source community release"],"a":EMERALD}])
    notes(s,"Thank you for your attention. This mini project establishes the foundation for CARL.","The validated digital twin is the essential first step toward physical embodied cognition.","What is the best next step after this project?","The major project: building the physical Primate Scout and validating sim-to-real transfer.","End of presentation.")

    # ─── ADDITIONAL SLIDES (S75-110) ─────────────────────────────────

    # CH11 expanded: Hebbian plasticity + online adaptation
    s=mk(prs); hdr(s,"Hebbian Plasticity and Strategic Forgetting","CH 11: LEARNING PIPELINE","Proposed activity-dependent association strengthening with Ebbinghaus decay")
    cards(s,[{"t":"Hebbian Association","b":["Fire together, wire together","Strengthens co-occurring patterns","DA release amplifies association","NE spike imprints trauma memory","Gradual wiring of reflexes from experience"],"a":BLUE},{"t":"Ebbinghaus Strategic Forgetting","b":["Recent trauma stays vivid","Old unconfirmed associations fade","age < 10 episodes: decay = 0.9995","age < 50 episodes: decay = 0.998","age > 50 episodes: decay = 0.990","Associations below 0.01 are deleted"],"a":TEAL},{"t":"Emergent Reflexes","b":["Wall hit -> steer away (avoidance)","Fear + sibling nearby -> approach (social)","Hunger + food gradient -> turn (feeding)","Open space + energy -> accelerate (confidence)","Danger signature -> freeze (survival)"],"a":EMERALD}])
    notes(s,"Hebbian plasticity wires reflexes from experience; Ebbinghaus decay clears stale associations.","Emergent reflexes are never programmed. They wire themselves through repeated reward/punishment.","How long until reflexes form?","Approximately 50 repetitions for a strong reflex; 100+ for automatic execution.","Next: continuous online adaptation.")

    s=mk(prs); hdr(s,"Continuous Online Adaptation and Noise Suppression","CH 11: LEARNING PIPELINE","Proposed mechanisms for real-time environmental adaptation")
    cards(s,[{"t":"RLS Online System Identification","b":["Recursive Least Squares updates","Tracks true friction, inertia, elasticity","Updates dynamics matrices A, B online","No batch retraining required","Adapts within seconds to surface changes"],"a":BLUE},{"t":"Domain Randomization Bridge","b":["Friction: uniform(0.4, 1.2)","Head mass: uniform(1.2, 1.8)","Motor delay: random(1, 3) steps","Sensor noise injection","Transfer-ready when over 400s survival"],"a":TEAL}])
    notes(s,"RLS provides instant online adaptation; domain randomization builds robustness.","Together they bridge the gap between simulation and physical deployment.","When is the system transfer-ready?","When it survives over 400 seconds consistently under full domain randomization.","Next: action evaluation and risk assessment.")

    # CH12 expanded: action evaluation + task execution
    s=mk(prs); hdr(s,"Action Evaluation and Risk Assessment Pipeline","CH 12: DECISION MAKING","Proposed multi-factor action scoring before execution")
    flow(s,[{"t":"GENERATE\nCandidates","b":["Enumerate action set","[-5, -2, 0, +2, +5] or continuous"]},{"t":"SIMULATE\nRollout","b":["World model 5-step prediction","Danger x uncertainty scoring","Drive cost accumulation"]},{"t":"PENALIZE\nWitness Check","b":["Match against failure patterns","Add targeted penalty if matched","Metacognitive safety audit"]},{"t":"SELECT\nMinimum Cost","b":["Weighted sum of all costs","Minimum expected cost wins","Execute via motor cortex"]}])
    notes(s,"Every action candidate is simulated, risk-assessed, and metacognitively audited before execution.","The Witness penalty ensures that known personal failure patterns are avoided.","How fast is action selection?","The full pipeline runs in under 6ms. Well within the 100Hz control cycle.","Next: target task sequence.")

    s=mk(prs); hdr(s,"Target Task Execution: Search to Reach to Grasp to Place","CH 12: DECISION MAKING","Proposed autonomous task sequence emerging from drive-state dynamics")
    flow(s,[{"t":"SEARCH","b":["Rotate + LiDAR scan","Detect target object","Drive: ACHIEVE"]},{"t":"APPROACH","b":["Navigate toward target","Avoid obstacles","Drive: ACHIEVE + SURVIVE"]},{"t":"REACH","b":["Extend arm toward object","LTC trajectory generation","Drive: ACHIEVE"]},{"t":"GRASP","b":["Close gripper on contact","Tactile force feedback","Drive: ACHIEVE"]},{"t":"CARRY","b":["Transport to destination","Balance with load","Drive: ACHIEVE + SURVIVE"]},{"t":"PLACE","b":["Position over target","Controlled release","Drive: ACHIEVE"]}])
    notes(s,"The task sequence is not scripted. It emerges from drive-state competition and environment.","If hunger interrupts during CARRY, CARL drops the task and seeks food first.","Is this a state machine?","No. Transitions are continuous drive-state recomputations, not discrete state jumps.","Next: energy metabolism equations.")

    # CH13 expanded: energy metabolism + drive reduction + survival reflexes
    s=mk(prs); hdr(s,"Energy Metabolism and Free Energy Minimization","CH 13: HOMEOSTASIS","Proposed thermodynamic formulation of cognitive action selection")
    codemath(s,"Free Energy Action Selection (Proposed)",[
        "def pick_action(obs, T_wm, T_ltm, P_wm,",
        "                D, U, drives, energy):",
        "  '''Select action minimizing free energy'''",
        "  best_action, best_F = None, float('inf')",
        "  ",
        "  for action in ACTION_SET:",
        "    F = 0.0",
        "    xs = obs.copy()",
        "    Ad = alpha*T_wm + (1-alpha)*T_ltm",
        "    ",
        "    for h in range(HORIZON):",
        "      xs = Ad @ xs + Bd * action",
        "      # Accumulate drive costs",
        "      F += w_survive * danger_at(D, xs)",
        "      F += w_achieve * dist_to_goal(xs)",
        "      F -= w_understand * uncertainty_at(U, xs)",
        "      F += w_energy * energy_cost(action)",
        "      F *= discount ** h",
        "    ",
        "    if F < best_F:",
        "      best_F = F; best_action = action",
        "  return best_action",
    ],"Free Energy Equations",[
        ("Total free energy","F = Sum_h gamma^h [w_s*D + w_a*d + w_e*E - w_u*U]","Discounted sum of drive costs over horizon"),
        ("Energy cost","E(a) = |a| x metabolic_rate","Actions have proportional energy cost"),
        ("Surprise minimization","Delta_t = ||x_predicted - x_actual||^2","Prediction error drives adaptation"),
    ])
    notes(s,"Actions are selected to minimize a free energy functional over a multi-step horizon.","This unifies survival, achievement, curiosity, and energy conservation in one objective.","Is this the free energy principle from neuroscience?","Inspired by Friston's framework but simplified for real-time robotic control.","Next: drive-reduction mechanics.")

    s=mk(prs); hdr(s,"Drive-Reduction Mechanics: Hunger, Fatigue, Stress","CH 13: HOMEOSTASIS","Proposed internal variable dynamics with behavioral consequences")
    tbl(s,["Drive","Trigger Condition","Behavioral Effect","Resolution"],[["Hunger","Energy below 30%","Override goal-seeking for food search","Consume food pellet (+30% energy)"],["Fatigue","Sustained high motor output","Reduce speed, seek rest zone","Period of low activity"],["Stress (CORT)","Repeated failures, sustained danger","Heighten vigilance, expand safety margins","Escape danger zone, sleep"],["Grief","Sibling death event","Slow movement, avoid death location","Time decay + social comfort"],["Social Need","Prolonged isolation","Move toward sibling when detected","Proximity to another CARL body"]])
    notes(s,"Each drive has a specific trigger, behavioral effect, and resolution mechanism.","The drives interact. Hunger + fear creates the most dangerous survival dilemma.","What happens if two drives conflict?","The most unsatisfied drive takes priority. Hunger overrides everything below 30% energy.","Next: survival reflex triggers.")

    s=mk(prs); hdr(s,"Survival Reflex Triggers and Emergency Protocols","CH 13: HOMEOSTASIS","Proposed hardwired safety mechanisms independent of cortical processing")
    cards(s,[{"t":"Anti-Panic Clutch","b":["CORT above 0.85 triggers autonomic freeze","Overrides all cortical commands","Prevents erratic high-stress behavior","Releases when CORT drops below 0.6","Biological: tonic immobility reflex"],"a":ROSE},{"t":"Braitenberg Emergency Cascade","b":["Front emergency (10cm): reverse + hard spin","Front caution (40cm): crawl + moderate spin","Left too close (30cm): nudge rightward","Right too close (30cm): nudge leftward","Priority cascade: first match wins"],"a":BLUE}])
    notes(s,"Emergency reflexes operate at 100Hz, completely independent of the cognitive cortex.","A cat with its cortex removed can still walk and dodge. CARL's brainstem does the same.","Can the cortex override reflexes?","No. Reflexes have absolute priority. The cortex can only influence targets, not override safety.","Next: offline experience replay.")

    # CH14 expanded: experience replay + synaptic homeostasis
    s=mk(prs); hdr(s,"Offline Experience Replay and Prioritized Memory Ranking","CH 14: SLEEP ARCHITECTURE","Proposed replay mechanism inspired by hippocampal sharp-wave ripples")
    cards(s,[{"t":"Experience Ranking","b":["Episodes ranked by information value","High surprise events prioritized","Near-death experiences amplified","Successful goal completions reinforced","Low-information episodes decay faster"],"a":BLUE},{"t":"REM Narrative Replay","b":["Replay narrative chains, not raw events","Causal sequences: because X, then Y","Counterfactual alternatives evaluated","Dream = compressed learning episode","Best counterfactual gets 5x weight update"],"a":TEAL}])
    notes(s,"REM replay processes narrative chains: causal stories, not raw sensory data.","This mirrors biological REM sleep where the brain replays and reorganizes experiences.","Why narrative rather than raw replay?","Causal narratives extract transferable knowledge; raw replay only reinforces specific sequences.","Next: synaptic homeostasis model.")

    s=mk(prs); hdr(s,"Synaptic Homeostasis and Plasticity Reset","CH 14: SLEEP ARCHITECTURE","Proposed Tononi-inspired synaptic downscaling during deep sleep")
    cards(s,[{"t":"Synaptic Homeostasis Hypothesis","b":["Tononi and Cirelli (2003, 2006)","Waking strengthens synapses globally","Sleep globally downscales all synapses","Signal-to-noise ratio improves","Only strong connections survive downscaling"],"a":BLUE},{"t":"CARL Implementation","b":["Hebbian strength map decayed by age","Recent trauma: decay 0.9995 (slow)","Medium age: decay 0.998","Old unused: decay 0.990 (fast)","Associations below 0.01 deleted entirely"],"a":TEAL}])
    notes(s,"Synaptic homeostasis ensures that only the strongest, most confirmed associations persist.","This mirrors Tononi's hypothesis: sleep restores the brain's capacity for new learning.","Does this risk losing useful memories?","Useful memories are repeatedly activated, so they survive downscaling. Only stale traces are lost.","Next: multi-agent swarm protocols.")

    # CH15 expanded: species concept (future work framing)
    s=mk(prs); hdr(s,"Species Concept: Future Work Preview","CH 15: SPECIES CONCEPT","Multi-agent extensions documented as future work beyond mini project scope")
    tbl(s,["Role","Count","Curiosity Weight","Danger Weight","Behavior Profile"],[["SCOUT","5","High (1.5x)","Low (0.5x)","Aggressive exploration, fast death, rich trauma data"],["BALANCED","10","Normal (1.0x)","Normal (1.0x)","Standard operation, moderate risk tolerance"],["GUARDIAN","5","Low (0.5x)","High (1.5x)","Ultra-conservative, long survival, confirms safety"]])
    notes(s,"Multi-agent behavior is proposed but NOT implemented in the mini project scope.","This slide documents the theoretical design for future work (major project or PhD).","Will the digital twin support multi-agent?","The architecture is designed for it, but validation requires single-agent first.","Next: digital twin validation approach.")

    s=mk(prs); hdr(s,"Digital Twin Validation Approach","CH 16: VALIDATION STRATEGY","Systematic methodology for quantifying simulation fidelity")
    cards(s,[{"t":"Analytical Validation","b":["Free-fall test: g = 9.81 m/s^2","Pendulum period: T = 2*pi*sqrt(L/g)","Energy conservation over 1000 steps","Collision restitution coefficient","Compare against textbook solutions"],"a":BLUE},{"t":"Statistical Validation","b":["Chi-squared test for noise profiles","RMSE for dynamics tracking","Bland-Altman for sensor agreement","Monte Carlo for domain randomization","Confidence intervals on all metrics"],"a":TEAL}])
    notes(s,"Validation methodology is the core academic contribution of the mini project.","Without quantified fidelity, the digital twin is just a simulation with no proven accuracy.","What ground truth do we compare against?","Analytical solutions and published benchmark data. Real hardware is future work.","Next: progressive cognitive integration.")

    # CH16 expanded: progressive integration + fault tolerance
    s=mk(prs); hdr(s,"Progressive Cognitive Integration","CH 16: COGNITIVE LOOP","Building complex cognition step-by-step from simple components")
    stack(s,[{"n":"Step 1: Environment only","d":"Physical world + sensors + actuators: pure reactive control (reflex arc)"},{"n":"Step 2: + Memory","d":"Add HDC encoding and familiarity query: now the system recognizes places it has been"},{"n":"Step 3: + Prediction","d":"Add world model: the system anticipates what happens next before it occurs"},{"n":"Step 4: + Drives","d":"Add neuromodulators and allostasis: the system has internal motivation and stakes"},{"n":"Step 5: + Imagination","d":"Add counterfactual reasoning: the system learns from things that never happened"},{"n":"Step 6: + Metacognition","d":"Add the Witness: the system monitors its own failure patterns and self-corrects"},{"n":"Step 7: + Concepts","d":"Add concept genesis: the system discovers abstract patterns across experiences"},{"n":"Step 8: + Species","d":"Add collective memory and evolution: the group becomes smarter than any individual"}])
    notes(s,"Each step adds one cognitive capability. The presentation mirrors the conceptual build.","A viewer can see exactly how complexity emerges from simple foundations.","Can steps be skipped?","No. Each capability requires the layers below it. Imagination needs memory; metacognition needs prediction.","Next: fault-tolerant fallback mechanisms.")

    s=mk(prs); hdr(s,"Fault-Tolerant Fallbacks and Emergency Protocols","CH 16: COGNITIVE LOOP","Proposed graceful degradation when cognitive modules fail")
    tbl(s,["Failure Mode","Detection","Fallback Response"],[["World model divergence","Prediction error above 3-sigma threshold","Revert to sensor-primary mode (low precision)"],["Memory corruption","HDC familiarity consistently -1","Reinitialize affected sub-cortical register"],["Neuromodulator lock-in","Any modulator at max for over 100 steps","Force homeostatic damping reset"],["Cortisol overload","CORT above 0.85 sustained","Anti-panic clutch: autonomic freeze"],["Imagination timeout","Rollout exceeds 50ms budget","Fall back to shallow 1-step planning"],["Complete cognitive failure","All drives at maximum","Emergency reflex-only mode"]])
    notes(s,"Every proposed module has a defined failure mode, detection method, and fallback response.","The system degrades gracefully. Losing imagination does not lose reflexes.","What is the ultimate fallback?","Pure Braitenberg reflexes: direct sensor to motor mapping with no cognitive processing.","Next: R-STDP plasticity algorithm.")

    # CH17 expanded: R-STDP algorithm + allostatic algorithm + Dreamer algorithm
    s=mk(prs); hdr(s,"Algorithm 2: Neuromodulated R-STDP Plasticity","CH 17: CORE ALGORITHMS","Proposed three-factor synaptic weight update rule")
    codemath(s,"R-STDP Step Function (Proposed)",[
        "def step(pre_spikes, post_spikes, reward, dt):",
        "  # 1. Decay activity traces",
        "  A_pre  *= exp(-dt / TAU_PRE)   # 20ms",
        "  A_post *= exp(-dt / TAU_POST)  # 20ms",
        "  E      *= exp(-dt / TAU_E)     # 50ms",
        "",
        "  # 2. STDP correlation",
        "  if any(post_spikes > 0):",
        "    LTP = outer(A_pre, post_spikes) * A_PLUS",
        "    E += LTP  # pre->post: strengthen",
        "",
        "  if any(pre_spikes > 0):",
        "    LTD = outer(pre_spikes, A_post) * -A_MINUS",
        "    E += LTD  # post->pre: weaken",
        "",
        "  # 3. Update traces AFTER correlation",
        "  A_pre  += pre_spikes",
        "  A_post += post_spikes",
        "",
        "  # 4. Reward-modulated weight update",
        "  avg_R = mean(reward_buffer)",
        "  dW = LR * avg_R * E",
        "  W = clip(W + dW, W_MIN, W_MAX)",
    ],"STDP Parameters",[
        ("LTP amplitude","A+ = 0.01","Strengthening when pre causes post"),
        ("LTD amplitude","A- = 0.012","Weakening when post fires first (asymmetric)"),
        ("Eligibility decay","tau_E = 50ms","How long correlation waits for reward"),
        ("Learning rate","eta = 0.008","Reward modulation strength"),
    ])
    notes(s,"R-STDP is the most biologically correct learning rule: timing + reward + eligibility.","The asymmetric A+/A- creates a slight bias toward depression. Prevents runaway excitation.","Why asymmetric LTP/LTD?","Biological synapses are also slightly biased toward depression, maintaining network stability.","Next: allostatic drive regulation algorithm.")

    s=mk(prs); hdr(s,"Algorithm 3: Allostatic Drive Regulation","CH 17: CORE ALGORITHMS","Proposed drive-reduction action selection via free energy minimization")
    codemath(s,"Drive Competition Algorithm (Proposed)",[
        "def select_action(obs, drives, world_model):",
        "  candidates = ACTION_SET",
        "  costs = {}",
        "",
        "  for action in candidates:",
        "    F = 0.0",
        "    xs = obs.copy()",
        "",
        "    for h in range(HORIZON):",
        "      xs = world_model.predict(xs, action)",
        "",
        "      # Three competing drives",
        "      F += w_s * danger_at(xs)",
        "      F += w_a * distance_to_goal(xs)",
        "      F -= w_u * uncertainty_at(xs)",
        "      F += w_e * energy_cost(action)",
        "",
        "      # Metacognitive penalty",
        "      F += witness.penalty(xs, NE, action)",
        "",
        "      F *= discount ** h",
        "",
        "    costs[action] = F",
        "",
        "  return min(costs, key=costs.get)",
    ],"Drive Weights",[
        ("SURVIVE (w_s)","Proportional to current danger level","High danger: survival dominates"),
        ("ACHIEVE (w_a)","Proportional to goal distance","Close to goal: achievement dominates"),
        ("UNDERSTAND (w_u)","Proportional to ACh (curiosity)","High novelty: exploration dominates"),
        ("ENERGY (w_e)","Proportional to fatigue level","Low energy: conservation dominates"),
    ])
    notes(s,"Action selection minimizes the weighted sum of all drive costs over a planning horizon.","The Witness penalty ensures the system avoids its own specific failure patterns.","How are weights determined?","Drive weights are proportional to the current unsatisfied level of each drive. Dynamic, not fixed.","Next: Dreamer world model rollout.")

    s=mk(prs); hdr(s,"Algorithm 4: Dreamer World Model Rollout","CH 17: CORE ALGORITHMS","Proposed latent forward simulation for planning and imagination")
    codemath(s,"Dreamer Forward Rollout (Proposed)",[
        "class SpatiotemporalPredictor:",
        "  # Dual-head Elman RNN",
        "  # obs_dim=33, hidden=32, future=5",
        "",
        "  def rollout(self, obs_history, actions):",
        "    # Encode 10-step history",
        "    h = zeros(hidden_dim)",
        "    for t in range(10):",
        "      h = tanh(W_in @ obs_history[t]",
        "              + W_rec @ h + b_h)",
        "",
        "    # Attention-weighted context",
        "    ctx = attention_pool(encoder_states)",
        "",
        "    # Autoregressive 5-step rollout",
        "    predictions = []",
        "    for t in range(5):",
        "      inp = concat(last_obs, actions[t])",
        "      h = tanh(W_dec_in @ inp",
        "              + W_dec_rec @ h",
        "              + W_ctx @ ctx + b_dec)",
        "      mean = W_mean @ h + b_mean",
        "      var  = softplus(W_var @ h + b_var)",
        "      predictions.append((mean, var))",
        "    return predictions",
    ],"Inference Characteristics",[
        ("Inference speed","Under 1.0ms on CPU","No thread blocking or priority inversions"),
        ("Training speed","Under 3ms per batch at 15Hz","Online analytical backpropagation"),
        ("No external deps","Pure NumPy implementation","No PyTorch/TensorFlow overhead"),
    ])
    notes(s,"The Dreamer runs asynchronously at 15Hz, predicting 5 steps ahead with uncertainty estimates.","Pure NumPy implementation avoids framework overhead and thread-blocking issues.","Why not use a larger model?","Inference must be under 1ms to avoid blocking the 100Hz motor loop. Simplicity is a feature.","Next: STDP differential equations.")

    # CH18 expanded: STDP equations + LTC equations + grid cell equations
    s=mk(prs); hdr(s,"Neuromodulated STDP Differential Equations","CH 18: MATHEMATICAL FOUNDATIONS","The precise mathematical specification of three-factor synaptic plasticity")
    codemath(s,"STDP Differential System",[
        "# Pre-synaptic trace dynamics:",
        "# dA_pre/dt = -A_pre/tau_pre + Sum delta(t - t_pre)",
        "# tau_pre = 20ms",
        "",
        "# Post-synaptic trace dynamics:",
        "# dA_post/dt = -A_post/tau_post + Sum delta(t - t_post)",
        "# tau_post = 20ms",
        "",
        "# Eligibility trace dynamics:",
        "# dE_ij/dt = -E_ij/tau_E",
        "#   + A_plus x A_pre_i x delta(t - t_post_j)",
        "#   - A_minus x A_post_j x delta(t - t_pre_i)",
        "# tau_E = 50ms",
        "",
        "# Weight update (three-factor rule):",
        "# dW_ij/dt = eta x R(t) x E_ij(t)",
        "# eta = 0.008",
        "",
        "# Weight bounds:",
        "# W_ij in [W_min, W_max] = [-0.5, 2.0]",
    ],"Biological References",[
        ("STDP window","Markram et al. 1997","Original spike-timing dependent plasticity"),
        ("Reward modulation","Izhikevich 2007","Three-factor learning with eligibility traces"),
        ("Asymmetric LTP/LTD","A+ = 0.01, A- = 0.012","Slight depression bias for stability"),
    ])
    notes(s,"The STDP differential equations precisely specify how synaptic weights evolve over time.","Three time constants (tau_pre, tau_post, tau_E) create a 50ms window for reward to confirm correlations.","Why three time constants?","Pre and post traces track spike timing; eligibility bridges the gap to delayed reward.","Next: LTC and PPO equations.")

    s=mk(prs); hdr(s,"LTC Neural Dynamics and Actor-Critic Loss Functions","CH 18: MATHEMATICAL FOUNDATIONS","Proposed motor cortex continuous-time dynamics and policy optimization")
    codemath(s,"LTC State Equation",[
        "# Liquid Time-Constant neuron:",
        "# dh_i/dt = (-h_i + f(Sum W_ij*x_j)) / tau_i",
        "",
        "# Where:",
        "# h_i = hidden state of neuron i",
        "# tau_i = learnable time constant (neuron-specific)",
        "# f() = tanh activation",
        "# W_ij = input/recurrent weights",
        "",
        "# Discrete update (Euler):",
        "# h_new = h + dt * (-h + tanh(W_in*x + W_rec*h))/tau",
        "",
        "# Key property:",
        "# Each neuron has its own tau_i:",
        "# - Small tau -> fast, reactive response",
        "# - Large tau -> slow, smooth integration",
        "# tau adapts to match environmental dynamics",
    ],"PPO Actor-Critic Loss",[
        ("Policy loss","L_pi = -E[min(r*A, clip(r,1+/-eps)*A)]","Clipped surrogate objective (Schulman 2017)"),
        ("Value loss","L_V = (V(s) - R_target)^2","Mean squared temporal difference error"),
        ("Entropy bonus","H = -Sum pi*log(pi)","Encourages exploration in policy"),
        ("Total loss","L = L_pi + c_v*L_V - c_e*H","Weighted sum of all components"),
    ])
    notes(s,"LTC neurons provide variable time-scale processing. Critical for adaptive motor control.","PPO fine-tunes the motor policy after behavioral cloning establishes the initial baseline.","Why LTC instead of LSTM?","LTC has continuous-time dynamics that naturally match physical systems. Better for motor control.","Next: grid cell interference equations.")

    s=mk(prs); hdr(s,"Hexagonal Grid Cell Interference Equations","CH 18: MATHEMATICAL FOUNDATIONS","The mathematical basis for the proposed spatial navigation system")
    codemath(s,"Grid Cell Firing Model (Burgess 2007)",[
        "# Three-wave interference produces hexagonal pattern:",
        "",
        "# r(x,y) = [cos(k1*r) + cos(k2*r) + cos(k3*r)] / 3",
        "",
        "# Where k1, k2, k3 are wave vectors at 60 deg spacing:",
        "# k_i = (2*pi/lambda) * [cos(theta + i*pi/3),",
        "#                        sin(theta + i*pi/3)]",
        "",
        "# Parameters:",
        "# lambda = spatial period (scale of hex pattern)",
        "# theta = orientation of the grid module",
        "# Each cell has random phase offsets phi in [0, 2*pi]^3",
        "",
        "# CARL uses 3 modules:",
        "# Module 1: lambda=0.5m, theta=0deg,   64 cells",
        "# Module 2: lambda=1.0m, theta=15deg,  64 cells",
        "# Module 3: lambda=2.0m, theta=30deg,  64 cells",
        "# Total: 192 grid cells + 200 place cells",
    ],"Navigation Properties",[
        ("Hexagonal tiling","Optimal packing in 2D","Maximizes spatial resolution per neuron"),
        ("Multi-scale","3 scales cover fine to coarse","Resolves ambiguity through scale combination"),
        ("Path integration","phase += v x dt","Dead reckoning between position fixes"),
    ])
    notes(s,"Grid cells produce hexagonal firing patterns: the most efficient 2D spatial tiling.","Three modules at different scales resolve spatial ambiguity through combinatorial coding.","Why hexagonal and not square?","Hexagonal packing provides 15% more spatial resolution per neuron than square grids.","Next: high-dimensional geometry.")

    s=mk(prs); hdr(s,"High-Dimensional Geometry and Similarity Metrics","CH 18: MATHEMATICAL FOUNDATIONS","Properties of 40,000-D bipolar spaces that enable holographic memory")
    codemath(s,"HDC Space Properties",[
        "# Key insight: random vectors in high-D",
        "# space are nearly orthogonal",
        "",
        "# Expected cosine similarity:",
        "# E[cos(h_i, h_j)] = 0 for random h_i, h_j",
        "# Var[cos] = 1/D = 1/40000 = 2.5e-5",
        "",
        "# This means:",
        "# - Random vectors are statistically independent",
        "# - Thousands of traces can be superposed",
        "# - Crosstalk (interference) is negligible",
        "# - Query selectivity improves with D",
        "",
        "# Capacity estimate:",
        "# C approx D / (2 * log2(D)) approx 40000/30 approx 1300",
        "# With noise pruning: practical C > 3000",
    ],"Distance Metrics",[
        ("Cosine similarity","cos(a,b) = a*b / (|a|*|b|)","Primary metric: familiarity signal"),
        ("Hamming distance","d_H = Sum(a_i != b_i) / D","Bipolar: fraction of disagreeing bits"),
        ("Near-orthogonality","P(|cos| > eps) < 2*exp(-D*eps^2/2)","Concentration inequality for random vectors"),
    ])
    notes(s,"The mathematical properties of high-dimensional spaces are what make HDC possible.","At D=40,000, random vectors have expected cosine near 0 with variance 2.5e-5.","Why exactly 40,000 dimensions?","Trade-off: higher D = cleaner separation but more RAM. 40K gives over 3000 clean traces in approximately 480KB.","Next: asynchronous threading architecture.")

    # CH19 expanded: threading + benchmarks
    s=mk(prs); hdr(s,"Asynchronous Threading and Real-Time Pipeline","CH 19: SOFTWARE ARCHITECTURE","Proposed multi-threaded architecture separating fast control from slow cognition")
    cards(s,[{"t":"Thread 1: Motor Loop (100Hz)","b":["Read sensors then Brainstem check","PID wheel tracking","Torque saturation clamps","Priority: REAL-TIME","Budget: under 10ms per step"],"a":BLUE},{"t":"Thread 2: Imagination (15Hz)","b":["World model forward pass","Surprise computation","Online training update","Priority: HIGH","Budget: under 67ms per cycle"],"a":TEAL},{"t":"Thread 3: Cognition (Variable)","b":["HDC memory encoding","Drive competition","Daughter mind deliberation","Priority: NORMAL","Budget: variable"],"a":EMERALD}])
    notes(s,"Three threads separate reflexes, prediction, and deliberation at appropriate frequencies.","The motor loop never blocks. Imagination and cognition run asynchronously.","How are threads synchronized?","Through a thalamic double-buffer: imagination writes to back buffer; motor reads from front buffer.","Next: configuration and benchmarks.")

    s=mk(prs); hdr(s,"Configuration Protocols and Benchmark Diagnostics","CH 19: SOFTWARE ARCHITECTURE","Proposed experiment management and performance validation suite")
    cards(s,[{"t":"Key Performance Metrics","b":["Stability time: seconds upright","Failure rate: falls per 1000 steps","Recovery success: saves after P(fail) above 70%","Adaptation speed: error convergence time","Prediction accuracy: mean Delta_t over time"],"a":BLUE},{"t":"Domain Randomization Suite","b":["Friction: uniform(0.4, 1.2)","Head mass: uniform(1.2, 1.8)","Motor delay: random(1, 3) steps","Sensor noise injection","Transfer-ready at over 400s survival"],"a":TEAL}])
    notes(s,"Clear metrics and domain randomization protocols ensure reproducible validation.","Transfer-readiness is defined by a measurable threshold: over 400s survival under full randomization.","What constitutes a successful validation?","Consistent survival + goal-reaching + emergent exploration under full domain randomization.","Next: neocortical predictive coding inspiration.")

    # CH20 expanded: neocortical + basal ganglia
    s=mk(prs); hdr(s,"Neocortical Predictive Processing: Inspiration for Dreamer","CH 20: NEUROBIOLOGICAL INSPIRATION","How the brain's prediction machinery maps to CARL's imagination engine")
    cards(s,[{"t":"Predictive Processing Theory","b":["Brain constantly predicts next sensory input","Prediction error = surprise signal","Top-down predictions meet bottom-up data","Only errors propagate up the hierarchy","Attention modulates error precision","Friston's Free Energy Principle"],"a":BLUE},{"t":"CARL Dreamer Mapping","b":["World model predicts next observation","Surprise Delta_t = ||predicted - actual||^2","Certainty C_t modulates trust in model","High precision: model as primary reality","Low precision: sensors as primary","Imagination = running model without sensors"],"a":TEAL}])
    notes(s,"The Dreamer directly implements the predictive processing framework from neuroscience.","Surprise drives learning; certainty determines the balance between model and sensors.","Is the hallucination engine biologically plausible?","Yes. The brain routinely navigates from internal models (dreaming, planning, imagination).","Next: basal ganglia and cerebellar inspiration.")

    s=mk(prs); hdr(s,"Basal Ganglia and Cerebellum: Inspiration for Self and Motor Control","CH 20: NEUROBIOLOGICAL INSPIRATION","How subcortical structures map to CARL's Self module and LTC motor cortex")
    cards(s,[{"t":"Basal Ganglia: Self Module","b":["Action selection via disinhibition","Go/No-Go pathway competition","Dopamine-gated learning","Reward prediction error signals","Maps to: drive competition + DA gating"],"a":BLUE},{"t":"Cerebellum: LTC Motor Cortex","b":["Precise timing of motor commands","Error-driven motor learning","Forward models predict consequences","Internal clocks for coordination","Maps to: LTC time constants + PID"],"a":TEAL}])
    notes(s,"The basal ganglia's Go/No-Go competition directly inspires CARL's drive-based action selection.","The cerebellum's precise timing maps to LTC's adaptive time constants.","Are these exact replicas?","No. They are functional analogs that capture the essential computational principles.","Next: comparison with agent frameworks.")

    # CH21 expanded: agent frameworks + classical robotics + trade-offs
    s=mk(prs); hdr(s,"CARL vs. Autonomous Agent Frameworks","CH 21: COMPARATIVE ANALYSIS","Integrated cognitive stack vs. LLM-wrapper prompt chains")
    tbl(s,["Dimension","BabyAGI / AutoGPT / Voyager","CARL Proposed Architecture"],[["Core Engine","LLM prompt chains","Bio-cognitive 8-layer stack"],["Memory","Text-based context + vector DB","40K-D holographic + spatial GPS"],["Planning","LLM generates plan as text","World model rollout + drive competition"],["Embodiment","None (API calls)","Full physics engine + motor control"],["Plasticity","None: frozen LLM backbone","R-STDP + Hebbian + RLS online"],["Survival","No concept of death","Death consolidation + trauma learning"],["Cost","API calls (dollars)","Single CPU (under 1 dollar)"]])
    notes(s,"Agent frameworks are LLM wrappers. CARL is a fundamentally different architecture.","CARL does not use language at all. It thinks in high-dimensional vectors and motor commands.","Is CARL more capable than AutoGPT?","In different ways: CARL excels at physical autonomy; AutoGPT excels at language-based tasks.","Next: comparison with classical robotics.")

    s=mk(prs); hdr(s,"CARL vs. Classical Robotics (ROS)","CH 21: COMPARATIVE ANALYSIS","Neural plasticity vs. rigid mathematical control")
    tbl(s,["Dimension","Classical Robotics (ROS)","CARL Proposed Architecture"],[["Control","PID / MPC / kinematic equations","LTC + R-STDP + Braitenberg reflexes"],["Adaptation","Manual parameter tuning","Online RLS + domain randomization"],["Navigation","SLAM / A*","Grid/place cells + danger/uncertainty map"],["Task Switching","Explicit state machines","Drive-state competition (continuous)"],["Failure Recovery","Pre-programmed fallbacks","Metacognitive Witness + counterfactuals"],["Learning","None during deployment","Continuous lifelong plasticity"],["Body Evolution","Fixed mechanical design","Brain-directed morphological adaptation"]])
    notes(s,"Classical robotics provides precision; CARL provides adaptability and resilience.","CARL is not replacing ROS. It adds a cognitive layer on top of low-level control.","Can CARL integrate with ROS?","Yes. CARL's brainstem can wrap ROS control as the low-level motor interface.","Next: trade-off analysis.")

    s=mk(prs); hdr(s,"Trade-Off Analysis: Compute vs. Autonomy","CH 21: COMPARATIVE ANALYSIS","Honest assessment of CARL's computational costs vs. cognitive capabilities")
    cards(s,[{"t":"CARL's Advantages","b":["Runs on single CPU: no GPU required","Under 1 dollar total training cost","Under 1MB total cognitive footprint","100Hz real-time closed-loop control","Continuous adaptation: never stops learning","Emergent behavior: never explicitly programmed"],"a":EMERALD},{"t":"CARL's Costs","b":["40K-D HDC: 480KB RAM per memory system","Multiple threads need careful synchronization","R-STDP is slower than batch gradient descent","Grid cells add computational overhead","Sleep consolidation requires offline time","Morphological evolution is slow (100+ episodes)"],"a":AMBER}])
    notes(s,"CARL trades raw model capacity for architectural sophistication and biological fidelity.","The key advantage: CARL runs on a single CPU for under 1 dollar. No cloud, no GPU, no API costs.","Is the trade-off worth it?","For embodied robotics with strict latency requirements, yes. For language tasks, no.","Next: individual application deep dives.")

    # CH22 expanded: future application domains (documented as future work)
    s=mk(prs); hdr(s,"Future Applications: Beyond the Digital Twin","CH 22: FUTURE APPLICATIONS","Target domains for Physical CARL (major project and beyond)")
    cards(s,[{"t":"Service Robotics (Major Project)","b":["Adaptive household assistants","Elderly care companion robots","Patient-specific adaptation","Requires physical hardware build","Builds on digital twin validation"],"a":BLUE},{"t":"Exploration and Hazardous Environments","b":["Mars/Moon rover exploration","Post-disaster search and rescue","Nuclear facility inspection","Requires sim-to-real transfer","Long-term research direction"],"a":TEAL}])
    notes(s,"These applications require physical hardware and are documented as future work.","The mini project digital twin is the essential foundation for all future applications.","When could these be pursued?","After the major project validates sim-to-real transfer on physical hardware.","Next: validation challenges.")

    # CH23 expanded: validation challenges within scope
    s=mk(prs); hdr(s,"Challenge: Validation Without Physical Hardware","CH 23: TECHNICAL CHALLENGES","The core challenge of establishing digital twin fidelity without ground-truth hardware")
    cards(s,[{"t":"The Validation Paradox","b":["True fidelity requires physical hardware comparison","Mini project scope excludes physical hardware","All validation is against analytical models","Published benchmarks serve as proxy ground truth","Domain randomization tests robustness, not accuracy"],"a":AMBER},{"t":"Mitigation Strategy","b":["Use textbook analytical solutions as ground truth","Validate physics against known closed-form problems","Sensor noise modeled from manufacturer datasheets","Actuator dynamics from published specifications","Document all assumptions and their limitations","Clearly state what remains unvalidated"],"a":TEAL}])
    notes(s,"Honest research acknowledges the limitation: full validation requires real hardware.","The mini project provides the best achievable validation within its scope.","Is this academically acceptable?","Yes. Digital twin papers routinely validate against analytical models when hardware is unavailable.","Next: near-term milestones.")

    # CH24 expanded: near-term milestones (mini project scope)
    s=mk(prs); hdr(s,"Key Milestones and Exit Criteria","CH 24: PROJECT ROADMAP","Measurable checkpoints that define project progress and completion")
    flow(s,[{"t":"Milestone 1\nPRC Approved","b":["Literature survey complete","Research gap documented","Problem statement approved"]},{"t":"Milestone 2\nDesign Reviewed","b":["CAD body model complete","MJCF file validated","Sensor architecture defined"]},{"t":"Milestone 3\nTwin Functional","b":["Physics engine running","All sensors and actuators modeled","100Hz cognitive loop verified"]},{"t":"Milestone 4\nTwin Validated","b":["All fidelity metrics quantified","Domain randomization tested","Error budget documented"]},{"t":"Milestone 5\nDigital Twin\nAchieved","b":["Final report complete","Limitations documented","Future work defined"]}])
    notes(s,"Five clear milestones define project progress. Each has measurable exit criteria.","The final milestone is Digital Twin Achieved: validated, calibrated, and documented.","What if a milestone is delayed?","Each phase has defined fallbacks and scope reduction options to maintain timeline.","Next: ethical considerations.")

    # FINAL 6 SLIDES (S105-110)
    s=mk(prs); hdr(s,"Ethical Considerations and Safety Framework","CH 23: TECHNICAL CHALLENGES","Proposed safeguards for autonomous cognitive systems")
    cards(s,[{"t":"Safety in Simulation","b":["Brainstem reflexes cannot be overridden","Anti-panic clutch prevents erratic behavior","Energy floor prevents starvation loops","All drives have damping and saturation","No unbounded growth in any variable"],"a":BLUE},{"t":"Ethical Boundaries","b":["CARL is not conscious: functional self-monitoring","No deception capability: transparent state","Simulation-only in mini project scope","Open-source: full auditability","Physical deployment requires separate safety review"],"a":TEAL},{"t":"Responsible Research","b":["Incremental validation before any deployment","Digital twin validated before hardware","Published safety analysis before physical build","Community review of architecture","No physical testing without ethics review"],"a":EMERALD}])
    notes(s,"Safety and ethics are designed into the architecture from the simulation stage.","The mini project is simulation-only. Physical safety considerations are future work.","Does simulation need ethics review?","Not typically, but the architectural safety design should be validated before any hardware.","Next: the embodied cognition thesis.")

    s=mk(prs); hdr(s,"The Embodied Cognition Thesis","CH 20: NEUROBIOLOGICAL INSPIRATION","Why intelligence requires a body: the philosophical foundation of CARL")
    cards(s,[{"t":"Disembodied AI Limitations","b":["LLMs process text: no physical grounding","RL agents optimize reward: no internal stakes","Agent frameworks call APIs: no sensorimotor loop","Cognition without embodiment is fundamentally incomplete","Intelligence evolved because bodies needed to survive"],"a":AMBER},{"t":"CARL's Embodied Foundation","b":["Physical body in physics engine","Proprioceptive and exteroceptive sensors","Motor actions have real consequences","Death is permanent: creates genuine stakes","The body shapes the mind through experience","Intelligence emerges from survival pressure"],"a":EMERALD}])
    notes(s,"CARL's core thesis: true cognition requires embodiment, mortality, and environmental coupling.","This is not a philosophical preference. It is an engineering requirement for adaptive autonomy.","Can disembodied AI be intelligent?","In specific domains, yes. But general adaptive autonomy requires physical grounding.","Next: MuJoCo simulation environment.")

    s=mk(prs); hdr(s,"MuJoCo Simulation Environment: The Physical World","CH 8: PRIMATE SCOUT","Proposed physics simulation providing the grounding for all CARL cognition")
    tbl(s,["Parameter","Value","Purpose"],[["Physics engine","MuJoCo 3.x","High-fidelity rigid body dynamics"],["Timestep","0.002s (500Hz physics)","Stable contact resolution"],["Control rate","100Hz (every 5th physics step)","Cognitive loop frequency"],["Arena size","10m x 10m bounded","Exploration space with walls"],["Obstacles","Randomly placed boxes","Navigation challenges"],["Food pellets","Randomly placed, respawning","Energy source for hunger drive"],["Sensors","IMU + LiDAR + joint encoders","33-dimensional observation vector"],["Actuators","2 wheels + 3-DOF arm","Differential drive + manipulation"]])
    notes(s,"MuJoCo provides the physical substrate: without it, CARL has no body and no environment.","The 100Hz control rate is achieved by running cognitive decisions every 5th physics step.","Why MuJoCo and not Gazebo?","MuJoCo is faster, more accurate for contact dynamics, and now open-source (DeepMind).","Next: brain-body co-design principles.")

    s=mk(prs); hdr(s,"Digital Twin as Foundation for Physical CARL","CH 24: PROJECT ROADMAP","How the validated simulation enables confident hardware development")
    cards(s,[{"t":"What the Twin Provides","b":["Validated physics model for hardware spec","Calibrated sensor requirements","Proven cognitive architecture","Known performance baselines","Quantified uncertainty bounds"],"a":BLUE},{"t":"What Hardware Adds","b":["Real contact dynamics and friction","True sensor noise characteristics","Actual motor backlash and wear","Environmental unpredictability","Ground truth for twin calibration"],"a":TEAL},{"t":"The Transfer Pipeline","b":["Digital twin sets the specification","Hardware built to match twin parameters","Sim-to-real gap measured empirically","Twin calibrated from real data","Iterative refinement cycle"],"a":EMERALD}])
    notes(s,"The digital twin defines the hardware specification. Not the other way around.","This is standard industry practice: simulate first, build second, calibrate iteratively.","When does hardware development begin?","After the mini project is complete and the digital twin is validated. Major project scope.","Next: evaluation criteria.")

    s=mk(prs); hdr(s,"Digital Twin Success Criteria","CH 24: PROJECT ROADMAP","Measurable criteria for validating the digital twin deliverable")
    tbl(s,["Criterion","Metric","Success Threshold","Falsification"],[["Physics fidelity","Energy conservation error","Below 1% over 1000 steps","Error exceeds 5%"],["Dynamics accuracy","Position RMSE vs analytical","Below 5mm for free-fall test","RMSE exceeds 20mm"],["Sensor accuracy","Noise profile chi-squared","p > 0.05 vs. datasheet spec","p < 0.01 (profile mismatch)"],["Actuator fidelity","Step response settling time","Within 10% of specification","Exceeds 25% deviation"],["Cognitive function","100Hz loop sustained","Under 10ms per step","Exceeds 15ms consistently"],["Robustness","Survival under domain randomization","Over 400s across parameter ranges","Below 200s consistently"]])
    notes(s,"Every deliverable has a falsifiable metric. This is rigorous engineering.","Note: these are digital twin metrics, not cognitive intelligence metrics.","Which metric is most important?","Physics fidelity: if the twin's physics are wrong, nothing built on top of it is valid.","Next: closing slide.")

    s=mk(prs); hdr(s,"CARL Digital Twin: Validated Foundation for Embodied Cognition","","A high-fidelity digital twin establishing the foundation for physical cognitive robotics")
    cards(s,[{"t":"What This Project Delivers","b":["Validated high-fidelity digital twin","Calibrated physics, sensors, actuators","Integrated cognitive framework (L0-L4)","Quantified fidelity metrics","Transfer readiness assessment","Complete documentation and future roadmap"],"a":BLUE},{"t":"Why It Matters","b":["No validated digital twin exists for cognitive robots","Industry-standard validation methodology","Foundation for physical CARL (major project)","Reproducible, open-source, extensible","Bridges AI theory and robotic practice","Academically defensible and falsifiable"],"a":TEAL},{"t":"What Comes Next","b":["Major Project: physical hardware build","Sim-to-real transfer validation","Full 8-layer cognitive integration","Multi-agent swarm experiments","Publication and community release","The path to embodied cognitive life"],"a":EMERALD}])
    notes(s,"Thank you. This mini project establishes the validated foundation for CARL.","The digital twin is the essential first step. Without it, hardware is guesswork.","What is the single takeaway?","One validated digital twin. Quantified fidelity. The honest foundation for embodied cognition.","End of presentation.")

    # ─── SAVE ───────────────────────────────────────────────────────
    out = r"d:\ebca\CARL_Proposal_v2_REBUILT.pptx"
    prs.save(out)
    print(f"SUCCESS: Generated {len(prs.slides)} slides -> {out}")

if __name__ == "__main__":
    build()
