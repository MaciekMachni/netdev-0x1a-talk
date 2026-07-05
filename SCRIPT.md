# Making Time Uncertainty a First-Class Concept in Linux Timing — Speaking Script

Full spoken script for the 34-slide deck
(`time-uncertainty-error-bar.pptx`). Written to run **~40 minutes** at a calm
pace (~135 words/min). Timing cues are cumulative. Text in *(parentheses italics)*
is stage direction, not spoken.

Delivery notes:
- Pause at every `[PAUSE]`. Silence sells the interval idea.
- The three anchor lines to land hard: **"unknown, not wrong"** (slide 10),
  **the formula** (slide 21), and **"sync aligns, uncertainty qualifies"** (slide 29).
- If you are running long, cut the second half of slide 30 and skip slide 5's
  last sub-point. Do not cut the staleness slide (17) or the formula (21).

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

You may have seen — or will see — the companion talk on profiling AI clusters.
It's worth drawing the line between the two, because they're two halves of the
same story.

That talk asks: *how do we align events across nodes?* It's about PTP
synchronizing a whole cluster so timestamps mean the same thing everywhere. It's
"can I trace this workload?"

This talk asks a narrower, sharper question: *what is the error bar on a single
timestamp?* It's "can I trust this ordering — yes or no?"

Here's the relationship in one sentence: **synchronization gives you alignment;
uncertainty tells you the limits of that alignment.** Hold onto that. I'll come
back to it at the end.

---

## Block 2 — Precise ≠ correct  (3:00 – 8:00)

### Slide 4 — Part 1: Precise is not the same as correct  (3:00)

Part one. The premise: precise is not the same as correct.

### Slide 5 — We spent a decade chasing precision  (3:15)

We have spent roughly a decade chasing precision, and we won.

Sub-microsecond PTP is now normal on data-center and AI fabrics. Hardware
timestamping is built into NICs, SmartNICs, DPUs. We routinely capture GPU traces
that span thousands of ranks across a cluster.

The clocks got dramatically better. And here's the catch: **the better our clocks
got, the more we trusted them — implicitly.** [PAUSE]

Precision raised our *confidence* faster than it raised our *correctness*. We
started treating "the clock is very precise" as if it meant "the timestamp is
exactly right." Those are not the same statement.

### Slide 6 — Three ways timestamps quietly mislead  (4:30)

That gap shows up in three places.

*Ordering.* We claim A came before B — but if the two intervals overlap, the true
order is simply unknown.

*Causality.* We claim A caused B — but a small offset between two nodes can flip
the apparent order and manufacture a cause that never existed.

*Compliance.* We claim a log is correctly ordered — but if we can't bound the
error, we can't *prove* that ordering is defensible. And auditors care about
defensible ordering, not about how many nanoseconds we can print.

### Slide 7 — Two events 200 ns apart, ±150 ns  (5:45)

Let me make it concrete. [PAUSE]

Two events. They're 200 nanoseconds apart. But each timestamp is only known to
within plus-or-minus 150 nanoseconds.

Their true order is *unknown*. [PAUSE] The intervals overlap — either one could
have come first.

And the point that should bother you: nothing in that timestamp told you so. The
numbers looked perfectly confident. 200 nanoseconds apart, printed to the
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

*U* is the time-uncertainty bound at the moment we observed the event.

And once *U* is part of the record, the application can ask questions it simply
could not ask before. Is the ordering between A and B *definite*, or is it
*ambiguous*? Is this time window *fresh enough* to base a compliance decision on?
These become explicit, answerable questions instead of silent assumptions.

### Slide 10 — The ordering rule  (9:30)

Here's the rule that falls out of it.

On the left, the old point model: a single tick on a line. On the right, the
interval model: a band from *t minus U* to *t plus U*.

The rule: **A is before B *only if* T-A plus U-A is less than T-B minus U-B.**
Only if the whole interval of A sits entirely below the whole interval of B.

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

At the bottom, the *oscillator and PHC hardware* — it drifts, and it drifts with
temperature. Above that, the *PTP servo* that disciplines the clock — offset and
delay. Then *network path asymmetry* — queueing and routing. Then the *timestamp
capture point* — was it taken in hardware or software? Then the *kernel-to-
userspace transfer* — interrupts, softirqs, a copy. And at the top, the
*userspace observation delay* — the syscall and the scheduler.

Every one of these layers adds either error or delay. [PAUSE] And here's the
uncomfortable part: only *some* of them expose a metric you can read. "The event
time" means something different at each layer — even when everything reports as
perfectly synced.

Let me pull out the ones that matter most.

### Slide 14 — Layers 1–2: hardware & sync offset  (14:45)

The oscillator first. Its stability is measured in parts per billion, and it's
sensitive to temperature. Even reading the hardware clock has a latency.

Then PTP sits on top and gives us estimates — and I want to stress the word
*estimates*, not truths. `offsetFromMaster` is an *estimate* of our clock offset.
`meanPathDelay` is an *estimate* of the path asymmetry. `stepsRemoved` tells us
how far we are from the grandmaster.

The servo *converges* toward zero offset. It never mathematically *reaches* zero.
So PTP believes something about your clock — and that belief is an input to *U*,
not a guarantee about reality.

### Slide 15 — Layer 4: where was the timestamp taken?  (16:00)

Now the capture point, because this one surprises people.

The same "event time" has wildly different error depending on where you stamped
it. A hardware PHC timestamp in the NIC has the smallest error. A software
`SO_TIMESTAMPING` stamp is larger — it's delayed by interrupt and softirq
handling. And a plain `clock_gettime` in your application is the largest — it eats
syscall overhead and scheduling jitter.

This matters enormously for profiling. Your GPU, your NIC, and your CPU may each
be stamping in a *different domain* — even when the cluster says everything is
synchronized.

### Slide 16 — Layers 3 & 5: network and kernel path  (17:15)

Two more layers, quickly.

The network: remember `meanPathDelay` is a *mean*. It is not a constant.
Congestion spikes it. On AI fabrics you get asymmetric up and down links and
queueing on a leaf switch — the delay moves around under you.

And the kernel: Linux actually exposes a lot of useful data here — but not as one
tidy package. `PTP_SYS_OFFSET` cross-timestamps the PHC against the system clock.
`SO_TIMESTAMPING` gives you ingress and egress timestamps. The `ptp4l` management
API gives you offset, delay, and ingress time. The ingredients are all there.
Remember that — I'll come back to what's *missing* at the end.

### Slide 17 — The layer everyone forgets: staleness  (18:30)

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

### Slide 18 — Part 4: Turning PTP state into a bound  (21:00)

Part four. Let's turn all of this into an actual number we can compute.

### Slide 19 — PTP answers: what does the protocol believe?  (21:15)

PTP answers exactly one question for us: *what does the protocol believe about my
clock?* We read that belief from four datasets, all through `ptp4l`.

`CURRENT_DATA_SET` gives offset, mean path delay, and steps removed.
`PORT_DATA_SET` gives the port state and the sync interval. `TIME_STATUS_NP` — a
Linux extension — gives the sync ingress time and the grandmaster identity. And
`PORT_HWCLOCK_NP` optionally gives the PHC index.

What PTP does *not* answer is "what is my application-level timestamp error bar?"
That's the part we build on top.

### Slide 20 — Ingress time is the drift anchor  (22:30)

And this is how we build it. The key is that ingress time.

`TIME_STATUS_NP` tells us *when the last sync event actually arrived*, in PHC
time. That timestamp is our *anchor*.

Then the drift term is simple: take the monotonic time now, subtract the monotonic
time at that ingress anchor, and multiply by a worst-case drift bound in parts per
billion. [PAUSE]

That's the mechanism that makes staleness concrete. Uncertainty grows between sync
messages — even when the offset number on the screen is sitting perfectly flat.

### Slide 21 — The formula  (23:45)

So here is the whole model on one slide.

**Total uncertainty equals the absolute offset, plus the absolute path delay, plus
the drift.** [PAUSE]

Three terms. The offset — how far PTP thinks we are from the master. The path
delay — the asymmetry component. And the drift — the staleness since the last
sync.

A worked number: offset of 80 nanoseconds, delay of 120, drift of 50 — total 250
nanoseconds. That 250 is the half-width of the interval you attach to your
timestamp.

I want to be honest about what this is: it's a *practical* model. It is not a full
Allan-deviation analysis of your oscillator. It's a conservative, computable bound
built from the data PTP actually gives us — and that's exactly what makes it
usable in production.

### Slide 22 — Sync status is a prerequisite, not a proof  (25:15)

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

### Slide 23 — Part 5: A model implementation  (27:00)

Part five. Let's make it something you can actually run. This is `ptp-uncertainty`
— a small daemon and a client library.

### Slide 24 — Architecture  (27:15)

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

### Slide 25 — What the daemon collects  (28:45)

Concretely, the daemon collects offset, delay, and steps removed from
`CURRENT_DATA_SET`; the port state and sync interval from `PORT_DATA_SET`; the
ingress time and grandmaster ID from `TIME_STATUS_NP`; and optionally the PHC
index.

A couple of niceties: it can derive its poll interval automatically from the sync
interval — polling at least twice the sync rate — and it can autodetect the PHC
index. You point it at the socket and it configures itself.

### Slide 26 — Client API  (29:45)

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

### Slide 27 — Behavior under failure = explicit correctness  (31:00)

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

*(Optional live demo here, ~3 min: run `watch_uncertainty`, disturb `ptp4l`, show
`ptp4l_connected=0` with total uncertainty climbing, then the CSV plot. Have a
pre-recorded plot ready — conference Wi-Fi rarely carries clean PTP.)*

---

## Block 7 — Payoff: AI cluster profiling  (34:00 – 38:00)

### Slide 28 — Part 6: Payoff: profiling AI clusters  (34:00)

Part six. Why does any of this matter at scale? This is where the two talks meet.

### Slide 29 — The bridge  (34:15)

Here's the bridge, and it's the second line I want you to remember.

The companion talk shows that PTP *aligns* cross-node events — it puts every GPU,
every NIC, every rank on a common timeline. That's real, and it's powerful.

What uncertainty adds is this: **it tells you *when* that alignment can actually
carry a causal claim.** [PAUSE]

Synchronization solves *alignment*. Uncertainty solves the *epistemic limits* of
that alignment — the point past which "these two events line up" stops being
evidence of anything.

### Slide 30 — 512-GPU trace: what bounds add  (35:15)

Make it concrete with a 512-GPU training run, fully PTP-synced.

The profiler sees rank 42 launch a kernel at time T, and rank 7 stall 300
nanoseconds later. The tempting conclusion: the launch caused the stall. But if
the uncertainty on each node is around 500 nanoseconds, that 300-nanosecond gap is
*inside the error bars*. The ordering is ambiguous. "Launch caused stall" is
false causality — and chasing it is wasted engineering time. [PAUSE]

Look at the table. With sync alone you *can* align traces visually — that's the
first row, and it's genuinely useful. But merging cross-node spans is fragile;
bottleneck detection is heuristic; ordering disputes stay hidden; your merge
windows are fixed guesses.

Add the uncertainty bound and every one of those upgrades. Span merging becomes
*confidence-gated*. Bottleneck claims become *defensible*. Ambiguity becomes
*explicit* instead of buried. And your trace-correlation window can *adapt* to the
live quality of synchronization — tight when the clocks are good, wider when
they're drifting.

---

## Block 8 — Kernel APIs: have vs missing  (38:00 – 39:00)

### Slide 31 — Part 7: Linux APIs — what we have, what we lack  (38:00)

Part seven, and I'll keep it short and honest.

### Slide 32 — Ingredients, not the recipe  (38:10)

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
knowledge. I'm not going to oversell the automation — the kernel gives you the
ingredients, but you still have to bring part of the recipe.

---

## Block 9 — Close  (39:00 – 40:00)

### Slide 33 — Takeaways  (39:00)

Five things to take with you.

One: timestamps are intervals. Design your systems around *t plus-or-minus U*.

Two: PTP provides the inputs, but it is not a complete uncertainty model on its
own.

Three: staleness — drift since the last sync — is the term most tools ignore.
Don't ignore it.

Four: explicit bounds enable explicit correctness — for ordering *and* for
compliance.

And five, the one that ties the two talks together: for AI profiling,
synchronization *aligns* your data, and uncertainty *qualifies* your causality.

### Slide 34 — Questions  (39:45)

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
