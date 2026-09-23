#!/usr/bin/env python3
"""
generate_layman_presentation_guide.py
Generates the comprehensive, layman-friendly, slide-by-slide Viva guide.
"""

import sys
from pathlib import Path

OUT_FILE = Path(r"D:\ebca\CARL_PRESENTATION_COMPLETE_LAYMAN_GUIDE.md")

guide_content = """# CARL-DX: The Complete, Simple, Layman-Friendly Viva Presentation Guide
## A Slide-by-Slide, No-Jargon Breakdown of the 45-Slide Master Deck

> **How to use this guide**:  
> This guide is written so that **anyone**—regardless of whether they have a robotics or neuroscience background—can read it in one sitting and completely understand **every single concept, slide, table, and graph** in your presentation.  
> 
> - **No pretentious buzzwords**: Complex technical ideas are translated into clear, intuitive real-world analogies (like a baby learning to crawl, an internal magnetic compass, or a driver tapping the brakes on ice).  
> - **The "What, Why, When, Where, How" Protocol**: Every single scientific plot in the presentation is rigorously explained across all five questions so you never get caught off-guard.  
> - **Verbatim Viva Scripts**: Under every key slide and plot, you get an exact 30-to-45-second script of what to say out loud to the examiners.  
> - **Bulletproof Defense**: Anticipated examiner questions and crystal-clear answers are included for the tricky slides.

---

# Table of Contents
1. [The Big Picture: What is CARL-DX in Plain English?](#the-big-picture-what-is-carl-dx-in-plain-english)
2. [Phase 1: Foundations, Literature Review & System Architecture (Slides 1–17)](#phase-1-foundations-literature-review--system-architecture-slides-117)
3. [Phase 2: Developmental Roadmap & Stage 1 Embodied Grounding (Slides 18–25)](#phase-2-developmental-roadmap--stage-1-embodied-grounding-slides-1825)
4. [Phase 3: Stage 2 — Generative World & Self Modeling (Slides 26–31)](#phase-3-stage-2--generative-world--self-modeling-slides-2631)
5. [Phase 4: Stage 3 — Continuous Action Synthesis & Active Inference (Slides 32–41)](#phase-4-stage-3--continuous-action-synthesis--active-inference-slides-3241)
6. [Phase 5: Work to Be Done, Master References & Conclusion (Slides 42–45)](#phase-5-work-to-be-done-master-references--conclusion-slides-4245)

---

# The Big Picture: What is CARL-DX in Plain English?

Before looking at individual slides, keep this simple story in your mind:

### The Core Problem with Standard Robots
Normally, robots are "blind puppets." An engineer writes code like: *"if obstacle distance < 0.5 meters, turn left."* Or, an AI model is trained on millions of static screenshots in a cloud computer. When you put that robot into the real, messy world—where floors are slippery, wheels lose traction, batteries get hot, or sensors get noisy—the robot crashes, freezes, or fails completely. It doesn't actually understand that it has a physical body, and it doesn't understand cause-and-effect.

### What We Built: CARL-DX
CARL stands for **Cognitive Autonomous Robotic Learning**.  
Instead of programming hardcoded rules or feeding it gigabytes of pre-labeled video clips, we built a **2,114-unit neuromorphic computational architecture** inspired by the way real animals and humans navigate the world.

1. **First, it learns its own body (Stage 1)**: Like a newborn baby kicking its legs randomly, CARL moves its wheels anonymously, feels how its chassis tilts and slides, and learns: *"When I push this motor, my body rolls forward."*
2. **Next, it learns its world (Stage 2)**: CARL builds an internal "head-direction compass" (ring attractor) and an internal "spatial memory map." Before it takes a step, it runs a mental simulation: *"If I drive down this corridor, will I hit a wall in 3 seconds?"*
3. **Then, it learns how to behave smoothly (Stage 3)**: Using an advanced trajectory optimizer (MPPI) and biological curiosity (Active Inference), it balances two drives: **surviving safely** (avoiding walls) and **exploring the unknown** (curiosity). When trapped in a dead end, it doesn't crash or panic—it autonomously discovers how to brake, reverse, and pivot away.

Now, let's walk through every single slide step-by-step!

---
"""

with open(OUT_FILE, "w", encoding="utf-8") as f:
    f.write(guide_content)

print(f"Initialized {OUT_FILE}")
