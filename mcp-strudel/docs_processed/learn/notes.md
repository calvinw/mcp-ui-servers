# Notes

Pitches are an important building block in many musical traditions.
In Strudel, pitches can be expressed as note names, note numbers or frequencies.
Here's the same pattern written in three different ways:

- `note`: letter notation, good for those who are familiar with western music theory:

  

- `note`: number notation, good for those who want to use recognisable pitches, but don't care about music theory:

  

- `freq`: frequency notation, good for those who want to go beyond standardised tuning systems:

  

Let's look at those in more detail...

## `note` names

Notes names can be notated with the note letter, followed by the octave number. You can notate flats with `b` and sharps with `#`.



By the way, you can edit the contents of the player, and press "update" to hear your change!
You can also press "play" on the next player without needing to stop the last one.

## `note` numbers

If you prefer, you can also use numbers with `note` instead:



These numbers are interpreted as so called [MIDI numbers](https://www.inspiredacoustics.com/en/MIDI_note_numbers_and_center_frequencies), where adjacent whole numbers are one 'semitone' apart.

You could also write decimal numbers to get 'microtonal' pitches (in between the black and white piano notes):



## `freq`

To get maximum freedom, you can also use `freq` to directly control the frequency:



## Hearing and frequency

In the above example, we play A3 (220Hz), C#4 natural (275Hz), E4 (330Hz) and A4 (440Hz), mirroring our previous examples.

But can you hear the difference between these individual frequencies?



How about these?



The higher we go up...



The less distance we can hear between the frequencies!



Why is this? [Human hearing operates logarithmically](https://www.audiocheck.net/soundtests_nonlinear.php).

## From notes to sounds

In this page, when we played a pattern of notes like this:



We heard a simple synthesised sound, in fact we heard a [triangle wave oscillator](https://en.wikipedia.org/wiki/Triangle_wave).

This is the default synthesiser used by Strudel, but how do we then make different sounds in Strudel?

Let's find out in the next page on [Sounds](/learn/sounds).

<br />