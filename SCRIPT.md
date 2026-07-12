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
something: for most of my career, I treated time as a solved problem. You call
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

Let me be precise about what *U* is, because it's easy to over-claim.

*U is:* a conservative bound on the clock error right now. It's derived from
measurable synchronization state plus a few configured limits. And it's an
explicit input to your application's logic.

*U is not:* a statistical confidence interval — not unless you deliberately layer
statistics on top. It's not a substitute for designing good clocks. And crucially,
it is *not* zero just because PTP reports the port state as "SLAVE." [PAUSE]

The spirit here is conservatism. We want a defensible upper bound we can stand
behind, not an optimistic best guess.

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
measure, locally, from the t1–t4 timestamp exchange. That measured offset is the
`|offset|` term that goes straight into the bound. One is a quality we're told; the
other is an offset we compute — keep them separate. (And `stepsRemoved` is 
the hop count, the number of boundary clocks between the
grandmaster, for which we may also want to assume some static value.)

Two come from *our* oscillator: its free-run *drift* between sync messages, and,
in the extreme, *holdover* — the drift that keeps accumulating when discipline is
lost entirely.

Two are about *reading* the clock: the *read delay* — the latency of actually
reading a PHC or calling `clock_gettime` — and the clock's *resolution*, the
granularity of the tick itself.

And two live in the *network*: the delays *accumulated across every path element*
— each transparent or boundary clock and every queue on the way — and *link
asymmetry*, where the up and down directions differ. [PAUSE]

Watch the last column. Some of these we fold straight into the bound; PTP
*compensates* the mean path delay for us; and one — link asymmetry — PTP simply
cannot see, so it stays a conservative gap. Now let me pull out the ones that
dominate.

### Slide 15 — Layers 1–2: oscillator & PHC clock  (14:45)

Layer one, the oscillator. Its stability is measured in parts per billion, and
it's sensitive to temperature — and left to free-run, it drifts.

Layer two is the PHC clock the oscillator feeds — the hardware clock we actually
read. Two things live here. First, `offsetFromMaster` — and I want to stress this
is an *estimate* of our offset from the reference. Second, the
clock's *resolution* — the granularity of a single tick, the smallest difference
it can even represent. And reading it isn't free either; the read itself has a
latency.

The servo *converges* toward zero offset. It never mathematically *reaches* zero.
So PTP believes something about your clock — and that belief is an input to *U*,
not a guarantee about reality.

### Slide 16 — Layer 4: where was the timestamp taken?  (16:00)

Now the capture point, because this one surprises people.

The same "event time" has wildly different error depending on where you stamped
it. A hardware PHC timestamp in the NIC has the smallest error. A software
`SO_TIMESTAMPING` stamp is larger — it's delayed by interrupt and softirq
handling. And a plain `clock_gettime` in your application is the largest — it eats
syscall overhead and scheduling jitter.

This matters enormously for profiling. Your GPU, your NIC, and your CPU may each
be stamping in a *different domain* — even when the cluster says everything is
synchronized.

### Slide 17 — Layers 3 & 5: network and kernel path  (17:15)

Two more layers, quickly.

Layer three, the network. Every hop — each transparent or boundary clock, each
switch queue — adds delay, and the more hops the sync crosses, the more of it
accumulates. Now the subtlety that trips people up: PTP *measures* the mean path
delay and *compensates* for it inside the offset — so the mean itself is not
uncertainty; it's already corrected out. What's left is link *asymmetry*: when the
up and down directions differ, on fabrics with asymmetric links and leaf-switch
queueing, and it grows with hop count. That residual is a real source, but we
don't get a clean measurement of it, so it stays out of the bound.

And layer five, the kernel path: Linux actually exposes a lot of useful data here
— but not as one tidy package. `PTP_SYS_OFFSET` cross-timestamps the PHC against
the system clock. `SO_TIMESTAMPING` gives you ingress and egress timestamps. The
`ptp4l` management API gives you offset, delay, and ingress time. The ingredients
are all there. Remember that — I'll come back to what's *missing* at the end.

### Slide 18 — The layer everyone forgets: staleness  (18:30)

And now the layer that almost every tool forgets. [PAUSE]

Between PTP updates, the clock drifts. That's it. That's the whole idea, and it's
the one people skip.

The drift uncertainty is elapsed time times the maximum drift rate. Put in a
number: 100 parts per million times one second is **100 microseconds**. [PAUSE]

Think about what that means. You can have a *perfect* offset at the instant a sync
message arrives — and a moment later that perfect point has already grown into an
interval. Staleness turns a point measurement into a *growing* interval.

Most dashboards show you the offset. Very few show you that interval widening
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
That's the part we build on top.

### Slide 21 — Ingress time is the drift anchor  (22:30)

And this is how we build it. The key is that ingress time.

`TIME_STATUS_NP` tells us *when the last sync event actually arrived*, in PHC
time. That timestamp is our *anchor*.

Then the drift term is simple: take the time now, subtract the
time at that ingress anchor, and multiply by a worst-case drift bound in parts per
billion. [PAUSE]

That's the mechanism that makes staleness concrete. Uncertainty grows between sync
messages — even when the offset number on the screen is sitting perfectly flat.

### Slide 22 — The formula  (23:45)

So here is the whole model on one slide.

**Total uncertainty is the sum of three residual terms — the drift, the clock
resolution, and the capture-point error.** [PAUSE]

The first and biggest is *drift* — the staleness we just built, growing since the
last sync. The second is *clock resolution* — you can never place an event more
finely than a single tick, so that granularity is a hard floor under the bound.
And the third is the *capture-point error* — where the timestamp was actually
taken: a hardware stamp in the NIC is tight, a software `SO_TIMESTAMPING` stamp or
a plain `clock_gettime` in your app is looser.

Notice what's *not* in the sum. The mean path delay isn't here — PTP measures and
compensates it inside the offset, so adding it would double-count. And the offset
itself is a *correction we apply* to get our best estimate of the time, not an
uncertainty we add on top; what's left after that correction is these three
residual terms. The one thing we stay deliberately conservative about is path
*asymmetry* — the up and down directions differing — which PTP doesn't hand us, so
we leave it out and treat it as a known gap.

A worked number: 50 nanoseconds of drift, 8 nanoseconds of resolution, and about
40 nanoseconds of capture-point error — call it a hundred-nanosecond bound. That
total is the half-width of the interval you attach to your timestamp.

I want to be honest about what this is: it's a *practical* model. It is not a full
Allan-deviation analysis of your oscillator. It's a conservative, computable bound
built from the data we actually have — and that's exactly what makes it
usable in production.

### Slide 23 — Sync status is a prerequisite, not a proof  (25:15)

One more piece before we build it: the port state gates whether the bound even
means anything.

In `SLAVE` state we're actively disciplining — the bounds are meaningful. In
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
— a small daemon and a client library.

### Slide 25 — Architecture  (27:15)

The shape is deliberately simple.

`ptp4l` runs as it always does. Our daemon, `ptp_unc_dmn`, connects to its Unix
management socket and polls offset, delay, and ingress time. It collects that
state and anchors it. Then it publishes a snapshot into POSIX shared memory at
`/ptp_uncertainty`.

On the other side, `libptp_unc.so` maps that shared memory and, at *read time*,
extrapolates the live bound. Your application links the library and just asks for
a number. [PAUSE]

Two design choices worth calling out: applications need *no* PTP code and *no*
direct PHC access. And they get a *live* bound, extrapolated to now — not just the
last stale offset snapshot.

### Slide 26 — What the daemon collects  (28:45)

Concretely, the daemon collects offset, delay, and steps removed from
`CURRENT_DATA_SET`; the port state and sync interval from `PORT_DATA_SET`; the
ingress time and grandmaster ID from `TIME_STATUS_NP`; and optionally the PHC
index.

A couple of niceties: it can derive its poll interval automatically from the sync
interval — polling at least twice the sync rate — and it can autodetect the PHC
index. You point it at the socket and it configures itself.

### Slide 27 — Client API  (29:45)

The client side is four calls.

You open a handle. Then `ptp_unc_get` gives you the uncertainty *at now*. Or
`ptp_unc_get_at` gives it to you at a specific monotonic timestamp — useful when
you captured an event earlier and want the bound *as it was then*.

Out of that you get `total_uncertainty_ns`, the `drift_ns` component broken out,
whether you're synchronized, whether `ptp4l` is connected, and `age_ns`. [PAUSE]

One clarification that trips people up: `age_ns` is the freshness of the *daemon's
snapshot* — how long since the daemon last updated shared memory. That is *not*
the same as the drift term, which is measured from the sync ingress anchor. Two
different clocks of staleness; keep them separate.

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
from the recent history of the clock's frequency adjustments, and then calibrates
it with temperature and vibration telemetry. I use a single configured drift
bound. [PAUSE]

Hold onto that second difference. Meta had to bring their own temperature and
vibration data to estimate oscillator drift — because nothing in the stack hands
it to you. That's not my opinion; that's the largest PTP deployment in the world
telling you what's missing. We come back to it in the last section.

---

## Block 7 — Measured on real oscillators  (33:00 – 37:00)

### Slide 30 — Part 6: Measured on real oscillators  (33:00)

Part six. Everything so far has been a model. Let me show you the model running
against real hardware — because this is the part that turns "staleness" from a
slide into a number you can see move.

Everything from here is captured with the `watch_uncertainty` tool logging the
daemon against a live `ptp4l`. Same host, same network. The only thing I change
between runs is the worst-case drift bound — which is exactly how you'd model a
better or worse oscillator.

### Slide 31 — Staleness in action  (33:30)

*(Show the sawtooth plot.)*

Here it is. This is a real capture. That dashed line sitting almost on the axis is
the offset floor — just tens of nanoseconds. Remember, PTP compensates the path
delay, so it's gone; there's essentially nothing under the curve but offset.
[PAUSE]

Now watch the blue line. Every second, a sync message arrives, and the
uncertainty snaps back down to essentially zero. Then, immediately, it starts
climbing again — pure drift, because the clock is drifting and no correction has
arrived yet. Climb, reset, climb, reset. [PAUSE]

That sawtooth *is* staleness. Remember slide eighteen, where I claimed a perfect
offset becomes a growing interval a moment later? There it is, measured. The
interval is widest right before the next sync — and most tools would only ever
show you the offset, which down here looks like nothing.

### Slide 32 — Same PTP, four oscillators  (34:45)

Now the same run, four times, one per oscillator class — and I've put it on a log
scale, because the spread is enormous.

Every one of these lines rides on the same tiny offset floor — tens of
nanoseconds — because the path delay is compensated away. Same offset, same
network. The only difference is the drift bound: an OCXO-class part down at
100 parts per billion, a TCXO at 1 ppm, a standard crystal at 10 ppm, and a basic
crystal at 100 ppm. [PAUSE]

Look at the separation. The OCXO barely leaves the floor — its line stays down in
the tens of nanoseconds. The basic crystal swings up past 100 microseconds between
sync messages. Same protocol. Same second. The envelope of your uncertainty is set
by the oscillator, not by PTP.

### Slide 33 — The budget, at its worst  (35:45)

One more view — the worst-case moment in each run, broken into its two parts: the
residual offset in gray, and the drift term in color.

For the OCXO, offset and drift are comparable — the whole budget is under three
hundred nanoseconds either way. But move to a standard crystal and drift is
*ninety-nine percent* of the budget; on the basic crystal it's essentially all
drift. [PAUSE]

Same network, same daemon, same formula — and the peak bound runs from about a
third of a microsecond to a hundred and twenty microseconds, decided entirely by
the crystal on the board. This is the single most important empirical point in the
talk: between sync messages, oscillator holdover — not the protocol — decides
whether your bound is a fraction of a microsecond or over a hundred. Hold that
thought for the very last section, because it's exactly the number the kernel
won't give you.

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

Linux gives us the ingredients. On the left: `SO_TIMESTAMPING` for hardware and
software timestamps; `PTP_SYS_OFFSET` to cross-reference the PHC against the
system clock; the `ptp4l` management socket for offset, delay, and ingress; and
`/dev/ptpN` for frequency adjustment.

But look at the right column — what's *missing*. The kernel does not hand you the
oscillator's stability, its Allan deviation. It doesn't tell you the age of the
factory calibration or the temperature model. It doesn't give you a bound on PHC
read latency. And there is no single, standardized "staleness since the last
discipline event" you can just query. [PAUSE]

This is exactly the conclusion in my abstract: the *frequency offset* is
available, but oscillator stability and calibration staleness are not. So a
precise bound today still depends on operator configuration and hardware-specific
knowledge. And you just *saw* how much that missing term matters — the crystal
alone drove the bound from a fraction of a microsecond to over a hundred. I'm not
going to oversell the automation — the kernel gives you the ingredients, but you
still have to bring part of the recipe.

---

## Block 10 — Close  (40:30 – 41:30)

### Slide 39 — Takeaways  (40:30)

Five things to take with you.

One: timestamps are intervals. Design your systems around *t plus-or-minus U*.

Two: PTP provides the inputs, but it is not a complete uncertainty model on its
own.

Three: staleness — drift since the last sync — is the term most tools ignore.
Don't ignore it.

Four: explicit bounds enable explicit correctness — for ordering *and* for
compliance.

And five, the one that ties the two talks together: fast access gives you the
time cheaply, and uncertainty tells you how far to trust it — fast access to the
time *and* its associated uncertainty.

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
