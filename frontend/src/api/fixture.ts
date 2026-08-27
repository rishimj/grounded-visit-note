import type { Citation, CitationOffsets, VisitNote } from '../types'

export function splitTranscript(text: string): string[] {
  return text.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n')
}

export function offsetsForQuote(
  lines: string[],
  quote: string,
): CitationOffsets {
  const raw = lines.join('\n')
  const start = raw.indexOf(quote)
  if (start < 0) {
    return { start: 0, end: 0 }
  }
  return { start, end: start + quote.length }
}

export function citation(
  lines: string[],
  quote: string,
  line_numbers: number[],
): Citation {
  return {
    quote,
    line_numbers: [...line_numbers].sort((a, b) => a - b),
    offsets: offsetsForQuote(lines, quote),
  }
}

/** Alvarez-shaped SOAP. Line numbers match docs/transcript_01.txt. */
export function alvarezNote(lines: string[]): VisitNote {
  const q = (quote: string, nums: number[]) => citation(lines, quote, nums)
  return {
    sections: [
      {
        id: 'subjective',
        heading: 'Subjective',
        items: [
          {
            id: 's-1',
            text: 'Morning headaches for about 6–8 weeks, most days, typically 6/10 with one 8/10 episode.',
            citations: [
              q(
                "I've been getting these headaches. Started maybe six weeks ago? Maybe two months. They're mostly in the morning.",
                [4],
              ),
              q("Most mornings. Four or five days a week I'd say.", [6]),
              q(
                'A six usually. There was one Saturday it was more like an eight and I had to lie down for a couple hours.',
                [8],
              ),
            ],
            uncertain: false,
            grounded: true,
          },
          {
            id: 's-2',
            text: 'Stopped lisinopril about three weeks ago because of cough.',
            citations: [
              q("That's the thing. I stopped that one. Maybe three weeks ago.", [
                12,
              ]),
              q("The cough. It was constant, I couldn't sleep.", [14]),
            ],
            uncertain: false,
            grounded: true,
          },
          {
            id: 's-3',
            text: 'Continues metformin twice daily; also fish oil and vitamin D.',
            citations: [
              q(
                'The metformin, still twice a day. And I take a fish oil and a vitamin D my daughter got me.',
                [16],
              ),
            ],
            uncertain: false,
            grounded: true,
          },
          {
            id: 's-4',
            text: 'Metformin dose reported as 500 mg.',
            citations: [q('Um. The five hundred I think. The little white ones.', [18])],
            uncertain: true,
            grounded: true,
          },
        ],
      },
      {
        id: 'objective',
        heading: 'Objective',
        items: [
          {
            id: 'o-1',
            text: 'BP 158/94 right arm, 154/92 left arm.',
            citations: [
              q("Okay, that's one fifty-eight over ninety-four. Let me do the other arm.", [
                20,
              ]),
              q("One fifty-four over ninety-two on the left. That's high, Ms. Alvarez.", [
                21,
              ]),
            ],
            uncertain: false,
            grounded: true,
          },
          {
            id: 'o-2',
            text: 'Heart sounds normal, no murmur; lungs clear; no ankle swelling.',
            citations: [
              q(
                'Heart sounds normal, no murmur. Lungs are clear. Let me look at your ankles. No swelling, that\'s good.',
                [23],
              ),
            ],
            uncertain: false,
            grounded: true,
          },
        ],
      },
      {
        id: 'assessment',
        heading: 'Assessment',
        items: [
          {
            id: 'a-1',
            text: 'Morning headaches may be related to elevated blood pressure.',
            citations: [
              q(
                'It could well be. Morning headaches with pressure like that, they often go together.',
                [23],
              ),
            ],
            uncertain: false,
            grounded: true,
          },
        ],
      },
      {
        id: 'plan',
        heading: 'Plan',
        items: [
          {
            id: 'p-1',
            text: 'Start amlodipine 5 mg daily in the morning; do not restart lisinopril.',
            citations: [
              q(
                "We're not going back to it. I want to start you on amlodipine instead. Five milligrams, once a day, in the morning.",
                [31],
              ),
              q('Start it. If I need to change it I\'ll reach you before the weekend.', [
                37,
              ]),
            ],
            uncertain: false,
            grounded: true,
          },
          {
            id: 'p-2',
            text: 'Stop Advil/ibuprofen; Tylenol as needed up to 3 g/day.',
            citations: [
              q(
                "Tylenol is fine, up to three grams a day. Avoid the ibuprofen, with your kidneys I'd rather not.",
                [39],
              ),
              q("Let's stop that. That may be part of why the pressure's running high", [
                43,
              ]),
            ],
            uncertain: false,
            grounded: true,
          },
          {
            id: 'p-3',
            text: 'Labs today: A1c and BMP (kidney function).',
            citations: [
              q(
                'Yes, A1c and a basic metabolic panel, I want to see your kidney function before I put you on something new.',
                [29],
              ),
            ],
            uncertain: false,
            grounded: true,
          },
          {
            id: 'p-4',
            text: 'Return in 4 weeks with home BP log morning and evening.',
            citations: [
              q(
                'labs downstairs today, and I want to see you back in four weeks with a pressure log.',
                [53],
              ),
              q('Morning and evening, write it down, bring the list.', [55]),
            ],
            uncertain: false,
            grounded: true,
          },
          {
            id: 'p-5',
            text: 'Right knee pain deferred to next visit.',
            citations: [
              q(
                "I don't want to short-change that but we're at time and I want to focus on the pressure today. Put it on the list for next visit",
                [51],
              ),
            ],
            uncertain: false,
            grounded: true,
          },
        ],
      },
    ],
  }
}
