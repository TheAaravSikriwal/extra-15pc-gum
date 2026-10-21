# 2026-10-21: Structure, first pass

*PC, Windows. The structure side track: the [spec](../specs/2026-10-21-structure-beams.md) and the [report](../reports/structure/README.md).*

The roadmap planned the structure work in FreeCAD with CalculiX, and neither is installed here. Installing them is `sudo`, which is mine. So the first pass is the textbook version in Python: each arm a cantilever, each joint its screws.

The catch is that iFlight publishes nothing about the Nazgul's carbon. So I don't pretend to know it: the stiffness runs from 40 to 70 GPa, typical for woven carbon plate, and the arm's free length moves 10% either way, since where the plates really clamp it is a guess too. Every number below is a range for that reason.

## The arms are strong

At the top of the motor's thrust table, 38.6 N, each arm sees about 58 MPa at its root. Carbon plate takes at least 400, so that's almost seven times over, and it's more than my firmware's 90 A current cap would ever let the motors make. The tips sag 3 to 5 mm.

## But they ring near the hover

A spinning prop shakes its arm once a turn (any imbalance) and once a blade. The arm's first bending modes:

| Mode | Frequency |
|---|---|
| Vertical | 37 to 67 Hz |
| In the frame's plane | 80 to 144 Hz |

At a hover the motors turn 88 to 103 times a second, depending on the combination. That's inside the in-plane band. An unbalanced prop in a hover shakes the arm sideways close to where it rings, and the gyro would see it. The vertical mode only gets crossed on the way up and down, which is brief.

![What shakes the arms](../reports/structure/stills/campbell-wide.png)

This doesn't mean the frame is bad. Lots of quads live with it. It means three things for the build: balance every prop before it goes on, take a gyro log in the first tethered hover and look for a peak around 90 to 100 Hz, and if it's there, a notch filter on it. All three are in the test plans now.

## The chute's mount is the weak link

Step 6 worked out a textbook bound on the canopy's opening jolt: up to 254 N. Between the riser and the frame there are three joints:

| Joint | Margin |
|---|---|
| The Harrier's three 4-40 steel screws | 25 to 37 times |
| The cradle's two rail locks, in heat-set inserts | 1.2 to 3.1 times |
| The rail's four nylon screws | 2.4 to 3.2 times |

Those assume only half the fasteners carry the load, since a joint rarely shares it evenly. The screws into the Harrier are fine. The inserts are the weak link, and their pull-out strength in printed PETG is a guess. The nylon screws are thin margin for something that holds a parachute.

So I'd make two changes before P flies. First, steel screws for the rail, about 3 g more; I'm leaving that one for my review, since it's a design change. Second, a hang test that's now in the test plans: 26 kg (the bound) hung from the riser's point on the mounted cradle for a minute, then 39 kg, with nothing cracking, creeping or pulling out.

## What's left for a real model

A drop from 1 m puts 23 J into the legs, and without an FE model their strength is a test, not a number. The cradle, the rail and the legs are the parts that want CalculiX.
