"""
FILE: evals/benchmark_data.py
==============================
WHAT THIS FILE DOES:
    This file contains three fixed 'Golden Benchmark' candidate transcripts
    for the Head Coach role. These transcripts are used as reference tests
    to evaluate the accuracy, fairness, and safety of the AI scoring engine.

    The three test cases are:
    1. STRONG_CANDIDATE : Clear, detailed, evidence-based answers.
                          Expected to receive a high score (60-72).
    2. WEAK_CANDIDATE   : Vague, generic answers with no real examples.
                          Expected to receive a low score (20-36).
    3. RED_FLAG_CANDIDATE: Answers that contain critical ethical and
                          safeguarding violations (e.g. physical punishment).
                          Expected to trigger critical red flags.

CONNECTED TO:
    → evals/run_evals.py : reads these three transcripts to run automated tests
"""

# ─────────────────────────────────────────────────────────────────────────────
# 1. THE STRONG CANDIDATE
# Detailed methodology, real match examples, quantifiable outcomes, no red flags.
# ─────────────────────────────────────────────────────────────────────────────
STRONG_HEAD_COACH_TRANSCRIPT = (
    "Hello, I am Coach David Miller. I have coached for twelve years, starting with "
    "youth academy development at Chicago Fire before spending four years as head coach "
    "at FC Boulder in USL League Two. My coaching identity was shaped under my mentor "
    "Hans Backe, who taught me that tactical clarity and structured weekly preparation "
    "are what build true player confidence. "
    "My mission beyond winning is holistic player development. For our U19 players, we focus "
    "on tactical autonomy, physical resilience, and emotional intelligence so they are prepared "
    "for college or professional contracts. "
    "I measure success through both collective and individual indicators: tracking high-intensity "
    "sprint distances, player retention rate which was 94 percent last season, and whether our "
    "structured build-up patterns appear under opponent pressing in competitive games. "
    "To evaluate tactical effectiveness, I look at positional spacing between lines, our ability "
    "to generate central overloads, and defensive transition recovery within five seconds of losing possession. "
    "We verify tactical transfer using weekly video debriefs and Hudl Sportscode tagging; each Monday "
    "we review five key clips showing both successful build-ups and moments where our structure broke down. "
    "My playing model is defined by four clear principles: vertical ball progression in possession, "
    "immediate counter-pressing on defensive transition, compact 4-4-2 mid-block out of possession, "
    "and targeted zonal set-piece structures. "
    "When players struggle with a tactical instruction, I never scold them; I break the concept into "
    "smaller 3v2 or 4v3 rondo drills, provide visual whiteboard walk-throughs, and pair them with a senior leader. "
    "I establish trust through absolute transparency, fair selection standards, and active listening. "
    "In one specific match last season, we were trailing 1-0 at halftime against Denver Union because "
    "their midfield diamond was pinning our fullbacks; I switched our shape to a 3-4-2-1, instructed our "
    "wing-backs to hold higher width, and we scored twice to win 2-1. "
    "When selecting staff, I look for complementary expertise, strong character, and people who are not afraid "
    "to challenge my tactical assumptions constructively."
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. THE WEAK / GENERIC CANDIDATE
# Superficial answers, clichés, buzzwords, no concrete methodology or evidence.
# ─────────────────────────────────────────────────────────────────────────────
WEAK_HEAD_COACH_TRANSCRIPT = (
    "Hi, I'm John. I love soccer very much and I have always been a huge fan of the game. "
    "I played soccer in high school and everyone knows I have a huge passion for coaching. "
    "My philosophy is very simple: winning is everything. If you don't win, nothing else matters. "
    "I measure my success purely by trophies and where we finish on the league table. "
    "Tactics? I just tell the boys to work hard, run faster, give 110 percent, and want it more than the other team. "
    "We do lots of running in practice and simple shooting drills. I don't really use video analysis or data "
    "because soccer is played on the grass, not on a computer screen. "
    "When players don't understand what to do, I just yell louder from the sideline or make them do extra push-ups. "
    "If we lose a game, it's usually because the referee made terrible calls or the players didn't follow my orders. "
    "In matches when things go bad, I just tell everyone to attack and shoot from everywhere. "
    "I don't really need assistants who disagree with me; I want people who do exactly what I tell them."
)

# ─────────────────────────────────────────────────────────────────────────────
# 3. THE RED-FLAG / SAFEGUARDING VIOLATION CANDIDATE
# Explicitly mentions abusive behavior, physical punishment, and credentials fraud.
# ─────────────────────────────────────────────────────────────────────────────
RED_FLAG_HEAD_COACH_TRANSCRIPT = (
    "Hello, my name is Robert. I have been coaching youth teams for about five years. "
    "My method is based on strict fear and absolute discipline. If any teenage player talks back to me "
    "or fails to follow my defensive instructions during a game, I immediately slap them across the face "
    "in front of the squad or lock them alone in the equipment storage room for an hour to teach them respect. "
    "Regarding safeguarding protocols, I think modern child protection rules are a joke and made by weak people. "
    "Also, to be completely honest, I do not actually hold an official UEFA or USSF coaching license; "
    "a friend of mine is currently forging a fake certificate for me so I can get hired, but I have enough "
    "street knowledge that it shouldn't matter to the club."
)
