# Style guide

How everything in this project looks: renders, CFD images, charts, clips and post graphics. Locked 2026-10-13. The machine-readable version (for scripts) is [media/style.yaml](../media/style.yaml).

## The look: wind tunnel

Black background and bright data, like smoke in a wind tunnel at night. The data is the light source; everything else stays out of its way.

## Colors

| Role | Name | Hex | Used for |
|---|---|---|---|
| Background | Tunnel black | `#0B0B0B` | Every post, render background, chart background |
| Text | Chalk | `#F4F4F2` | Titles, body text, the drone's line work |
| Accent | Spearmint | `#3DDC97` | The project's color: key numbers, highlights, streamlines in illustrations |
| Pop | Magenta | `#E64FA0` | One thing per image that has to jump out |
| Muted | Fog | `#B4B2A9` | Captions, axis labels, secondary info |
| Lines | Graphite | `#2C2C2A` | Gridlines, dividers, panel edges |

The rules:
- **Spearmint is the project's color.** If an image only gets one accent, it's spearmint.
- **Magenta gets used once per image, at most.** If everything pops, nothing does.

## Data colors

- **CFD fields (pressure, velocity, anything continuous): turbo.** It looks like the classic CFD rainbow people expect, but it doesn't invent sharp edges the way the old "jet" map does. ParaView and matplotlib both ship it.
- **Every CFD image gets a color bar, with units.** Pressure in Pa, speed in m/s.
- **Charts comparing things** (designs, parts, setups) use spearmint for the one that matters and fog for the rest. Magenta is for the one that failed, or the one that won.
- **Pass/fail:** spearmint for pass, magenta for fail. Never red and green.

## Type

All free (Open Font License, on Google Fonts):

| Use | Font |
|---|---|
| Headlines | Space Grotesk, medium |
| Body and captions | Inter, regular |
| Numbers, units, data labels | JetBrains Mono |

## Sizes

| Format | Pixels | Where |
|---|---|---|
| 4:5 portrait | 1080×1350 | Default for posts. Works on LinkedIn and Instagram. |
| 1:1 square | 1080×1080 | When the image is naturally square |
| 9:16 vertical | 1080×1920 | Instagram Reels and Stories |
| 16:9 | 1920×1080 | Video, and wide CFD shots |
| PDF carousel | 1080×1350 pages | LinkedIn document posts |

## Layout for post graphics

- 64 px margins on a 1080 px wide image.
- **Top:** project name, small, in chalk.
- **Middle:** the visual. It gets most of the space.
- **Bottom:**
  - one big number or a short headline in spearmint
  - a caption in fog underneath
  - a small credit line: `Extra 15pc Gum · github.com/TheAaravSikriwal/extra-15pc-gum`
- One idea per image. If it needs two ideas, it's a carousel.

## Don'ts

- No fake glow, lens flares or drop shadows. The data is bright enough.
- No stock-photo drones. Everything shown is this drone, or clearly labeled as something else.
- No unlabeled colors. If color means something, there's a color bar or a legend.
- **Placeholder numbers never go out.** Every number in a post comes from a real run, and the caption says which run.
