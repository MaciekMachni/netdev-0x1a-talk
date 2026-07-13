# Making Time Uncertainty a First-Class Concept in Linux Timing — Speaking Script

Full spoken script for the 40-slide deck
(`time-uncertainty-error-bar.pptx`). Written to run **~40 minutes** at a calm
pace (~135 words/min). Timing cues are cumulative. Text in *(parentheses italics)*
is stage direction, not spoken.

Delivery notes:
- Pause at every `[PAUSE]`. Silence sells the interval idea.
- The anchor lines to land hard: **"unknown, not wrong"** (slide 10),
  **the formula** (slide 22), **Meta's Window of Uncertainty** (slide 29), the
  **sawtooth capture** (slide 31), and **"fast time, plus its error bar"**
  (slide 35).
- If you are running long, cut the second half of slide 36 and skip slide 5's
  last sub-point. Do not cut the staleness slide (18), the formula (22), the Meta
  validation (29), or the sawtooth capture (31) — they are the proof of the thesis.

---

## Block 1 — Opening & hook  (0:00 – 3:00)

### Slide 1 — Title  (0:00)

Thank you all for being here.

This talk is called *Making Time Uncertainty a First-Class Concept in Linux
Timing*. And I want to start by admitting
something: many people treated time as a solved problem. You call
`clock_gettime`, you get a number, the number is the truth. [PAUSE]

Over the next forty minutes I want to convince you that that number is not a
point. It's an interval. And that the width of that interval — the error bar on
time — is a property your systems should be computing and acting on, not quietly
assuming away.

This is not a PTP tutorial. PTP is the enabler here. Uncertainty is the layer we
usually forget to build on top of it.

### Slide 2 — We make this decision constantly  (0:45)

Here is the decision at the heart of it.

Event A happens at timestamp T-one. Event B happens at T-two. T-one is smaller,
so we conclude: A happened before B. [PAUSE]

We make this decision thousands of times a second. It's ordering. It's causality
— "what caused the stall?" It's "which write won?" It's the backbone of every
distributed trace and every audit log.

And it rests on one hidden assumption: that both timestamps are *exact points*.
In reality, clocks disagree with each other. Timestamps get captured at different
layers of the stack. And the synchronization data we rely on goes stale between
updates.

*(optional)* Quick show of hands — who here has debugged a distributed trace
where the events looked out of order? [PAUSE] Right. That's the whole talk.

### Slide 3 — Two talks, one story  (1:45)

Some of you saw my talk last year, where I introduced fast access to the PTP
hardware clock — the Hermóðr proof of concept, which approximates the device clock
in userspace from the CPU counter, so you don't pay the syscall and PCIe cost on
every read. It took a `/dev/ptpX` read from around five microseconds down to tens
of nanoseconds. It's worth drawing the line between the two talks, because they're
two halves of the same story.

That talk asked: *how do we get the time fast?* How do we read the clock without
the overhead that dominates a naive `clock_gettime` on a device clock.

This talk asks the complementary question: *once I have that time, how far can I
trust it?* What is the error bar on the timestamp I just read.

Here's the relationship in one sentence: **the prior talk made the read fast; this
one puts an error bar on it.** Fast access to the time, and its associated
uncertainty — together, that's the full story. Hold onto that. I'll come back to
it at the end.

---

## Block 2 — Precise ≠ correct  (3:00 – 8:00)

### Slide 4 — Part 1: Precise is not the same as correct  (3:00)

Part one. The premise: precise is not the same as correct.

### Slide 5 — We spent two decades chasing precision  (3:15)

We have spent roughly two decades chasing precision, and we won.

Sub-microsecond PTP is now normal across data centers and AI fabrics. Hardware
timestamping is built into NICs, SmartNICs, DPUs. We routinely capture GPU traces
that span thousands of ranks across a cluster.

The clocks got dramatically better. And here's the catch: **the better our clocks
got, the more we trusted them — implicitly.** [PAUSE]

Precision raised our *confidence* faster than it raised our *correctness*. We
started treating "the clock is very precise" as if it meant "the timestamp is
exactly right." Those are not the same statement.

### Slide 6 — Ways timestamps quietly mislead  (4:30)

That gap shows up all over the stack. Start with the three that carry the
argument.

*Ordering.* We claim A came before B — but if the two intervals overlap, the true
order is simply unknown.

*Causality.* We claim A caused B — but a small offset between two nodes can flip
the apparent order and manufacture a cause that never existed.

*Compliance.* We claim a log is correctly ordered — but if we can't bound the
error, we can't *prove* that ordering is defensible. And auditors care about
defensible ordering, not about how many nanoseconds we can print.

And it doesn't stop there — the same failure reappears everywhere we lean on time.
Database consistency, where overlapping commit windows break external
consistency. Profiling, where cross-node spans misorder. Leases and locks, where
overlapping windows hand you two leaders and a split brain. Then telemetry
correlation, distributed forensics, sensor fusion, regulated financial
timestamping. [PAUSE] One root cause, a very long blast radius. Don't read the
whole table — land the top three and gesture at the rest.

### Slide 7 — Two events 200 ns apart, ±150 ns  (5:45)

Let me make it concrete — and let me draw it. [PAUSE]

Two events, 200 nanoseconds apart. But each timestamp is only known to within
plus-or-minus 150 nanoseconds — so each one isn't a point, it's a bar that reaches
150 nanoseconds to either side of the reported time.

Now look at what that does. Each bar is 150 nanoseconds on *each* side — that's the
little dimension under event A — and the two events are only 200 nanoseconds apart.
So the bars overlap. That amber region is the overlap, and inside it either event
could have come first. Their true order is *unknown*. [PAUSE]

And the point that should bother you: nothing in the bare timestamps told you so.
The numbers looked perfectly confident — 200 nanoseconds apart, printed to the
nanosecond. The ambiguity was invisible because the error bar wasn't part of the
data.

That's the problem we're going to fix.

---

## Block 3 — Time as an interval  (8:00 – 13:00)

### Slide 8 — Part 2: A timestamp is an interval  (8:00)

Part two — the mental model. A timestamp is an interval.

### Slide 9 — From a point to an interval  (8:15)

The whole shift is this small.

Instead of saying "the event happened at *t*," we say "the event happened at
*t plus-or-minus U*." [PAUSE]

*U* is the time-uncertainty bound at the moment we observed the event. You can
read the same thing two ways: as *t plus-or-minus U*, or as an *earliest* and a
*latest* — the event happened no sooner than *t minus U* and no later than
*t plus U*. Same interval, two vocabularies; the earliest/latest framing is the
one most timing APIs actually expose.

And once *U* is part of the record, the application can ask questions it simply
could not ask before. Is the ordering between A and B *definite*, or is it
*ambiguous*? Is this time window *fresh enough* to base a compliance decision on?
These become explicit, answerable questions instead of silent assumptions.

### Slide 10 — The ordering rule  (9:30)

Here's the rule that falls out of it.

On the left, the old point model: a single tick on a line. On the right, the
interval model: a band from *t minus U* to *t plus U* — or, in the words on the
slide, from the *earliest* the event could have happened to the *latest*.

The rule: **A is before B *only if* T-A plus U-A is less than T-B minus U-B.**
In earliest/latest terms: A is before B only if the *latest* A could have been is
still earlier than the *earliest* B could have been. Only if the whole interval of
A sits entirely below the whole interval of B.

And if they overlap? The answer is not "wrong." The answer is **ambiguous —
unknown, not wrong.** [PAUSE]

That distinction is the most important idea in this talk. "Unknown" is a valid,
*useful* answer. A system that knows the order is unknown can slow down, widen a
window, ask for confirmation, or flag the result. A system that guesses and calls
it certain just ships a silent error.

### Slide 11 — What uncertainty is — and is not  (11:00)

Let me be precise about what *U* is, because it's easy to over-claim — and this is
where a hostile reviewer will push first.

*U is:* a *computed uncertainty envelope*, right now. It's derived from the
synchronization state plus a few explicitly stated assumptions. And it's an
explicit input to your application's logic.

*U is not:* a statistical confidence interval — not unless you deliberately layer
statistics on top. And, being honest, it is *not* a proven mathematical upper
bound on the true clock error — because we deliberately omit some terms, like link
asymmetry. And it is *not* zero just because PTP reports the port state as "SLAVE."
[PAUSE]

So I'm going to call it an *operational envelope under stated assumptions*, not a
"conservative bound." The moment you name the assumptions — the frequency error is
within some D-max, the asymmetry within some A-max, the offset-estimation error
within some limit — the number becomes defensible. Hand-wave the assumptions and a
reviewer is right to attack it.

---

## Block 4 — Anatomy of uncertainty  (13:00 – 21:00)

### Slide 12 — Part 3: Where does uncertainty come from?  (13:00)

Part three. If *U* is a real number, where does it come from? Let's walk the
stack.

### Slide 13 — Walk the stack, bottom to top  (13:15)

Six layers, bottom to top.

At the bottom, layer one, the *oscillator* alone — it drifts, and it drifts with
temperature. Layer two, the *PHC clock* it feeds — that's where the *offset* from
the reference lives, and its finite *clock resolution*, the granularity of a
single tick. Layer three, the *network* — queueing, routing, and the number of
hops the sync has to cross. Then the *timestamp capture point* — was it taken in
hardware or software?

Then layer five, the *kernel-to-userspace transfer*. The event arrives as a
hardware interrupt, but the kernel doesn't finish the job right there — it defers
the real work to a *softirq* that runs soon, but not instantly — and then the data
has to be *copied* out of kernel memory into your process. Every one of those hops
adds delay between when the event actually happened and when your program can see
it, and because it varies with system load, it shows up as jitter, not a constant
you can subtract out.

And at the top, layer six, the *userspace observation delay*. Even once the data
is in your process, *reading the clock is itself a syscall* — a trip into the
kernel and back — and your thread is at the mercy of the *scheduler*: under load
it can be preempted and parked for microseconds before it gets to run. So the
instant you finally record can trail the real event by an amount you never
measure.

Every one of these layers adds either error or delay. [PAUSE] And here's the
uncomfortable part: only *some* of them expose a metric you can read. "The event
time" means something different at each layer — even when everything reports as
perfectly synced.

But first, the whole budget on one slide.

### Slide 14 — The uncertainty budget: every source  (14:15)

Before we zoom into the layers one by one, here is every source of error that can
widen your interval, grouped four ways.

Two come from the *source clock* itself, and they are different in kind. First,
the grandmaster's *class* — its `clockClass` and `clockAccuracy`. We don't measure
this; the grandmaster *advertises* it, and it gives us a bound on how good the
source is. Second, the *offset from* that grandmaster — and this one we *do*
compute, locally, from the t1–t4 timestamp exchange. But be careful, because this
is the first place a reviewer will attack: `offsetFromMaster` is an *estimate* of
our bias, not a bound on it. A two-nanosecond offset does not mean the true error
is under two nanoseconds. So it enters as the estimated offset *plus* its own
estimation uncertainty — timestamp noise, delay variation, and asymmetry all live
in that second term. One is a quality we're told; the other is an estimate we
compute, with error bars of its own. (And `stepsRemoved` is just the hop count to
the grandmaster — if we attribute error per hop, that's a crude *policy*, not a
physical bound; a transparent clock and a boundary clock fail differently.)

Two come from *our* oscillator, but say these carefully: the PHC is being
frequency-disciplined by ptp4l, so between syncs it does *not* free-run at the raw
crystal tolerance. What we bound is the *residual* frequency error — capped by a
configured D-max — times the age since the last sync. And in the extreme,
*holdover* — that same bound growing when discipline is lost entirely.

Two are about *reading* the clock: the clock's *resolution*, which enters as half
a tick of quantization; and the *capture* of the event itself — where and how it
was stamped — which, and this matters, is a *separate* uncertainty the application
owns, not the daemon.

And two live in the *network*: the delays accumulated across every path element,
whose *estimated mean* PTP compensates — but the estimation error of that mean
does not vanish; and *link asymmetry*, which PTP cannot see. Both fold into that
offset-estimation term. [PAUSE]

So watch that last column. It splits into two owners: U-clock, everything the
daemon can bound; and U-capture, what the application knows about how it stamped
the event. The total event uncertainty is the sum of the two. And none of it is a
proof — it's an envelope under the assumptions we just named.

### Slide 15 — Layers 1–2: oscillator & PHC clock  (14:45)

Layer one, the oscillator. Its stability is measured in parts per billion, and
it's sensitive to temperature — and left to free-run, it drifts.

Layer two is the PHC clock the oscillator feeds — the hardware clock we actually
read. Two things live here. First, `offsetFromMaster` — and I'll say it again
because it's the crux — this is an *estimate* of our offset from the reference,
and the estimate has its own uncertainty. Second, the clock's *resolution* — the
granularity of a single tick, which enters as a half-tick of quantization, and I
mean the *effective* granularity of the NIC clock, not just whatever `clock_getres`
reports. And reading it isn't free either; the read itself has a latency.

The servo *converges* toward zero offset. It never mathematically *reaches* zero.
So PTP believes something about your clock — and that belief is an input to *U*,
not a guarantee about reality.

### Slide 16 — Layer 4: capture point — a separate uncertainty  (16:00)

Now the capture point, because this one surprises people — and because it's a
place the model has to be careful.

First, three things that are easy to blur together. There's *clock uncertainty* —
the envelope we've been building. There's *capture uncertainty* — where and how
you stamped the event. And there's plain *observation latency*. They are not the
same.

Here's the trap. A hardware PHC timestamp in the NIC has the smallest capture
error. A software `SO_TIMESTAMPING` stamp is larger — interrupt and softirq delay.
And `clock_gettime` in your app — people call it the "largest error," but be
careful: the syscall latency does *not* make the returned time wrong. That value
*is* the clock at the read point. It only becomes uncertainty when you claim an
*earlier* event happened at that time — then the event-to-read gap is what counts.

So capture uncertainty is a *separate* term — call it U-capture — that the
application adds on top of the clock envelope. The daemon can't know how you
stamped. And this matters enormously for profiling: your GPU, your NIC, and your
CPU may each
be stamping in a *different domain* — even when the cluster says everything is
synchronized.

### Slide 17 — Layers 3 & 5: network and kernel path  (17:15)

Two more layers, quickly.

Layer three, the network. Every hop — each transparent or boundary clock, each
switch queue — adds delay, and the more hops the sync crosses, the more of it
accumulates. Now the subtlety that trips people up — and here I have to be more
careful than the usual hand-wave. PTP measures and compensates the *estimated*
mean path delay. The mean gets corrected out, yes — but the *estimation error* of
that mean does not vanish. Delay variation, changing path conditions, a stale
delay estimate, and above all link *asymmetry* — the up and down directions
differing — all remain. So I won't say "path delay is gone." I'll say the
estimated mean is compensated, and its residual estimation error, growing with hop
count, folds into the offset-estimation term. PTP doesn't hand us a clean
measurement of it.

And layer five, the kernel path: Linux exposes useful *ingredients* here —
`PTP_SYS_OFFSET` cross-timestamps the PHC against the system clock, and
`SO_TIMESTAMPING` gives you ingress and egress timestamps. But notice what's *not*
a kernel API: the disciplined sync-state itself. That lives only in `ptp4l` in
userspace, and there's no coherent snapshot of it. Remember that — it's exactly
what's *missing*, and I'll come back to it at the end.

### Slide 18 — The layer everyone forgets: staleness  (18:30)

And now the layer that almost every tool forgets. [PAUSE]

Between syncs, the clock's frequency isn't perfectly known — so our *bound* on the
error grows. And I want to phrase this precisely, because it's the second thing a
reviewer will catch. The PHC is being frequency-disciplined; between syncs it does
*not* free-run at the raw crystal tolerance — the last correction stays
programmed. So this isn't "the oscillator drifts 100 microseconds." The honest
statement is: the *residual* frequency error is bounded by a configured D-max, and
our uncertainty grows as that bound times the age since the last sync.

Put in a number: a D-max of 100 parts per million times one second is **100
microseconds**. [PAUSE]

Think about what that means. You can have a *perfect* offset estimate at the
instant a sync arrives — and a moment later that point has already grown into an
interval. Staleness turns a point estimate into a *growing* envelope — an
*attributed* bound, not a measurement of drift.

Most dashboards show you the offset. Very few show you that envelope widening
since the last correction. That gap — that's exactly what the implementation
later in this talk makes explicit.

---

## Block 5 — Turning PTP into a bound  (21:00 – 27:00)

### Slide 19 — Part 4: Turning PTP state into a bound  (21:00)

Part four. Let's turn all of this into an actual number we can compute.

### Slide 20 — PTP answers: what does the protocol believe?  (21:15)

PTP answers exactly one question for us: *what does the protocol believe about my
clock?* We read that belief from four datasets, all through `ptp4l`.

`CURRENT_DATA_SET` gives offset, mean path delay, and steps removed.
`PORT_DATA_SET` gives the port state and the sync interval. `TIME_STATUS_NP` — a
Linux extension — gives the sync ingress time and the grandmaster identity. And
`PORT_HWCLOCK_NP` optionally gives the PHC index.

What PTP does *not* answer is "what is my application-level timestamp error bar?"
That's the part we build on top. And notice one thing that becomes important
later: these are four *separate* datasets, polled independently over the
management interface. There is no single call that hands you a coherent clock-state
at one instant. Hold that thought.

### Slide 21 — Ingress time is the drift anchor  (22:30)

And this is how we build it. The key is that ingress time.

`TIME_STATUS_NP` tells us *when the last sync event actually arrived*, in PHC
time. That timestamp is our *anchor*.

Then the drift term is simple: take the time now, subtract the time at that ingress
anchor, and multiply by the configured drift bound, D-max. That gives an
*attributed* bound on residual frequency error since the anchor. [PAUSE]

But let me flag the honest weakness here, because a careful reviewer will. The
offset comes from `CURRENT_DATA_SET`; the ingress time comes from `TIME_STATUS_NP`.
Those are two different datasets, and the servo state may have moved between them.
I'm treating two non-atomic observations as if they describe one synchronization
event at one epoch. It's a reasonable approximation — but it's an approximation.
And honestly, that snapshot-coherence gap is one of the strongest arguments for
the kernel API I'll propose at the end: Linux doesn't expose a coherent
clock-state at a common observation epoch.

### Slide 22 — The model, stated with its assumptions  (23:45)

So here is the whole model on one slide — and I've written it the way I'd want to
defend it, not the way that sounds cleanest.

Start at the top: the *event* uncertainty splits into two owners. **U-clock**,
which the daemon and library provide, and **U-capture**, which the application
provides. The total is their sum. Keep them separate — the daemon has no idea how
your application stamped its event.

Now U-clock itself. First term: the estimated offset — `offset_est` — the servo's
latest estimate of our bias, left uncorrected. Second, and this is the term people
drop: `U_est`, the *uncertainty of that estimate* — timestamp noise, delay
variation, residual path-delay-estimation error, asymmetry. An offset estimate is
not a bound on the offset; the bound needs this second term. Third: the drift —
age since the anchor times D-max, the attributed residual-frequency bound. And
fourth: half a tick of clock resolution — a quantization term.

And below the line, the assumptions, written out: the frequency error is within
D-max, the asymmetry within A-max, the offset-estimation error within its own
limit. [PAUSE]

I want to be honest about what this is. It is *not* a proven upper bound on true
clock error — I've left terms out and I've made assumptions. It's a *computed
uncertainty envelope under stated assumptions*. Name the assumptions, and it's
defensible. That's the strongest honest claim I can make, and it's the one I'll
stand behind.

### Slide 23 — Sync status is a prerequisite, not a proof  (25:15)

One more piece before we build it: the port state gates whether the bound even
means anything.

In the SLAVE state, we're actively disciplining — the bounds are meaningful. In
`UNCALIBRATED` we're still converging — the bounds are unstable, don't lean on
them. In `LISTENING` or `FAULTY`, don't trust ordering claims at all.

And the interesting one: **when `ptp4l` disconnects.** We hold the last anchor —
and the drift just keeps growing from it. The bound doesn't freeze; it inflates,
honestly reflecting that we're flying on a stale correction. Synchronization
status is a *prerequisite* for trust — it is never a *proof* of it.

---

## Block 6 — A model implementation  (27:00 – 34:00)

### Slide 24 — Part 5: A model implementation  (27:00)

Part five. Let's make it something you can actually run. This is `ptp-uncertainty`
— a small daemon and a client library that I built to visualize the concept, and verify
which data would such an app need to reliably calculate error bounds?

### Slide 25 — Architecture  (27:15)

The shape is deliberately simple.

`ptp4l` runs as it always does. The daemon, `ptp_unc_dmn`, connects to its Unix
management socket and polls offset, delay, and ingress time. It collects that
state and anchors it. Then it publishes a snapshot into POSIX shared memory at
`/ptp_uncertainty`.

On the other side, `libptp_unc.so` maps that shared memory and, at *read time*,
extrapolates the live bound. The application links the library and just asks for
a number. [PAUSE]

Two design choices worth calling out: applications need *no* PTP
And they get a *live* bound, extrapolated to now — not just the
last stale offset snapshot.

### Slide 26 — What the daemon collects  (28:45)

Concretely, the daemon collects offset, delay, and steps removed from
`CURRENT_DATA_SET`; PMC message the port state and sync interval from
 `PORT_DATA_SET`; the ingress time and grandmaster ID from `TIME_STATUS_NP`;
  the PHC index from a ptp4l-custom PORT_HWCLOCK_NP.

A couple of niceties: it can derive its poll interval automatically from the sync
interval — polling at least twice the sync rate — and it can autodetect the PHC
index. You point it at the socket and it configures itself.

### Slide 27 — Client API  (29:45)

You open a handle. Then `ptp_unc_get` gives you the clock uncertainty *at now*.

And here's the important framing: what the daemon returns —
`total_uncertainty_ns` — is **U-clock**, the clock-error envelope. It is *not* the
whole story for an event. The application composes the event uncertainty itself:
U-event equals U-clock plus U-capture, where U-capture is whatever the app knows
about how *it* stamped the event — a NIC hardware timestamp, an `SO_TIMESTAMPING`
stamp, a GPU counter converted to PHC. The daemon can't know that, so it doesn't
pretend to. It gives you the clock half; you add the capture half.

You also get whether you're synchronized, whether `ptp4l` is connected, and
`age_ns`. [PAUSE] One clarification that trips people up: `age_ns` is the freshness
of the *daemon's snapshot* — how long since it last updated shared memory. That is
*not* the drift-anchor age, which is measured from the sync ingress. Two different
clocks of staleness; keep them separate.

### Slide 28 — Behavior under failure = explicit correctness  (31:00)

And this slide is really the whole thesis in code.

When `ptp4l` restarts or drops, the daemon preserves the last valid anchor, sets
`ptp4l_connected` to zero, and lets the drift keep growing from that held anchor.
It does not pretend nothing happened, and it does not blank out.

So your application can write exactly this: if we're not connected to `ptp4l`, *or*
the total uncertainty has exceeded our threshold — mark the event ordering as
untrusted. [PAUSE]

That is what my abstract means by "evaluate temporal correctness *explicitly*."
It's three lines. The application, not the clock, decides what "trustworthy
enough" means for its own job — and the daemon's only responsibility is to keep
the bound honest.

### Slide 29 — Validated at scale: Meta's fbclock  (32:30)

And before I show you my own numbers, I want to prove this isn't a fringe idea.

Meta deployed exactly this model to a fleet of PTP clients. Their API is called
fbclock, and it does not return a timestamp — it returns a *Window of
Uncertainty*: an earliest and a latest. The same interval we've been building all
talk. [PAUSE]

Look at the two columns. Independently, they arrived at the same skeleton: a
daemon that reads `ptp4l` and the PHC, publishes a snapshot into shared memory,
and a small C library that clients link. Same architecture, down to the shared
memory.

Two honest differences, and they're the interesting part. First, the *bound*:
Meta computes a statistical, sigma-based window and targets six-nines certainty; I
default to a conservative worst-case bound. Both are defensible — two points on
the same spectrum. Second, *holdover*: Meta estimates the drift rate empirically,
from the recent history of the clock's frequency adjustments, and I use a single
configured drift bound. [PAUSE]

Hold onto that second difference. Unfortunately, to get the reliable bounds, you'd have
to bring the own temperature and vibration data to estimate oscillator drift — because nothing in the stack hands it to you. Hence the simplified approach was chosen as
giving you the data you can reliably use at scale with a minimum "investment"

 That's not my opinion; that's the largest PTP deployment in the world
telling you what's missing. We come back to it in the last section.

---

## Block 7 — Model behavior across oscillator bounds  (33:00 – 37:00)

### Slide 30 — Part 6: Model behavior across oscillator bounds  (33:00)

Part six. And let me be scrupulously honest about what these next plots are,
because it would be easy to oversell them. I am **not** putting four different
oscillators on the bench. It's the same host, the same `ptp4l`, the same network.
The only thing I change between runs is the daemon's configured drift bound,
D-max — one model parameter. So what you're about to see is the *model's* output
under four oscillator *assumptions*, not four measured crystals. I'd rather you
attack the model than catch me claiming a measurement I didn't make.

### Slide 31 — The bound growing between syncs  (33:30)

*(Show the sawtooth plot.)*

Here it is. That dashed line near the axis is the residual offset floor — tens of
nanoseconds — what's left after the estimated path delay is compensated. [PAUSE]

Now watch the blue line. Every second a sync arrives and the *bound* snaps back
down. Then it climbs again. And I want to be precise about what that climb is: it
is the uncertainty **attributed to potential drift** — age times D-max. It is
*not* a measurement of the clock physically drifting; the PHC is disciplined, its
frequency correction is still programmed. The plot demonstrates the *growth of the
bound*, not observed oscillator drift. Climb, reset, climb, reset. [PAUSE]

That sawtooth is the staleness term from slide eighteen, made visible. The
envelope is widest right before the next sync — and most tools would only show you
the offset, which down here looks like nothing.

### Slide 32 — Same PTP state, four drift bounds  (34:45)

Now the same run, four times — one per configured drift bound — on a log scale,
because the spread is enormous.

Every line rides on the same residual offset floor, tens of nanoseconds, because
the estimated path delay is compensated. Same PTP state, same host. The only thing
that differs is the assumed D-max: an OCXO assumption at 100 parts per billion, a
TCXO at 1 ppm, a quality crystal at 10 ppm, and a basic crystal at 100 ppm. [PAUSE]

Look at the separation. The tight bound barely leaves the floor; the loose bound
swings up past 100 microseconds between syncs. Same protocol, same second. The
envelope is set by the *configured bound* — the assumption you feed the model —
not by anything PTP measured.

### Slide 33 — The envelope, at its worst  (35:45)

One more view — the worst-case moment for each assumption, split into its two
parts: the residual offset estimate in gray, and the attributed drift in color.

For the tight bound, the residual offset and the attributed drift are comparable —
the whole envelope is a few hundred nanoseconds. Loosen the bound and the drift
term takes over: ninety-nine percent, then essentially all of it. [PAUSE]

Same network, same daemon, same model — and the peak envelope runs from about a
third of a microsecond to a hundred and twenty microseconds, decided by the
configured drift bound alone. That's the point, and I'll state it carefully: the
*assumed* residual-frequency bound, not measured holdover, is what dominates
between syncs. Which is exactly why that bound needs to be a first-class,
explicitly-configured input — and why the kernel not exposing a coherent
clock-state to hang it on is the real gap. Hold that for the last section.

---

## Block 8 — The full story: fast time + its uncertainty  (37:00 – 39:30)

### Slide 34 — Part 7: The full story: fast time + its uncertainty  (37:00)

Part seven. This is where the two talks meet.

### Slide 35 — The bridge  (37:15)

Here's the bridge, and it's the second line I want you to remember.

Last year's talk made reading the clock *fast* — the Hermóðr approximation gets
you the device time in tens of nanoseconds instead of microseconds, without the
syscall and PCIe overhead. That's real, and it's powerful. And notice it's built
the same way this daemon is: a background process that cross-timestamps and
estimates drift, a snapshot in shared memory, and a small client library.

What this talk adds is the other half: **it puts an error bar on that time.** [PAUSE]

Fast access gives you the time cheaply. Uncertainty tells you how far to trust it.
A timestamp you can read cheaply *and* trust explicitly — that's a complete time
primitive, and it takes both halves to build it.

### Slide 36 — Fast time + its uncertainty compose  (38:00)

Make it concrete. A fast read alone gives you a low-overhead timestamp — that's
the first row, and it's genuinely valuable. But on its own it's still just a
point: you compare two events point-to-point, you can't tell when the order is
ambiguous, and you can't gate a decision on how trustworthy the time is.

Two events 300 nanoseconds apart, each known to within about 500 nanoseconds — the
fast read alone happily says "A before B." With the uncertainty bound, that
ordering is honestly *ambiguous*, and the system knows it. [PAUSE]

Add uncertainty and every row upgrades. Point comparison becomes *interval*
comparison. Ambiguity becomes *explicit* instead of buried. Decisions can be
*gated* on a threshold over U. And any correlation or merge window can *adapt* to
the live quality of the clock — tight when it's good, wider when it's drifting.
That's fast time and its uncertainty, composed into one primitive.

---

## Block 9 — Kernel APIs: have vs missing  (39:30 – 40:30)

### Slide 37 — Part 8: Linux APIs — what we have, what we lack  (39:30)

Part eight, and I'll keep it short and honest.

### Slide 38 — Ingredients, not the recipe  (39:40)

Let me correct a framing you'll often hear — including from me earlier. The kernel
gives us *ingredients*. On the left: `SO_TIMESTAMPING` for hardware and software
timestamps; `PTP_SYS_OFFSET` to cross-reference the PHC against the system clock;
and `/dev/ptpN` for frequency adjustment and external timestamps.

But notice what is *not* on that list: the `ptp4l` management socket. That's the
whole point — it isn't a kernel API at all. It lives in *userspace*. So the one
thing we actually need — the disciplined PTP sync state — exists only inside
ptp4l, and the only way to get it today is to talk to that daemon out-of-band.

That's the gap I want to close — and the critique of the model earlier actually
sharpens it. The problem isn't merely that the data lives in userspace. It's that
Linux and PTP expose no *coherent* clock-state at a single observation epoch.
Remember slide twenty-one: offset comes from one dataset, ingress from another,
polled independently — I had to stitch non-atomic observations into one "now." So
the primitive I'd add isn't just "expose max_drift_ppb." It's *one atomic snapshot
at a defined epoch*, built on the structure this daemon already publishes:
`master_offset_ns` and `ingress_time_ns` together as the anchor; `max_drift_ppb`
as the assumed frequency-error bound; the grandmaster identity and `steps_removed`
— though I'll be honest that per-hop error is a crude policy, not a physical bound,
since a transparent clock and a boundary clock fail differently. Enough metadata,
at one epoch, to derive an uncertainty envelope under stated assumptions. [PAUSE]

That's a much harder thesis to attack than "give me a drift number." With a
coherent snapshot, any application could compute a live envelope without linking a
PTP stack or scraping a daemon. The harder physical unknowns — oscillator
stability, calibration age — still need operator config; I won't oversell that.
But a coherent clock-state at a defined epoch is a small, concrete thing to build,
and it's the missing recipe.

---

## Block 10 — Close  (40:30 – 41:30)

### Slide 39 — Takeaways  (40:30)

Six things to take with you.

One: timestamps are intervals. Design your systems around *t plus-or-minus U*.

Two, and this is the honest one: U is a *computed envelope under stated
assumptions*, not a proven upper bound. Name the assumptions and it's defensible.

Three: separate the two owners — U-clock, which the daemon bounds, and U-capture,
which the application knows. The event uncertainty is their sum.

Four: staleness is an *attributed* drift bound — age times a configured
frequency-error limit, not measured oscillator drift. It's the term most tools
ignore; don't.

Five: the real missing kernel primitive isn't a drift number — it's a *coherent
clock-state at one observation epoch*, with enough metadata to derive an envelope.

And six, the one that ties the two talks together: fast access gives you the time
cheaply, and uncertainty tells you how far to trust it — fast access to the time
*and* its associated uncertainty.

### Slide 40 — Questions  (41:15)

So: treat time as an interval, and make the error bar part of the data.

The implementation — the daemon, the client library, and the `watch_uncertainty`
monitor — is all available if you want to try it against your own `ptp4l`.

Better profiles need better time — and better time needs error bars. [PAUSE]
Thank you. I'd love to take your questions.

---

## Backup answers (Q&A)

- **Is U a statistical confidence interval?** No — by default it's a conservative
  worst-case bound. You *can* layer statistics on top, but the base model is
  deliberately conservative.
- **Why a 100 ppm default drift?** It's a safe generic bound. In production you
  tune it per oscillator or NIC datasheet — that's exactly the "hardware
  knowledge" the abstract calls out.
- **Does this replace PTP?** No. It *consumes* PTP state; it never disciplines the
  clock. `ptp4l` still does the real work.
- **How does this relate to NTP's root dispersion?** Same philosophy — an explicit
  error budget carried with the time — but different data sources and different
  timescales.
- **What about GPU timestamps?** They live in a separate domain today. Mapping them
  onto the PHC and adding their capture uncertainty is real, open future work.
- **What's the overhead?** The daemon polls at roughly the sync rate; clients read
  from shared memory and do a multiply and a few adds at read time. It's
  negligible next to the workload being profiled.
