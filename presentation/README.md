# Planimation VFG player

## Run locally

From the repository root, start a static server:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Open [the player](http://127.0.0.1:8000/presentation/). Select **Cabinet Retrieval**
or **Two-Object Transport** from the demo menu, or choose **Open VFG** to read a
local Planimation `.vfg` file. The demos, PNG sprites, and font are bundled.
Playback and video export run in the browser and work offline once the server
is running.

| Control | Shortcut when focus is outside a control |
| --- | --- |
| Play or pause | Space |
| Previous or next step | Left or Right |
| First or final step | Home or End |
| Toggle presentation mode | F |
| Exit presentation mode | Esc |

The timeline and step list jump to settled states. Playback moves continuously
between consecutive states. **Present** hides the inspector and widens the
stage while keeping transport controls and goal progress available. Use your
browser’s full-screen command to hide its chrome.

For new plans, generate the VFG in Planimation or follow the
[Fast Downward replay instructions](../pddl/animations/README.md#replay-a-fast-downward-plan).
The bundled demos are the hosted VFGs generated from the original validated
Fast Downward plans and the preserved animation profile.

## Record a seminar clip

Choose a speed, then click **Export video**. Keep the tab visible until the
download finishes. Export starts from the initial state and holds on the
final frame. The 1920×1080 recording contains the map, scenario title and
goal status. Browser buttons and the step list stay outside the recording.

The player requests H.264 MP4 and falls back to WebM based on the browser’s
recording support. For slide software that requires MP4, convert a WebM
download with FFmpeg:

```sh
ffmpeg -i demo.webm -c:v libx264 -pix_fmt yuv420p -movflags +faststart demo.mp4
```

A browser with limited recording support can use a system screen recorder
in **Present** mode. The exporter records in real time, so keeping the
tab visible matters for a steady frame rate.
[Canvas capture](https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/captureStream),
[recording format support](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder/isTypeSupported_static)

## Implementation choice

| Approach | Tradeoff |
| --- | --- |
| Local fork of Planimation | A small viewport patch could keep its integrated planning, upload and VFG tools. The fork would retain React, PixiJS, and the upstream app lifecycle and would need periodic upstream maintenance. |
| Standalone VFG player | A static page with three JavaScript modules and no package installation. Planimation continues generating VFGs. The local page owns presentation sizing, playback and export. |

The standalone approach fits this repository’s presentation workflow. The
player fits the union of sprite bounds across the plan with a single uniform
scale. The stable camera keeps rooms and labels in view. Sprites interpolate
linearly by name, with original depth and artwork through the transition.
At each state boundary the next VFG frame supplies the new positions and
images. The player's timing is tuned for presentation and independent of
the solver’s action costs. Goals come from the VFG’s recorded subgoal
metadata, so imported files with missing metadata show a final frame without
a goal claim.
[Planimation frontend](https://github.com/planimation/Frontend-JS),
[hosted-player interpolation](https://github.com/planimation/Frontend-JS/blob/b6ad236684e6338eeab86933077df1c5f811e8f3/src/pages/PageFour/index.js)

## Validation

Chrome at device scale factor 1, with both demos loaded from the local server.
The map fit the full scene with no viewport scrolling at either resolution.

| Browser viewport | Playback stage | Map width | Stage width / area used | Map width in Present |
| --- | --- | ---: | ---: | ---: |
| 1920×1080 | 1120×894 | 842 px | 75.2% / 70.8% | 894 px |
| 1366×768 | 746×582 | 552 px | 74.0% / 70.2% | 602 px |

The robot occupies about 160 px and 105 px at the two resolutions. The
book and laptop sprites are about 52 px and 34 px, with their icons distinct
on both grippers and on the table. Room label font sizes scale to roughly
31 px and 20 px. Readability was assessed from the browser captures.

| Scenario | Viewport | Initial | Intermediate | Final |
| --- | --- | --- | --- | --- |
| Cabinet Retrieval | 1920×1080 | [Closed](evidence/cabinet-retrieval-1920x1080-initial.jpg) | [Shelf open](evidence/cabinet-retrieval-1920x1080-intermediate.jpg) | [Book delivered](evidence/cabinet-retrieval-1920x1080-final.jpg) |
| Cabinet Retrieval | 1366×768 | [Closed](evidence/cabinet-retrieval-1366x768-initial.jpg) | [Shelf open](evidence/cabinet-retrieval-1366x768-intermediate.jpg) | [Book delivered](evidence/cabinet-retrieval-1366x768-final.jpg) |
| Two-Object Transport | 1920×1080 | [Items in Office](evidence/two-object-transport-1920x1080-initial.jpg) | [Both grippers loaded](evidence/two-object-transport-1920x1080-intermediate.jpg) | [Both items on table](evidence/two-object-transport-1920x1080-final.jpg) |
| Two-Object Transport | 1366×768 | [Items in Office](evidence/two-object-transport-1366x768-initial.jpg) | [Both grippers loaded](evidence/two-object-transport-1366x768-intermediate.jpg) | [Both items on table](evidence/two-object-transport-1366x768-final.jpg) |

[Presentation mode screenshot](evidence/presentation-mode-1920x1080.jpg)

Browser checks covered pause and resume during a move, 2× speed,
previous and next navigation, goal progression, presentation mode, local
door and handover imports, and recovery from a malformed file. Both demos
exported as 1920×1080 H.264 MP4 at about 30 fps and their final frames decoded
with the goal reached. The existing profile, sprite source, documentation
and evidence match their pre-player checksums. Planning inputs match the
base branch.

The four VFG regression tests run with Node’s built-in test runner:

```sh
node --test presentation/vfg.test.mjs
```
