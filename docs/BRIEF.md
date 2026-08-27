# Practice Brief: Grounded Visit Note

**Time: 90 minutes. Any stack. Runs locally.**

Clinicians spend hours a day writing notes from patient visits. An AI can draft the note, but a clinician will not sign a note they cannot verify. Every line in the draft needs to be traceable back to what was actually said.

Build a tool that takes a visit transcript and produces a structured note where the clinician can check any statement against its source.

## Core deliverable

A working local app where a user can:

1. Load a transcript (paste it, upload it, or read it from disk)
2. Generate a structured note from it
3. Click any item in the note and see which transcript lines it came from

The note should have sections. Use SOAP if you want a starting point (Subjective, Objective, Assessment, Plan), but the section scheme is your call.

Two sample transcripts are provided. `transcript_01.txt` is the main one. `transcript_02.txt` is shorter and different in shape.

## Open problems

You are not expected to get to these. Pick based on what you think matters.

- The model sometimes cites a line that does not actually support the claim. What would you do about that?
- Some statements in the transcript are corrected later, contradicted, or never resolved. What should the note do with those?
- A long visit will not fit in one context window.
- The clinician needs to edit the draft before signing. Edits should not silently break the links to source.
- Generation takes time. The user is staring at a blank screen while it runs.
- A note with a wrong medication dose is a patient safety event, not a bug. Does your UI reflect that?
- How would you know if a change to your prompt made the output better or worse?

## Notes

- No real patient data is involved here. The transcripts are synthetic.
- There is no hidden test suite and no reference solution.
- Bring your own model API key.

## What gets discussed at the end

- The plan you stated at the start and whether you held to it
- What you cut and why
- What you asked your AI tools to do, how you checked the output, what you changed
- A live change to something you built
