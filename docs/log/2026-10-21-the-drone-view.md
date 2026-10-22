# 2026-10-21: The drone view

*PC, Windows. The [spec](../specs/2026-10-21-the-drone-view.md), the [plan](../plans/2026-10-21-the-drone-view.md) and the build.*

The project site had grown into a stack of tabs: the drone in 3D, the wiring, every flight, the spec sheet, the library. All the information was there, but you had to go looking for the drone. So I rebuilt the front of it around one idea: the drone is always on screen, in the middle, and everything else changes around it.

There are two modes now. **Inside it** is the home page: the drone turning slowly over a blueprint (classic blueprint blue, a generic quad's drawings, not this drone), with the modules to switch off, a slider to pull it apart, and every wire drawn in 3D. **Fly it** fades the blueprint to white and the drone floats there, playing back the real recorded flights. The other pages (the spec, every step, every flight, Build it, the library, the catalog, the data, the math) live in a small corner menu.

## Every wire, pin to pin

The old 3D view drew the wiring as fat bundled tubes. I wanted each wire, from the pin it starts on to the pin it ends on, so you can pull the drone apart and watch the harnesses stretch.

That needed every pin's position. Two research agents went through the makers' drawings: ARK's STEP models for the GPS and the CANnode, Adafruit's and SparkFun's PCB files, PJRC's, Pololu's, Benewake's and Raspberry Pi's drawings, and ARK's, Holybro's, Matek's and RadioMaster's photos, scaled against their known dimensions to about 0.3 mm. Fourteen parts came out of that with real pin positions. The CJMCU switch board only has a seller's photo, so it's an estimate, and so are my own parts and the things that aren't boards. Every connector in the catalog says which it is.

With the pins placed, 128 wires got drawn, each at its real thickness and in its insulation's color: red power, black ground, light gray signal, yellow CAN. Click a board and its wires light up. Click a wire (or pick it from its harness's list) and the camera glides in to its pin, everything else fades to a ghost, and a card says both ends, the gauge, the length to cut it to, and where its pins came from.

Placing the pins found three real problems:

- **The ESC's motor order isn't PX4's.** Holybro's pads run M1 back right, M2 front right, M3 back left, M4 front left, which is Betaflight's order. PX4 numbers them 1 front right, 2 back left, 3 front left, 4 back right. Wired as the connection list has it, motor 1's leads start at the wrong corner and motor 2's cross the board. The fix is a swap inside the ESC cable, which gets re-pinned anyway, but it touches the motor cut's wiring, so it's waiting for me.
- **The wire routes missed their plugs.** The CAD's routes were rough lines I drew before anyone knew where the plugs were, and they missed by up to 54 mm. The safety monitor's route was 20 mm long; reaching its plugs takes 104. The wiring guide cut each wire to its route with 20 mm spare, so some wires would have come out short. The routes now start and end at the plugs, and each wire is cut to its whole run, plug to plug, branches included.
- **That wire weighs something.** The redrawn routes carry 1.18 m more wire in Base, about 8.7 g, most of it the motors' own leads crossing the board because of the motor order. It goes into the catalog with the motor order decision, so the sizing reruns once instead of twice.

The electrical checks all still pass on the new lengths: 437 in all eight combinations (one check dropped out because a ground pin's sliver of a ground loop now carries under the 1 mA it counts from). The main power path loses 351 mV at 90 A, against 341 before and a 432 mV limit.

## The flights as animations

Fly it plays the real runs, not a live sim: the logged path, attitude and motor speeds of every flown scenario from steps 4 to 7, 198 runs across 32 scenarios, both firmwares where both flew.

A 30 minute battery run can't play at real time, so each run becomes a 15 to 30 second loop. It runs from liftoff to touchdown, so both ends sit near a calm hover, and the first and last 0.8 s ease into exactly that, so the loop joins without a jump. The speed changes on a log scale, so it ramps evenly, and within 1.5 s of anything that happened (a stick step, a failure, the chute firing) it plays at real time. The speed shows beside the drone.

Two things I got wrong first. Failure flags that repeat every few seconds each counted as a moment, so the battery runs looped for almost five minutes; now each kind of event counts once. And I called every hard landing a crash, until I noticed that included every landing under the chute, at 4 m/s. Those now fade out where they came down, and the loop fades back in.

The drone itself never moves. It stays in the middle and turns with its logged attitude, while the world moves past it: a faint ground grid, the trail of where it's been, and only what tells the story. That means the canopy once the chute fires, wind streaks once the wind starts, and the column of rising air in the soar mode run. Each prop turns with its own motor, so when one dies you see it stop.

## The drone looks like a drone now

The old model was boxes in flat colors. The first fix was materials: carbon weave on the frame, anodized bells, each board in its maker's solder mask (PJRC green, SparkFun red, ARK black), matte prints, a blue-wrapped pack. The textures are drawn in code and the reflections come from three.js's own room scene, so nothing is fetched.

Then real shapes, in my own CAD code: boards with chips, JST plugs where the pins research put them and gold header pins at every pin; motors with a base, a copper gap over the windings and a bell with cooling holes; props whose blades twist from steep at the root to flat at the tip, each section at the angle the pitch gives there; lightening slots in the arms.

The rule that kept this safe: detail is a look, never the envelope. The checks, the clearances and the mass spread still use the plain shapes, and I ran the CAD before and after to make sure not one check moved. The twisted props are the one place I held back. Spreading the prop's mass over them moves the whole drone's inertia by 0.07%, and every flight model was made with the flat blades, so the flat ones stay underneath.

It works on a phone too: the drone takes the screen and the controls sit in a drawer along the bottom.

## After my first look

I opened it on my own screen and three things were off. The blueprint was one drawing scaled to cover the window, so on a wide, short screen its labels fell off the bottom and its side view and title block sat under the panel. The panel painted over the menu's list. And the panel itself looked like a form.

The blueprint is now a grid that fills any screen, with each drawing pinned to a corner of the space the panel leaves. The panel reads like an instrument now: what's switched on and whether it meets its targets at the top, the modules as three toggles, one labeled row per control, all in the mono face in small capitals, with thin lines and square corners. Then I took the same look through the rest of the site, so every page has the same bar along the top and the same headings, tables, buttons and lists. One site, one look.

## Fly it, so you can see what's going on

My next look was at Fly it, and it didn't say much. The list was just names, so "lost link" or "sagging pack" meant nothing unless you already knew. And the run did play, but the drone stays in the middle while the world moves, and the world was a plain grid. A plain grid sliding under you looks a lot like a plain grid sitting still.

So now each scenario in the list has a tiny drawing of its own run and its first sentence under the name. The drawing is the path seen from above when the run really goes around something, and its height over time when it doesn't, because a straight out-and-back from above is just a line. In 3D the whole route hangs in the air as a thin gray line, with a curtain of faint lines from it down to the ground every few meters, so you can read its height from any angle. There's a pad with an H where it took off, the last 8 m behind it in spearmint, and a line from the drone down to the spot under it.

Under the drone there's a strip now: what just happened in plain words ("The link to the ground is cut", "The chute fires"), a small map from above with a dot where the drone is, and its height from liftoff to touchdown with a tick at each moment, filling in as it plays. The strip runs along the loop as you watch it, not the run's own clock. The low battery run is 21 minutes of holding still with everything interesting at the two ends, so on the run's clock all the ticks pile up at the edges and the playhead races across the middle. You can click or drag along the strip to jump. On a phone, picking a run closes the drawer, since the drawer covers the drone.

Two bugs turned up along the way. Resizing the window in Fly it, or opening a Fly it link directly, snapped the camera back to the close-up from inside the drone. The fit that frames the drone for Inside it was running in both modes. Now it only runs inside, and Fly it pulls back from the distance that fits the drone, so a link lands in the same framing as walking in. The trail also used to cover the last 4 s of the loop whatever that came to in meters, and at 28 times real time that's a long way. Seen from 2 m away, it fanned out past the camera in big green rays.

## Finer detail

Then I wanted more detail in the drone itself. Task 14 gave the boards their chips and plugs and the motors their bells, but about a dozen parts were still the plain boxes and tubes the checks use. Each of them has a look of its own now, drawn inside the same envelope, so no check moves.

The chute's launcher gets a base flange, a dark band, a neck and a cap. That's my own guess at its shape, since Fruity Chutes publishes no drawing. The HaLow whip gets a nut, a hinge and a taper, and the Remote ID module a two-part case with a seam, a label and an LED. The lidar gets its mounting ears and its two round windows, one it sends from and one it sees with. The camera gets its lens barrel and the ribbon's socket, the HaLow HAT its mini PCIe card, shield can and header, and the Pi's cooler its fins and blower. Each module coupler is an XT30 beside a JST-GH, open toward the half it mates with, and the fuses get their violet body and black heat shrink. The pack gets nickel strips across its cell ends. The frame gets its screw heads, sunk flush into the carbon in the pictures, because a head standing proud would poke outside the frame's envelope.

Drawing the screws turned up a small mistake in my CAD. The two front standoffs sit at the full body's inset, but the plates narrow at the nose, so those standoffs hang about 1 mm past the edge. A real frame wouldn't do that. Moving them changes the solid the checks use, so I left them alone for now and left their screw heads off.

I ran the whole CAD again afterward, and every check and every line of its report came out the same. The biggest change in any number was in the 13th decimal place, which is just rounding. My printed parts don't get looks, since their solid is the part I'd actually print. The site's model is 3.7 MB thinned now, up from 3.2.

One more bug turned up while I looked: on a fresh page load, the view inside the drone fitted the camera to the empty scene before the model had arrived, so the drone came up at about half the size it should be until the window was resized. It fits again once the model is there.

## What's not done

- **The front standoffs,** about 1 mm past the nose's edge in my CAD. They move with the next change that reruns the checks anyway.
- **The makers' own models.** The ARK GPS and CANnode (BSD-3) and the Pi 5 (MIT) are on my machine; the Teensy 4.1's model (its author allows it with credit) is a download I haven't approved yet. None of them are in the site's model yet.
- **The scenery.** The camera and mapping runs fly over the grid alone; the shed, box and trees aren't drawn.
- **The motor order and the 8.7 g,** waiting on me.

## What's next

My review of the whole site, the motor order, and then the makers' models.
