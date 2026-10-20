# The flight sim

*Generated on 2026-10-20 by pcs14 0.1.0, the flight sim in `src/pcs14/flight/`. PX4 v1.17.0 flies a Gazebo Harmonic model of this drone, generated from the build, the sizing model and the CAD, in every module combination.*

## The verdict

**Fail.** 78 of 78 runs flown, and 16 miss: endurance in base; dead motor in base; endurance in V; dead motor in V; endurance in P; endurance in C; dead motor in C; failed sensor in C; endurance in mission; failed sensor in mission; endurance in V+C; dead motor in V+C; failed sensor in V+C; endurance in P+C; failed sensor in P+C; endurance in max.

Built from E3 2814 850KV / 1050 3-blade / 6S2P Molicel INR-21700-P45B.

## Every scenario, every combination

| Scenario | base | V | P | C | mission | V+C | P+C | max |
|---|---|---|---|---|---|---|---|---|
| hover | pass | pass | pass | pass | pass | pass | pass | pass |
| steps | pass | pass | pass | pass | pass | pass | pass | pass |
| top speed |  | pass | pass |  | pass |  |  |  |
| wind |  | pass | pass |  | pass |  |  |  |
| endurance | **fail** | **fail** | **fail** | **fail** | **fail** | **fail** | **fail** | **fail** |
| lost link | pass | pass | pass | pass | pass | pass | pass | pass |
| low battery | pass | pass | pass | pass | pass | pass | pass | pass |
| parachute drop |  |  | pass |  | pass |  | pass | pass |
| dead motor | **fail** | **fail** | pass | **fail** | pass | **fail** | pass | pass |
| failed sensor | pass | pass | pass | **fail** | **fail** | **fail** | **fail** | pass |
| sagging pack | pass | pass | pass | pass | pass | pass | pass | pass |
| payload grab |  |  |  | pass |  | pass | pass | pass |

A blank cell is a scenario that combination doesn't fly: top speed and wind only where the targets set them, the parachute drop with P, the payload grab with C.

<details>
<summary>dead motor, base: fail</summary>

| Check | Found | Verdict |
|---|---|---|
| no fly-away | ended on the ground, 1 m from where it was then | pass |
| touchdown | came down at 24.3 m/s at the end, too fast for a controlled landing | fail |
| safety monitor | its free fall trigger would fire 0.50 s after the failure | pass |

</details>

<details>
<summary>endurance, base: fail</summary>

| Check | Found | Verdict |
|---|---|---|
| hover endurance | 33.7 min in the sim against the sizing model's 33.6, at 283 W | pass |
| cruise endurance | 33.8 min in the sim against the sizing model's 45.4, at 282 W | fail |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>failed sensor, base: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the landing | gps failed then landed | pass |
| no fly-away | ended on the ground, 29 m from where it was then | pass |
| touchdown | came down at 0.7 m/s at the end, a controlled landing | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>hover, base: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| hover drift | drifted 0.07 m sideways over 60.036 s | pass |
| hover height | held its height within 0.07 m | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>lost link, base: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the return | link cut then link lost then return then landed | pass |
| no fly-away | ended on the ground, 0 m from where it started | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>low battery, base: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the return | low battery then return then landed | pass |
| no fly-away | ended on the ground, 0 m from where it started | pass |
| charge at landing | landed with 29% left by my battery model, against the 20% reserve | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>sagging pack, base: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the landing | pack sagged then low battery then landed | pass |
| sagged top speed | the motors topped out at 78% of their usual top speed | pass |
| no fly-away | ended on the ground, 0 m from where it was then | pass |
| touchdown | came down at 0.7 m/s at the end, a controlled landing | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>steps, base: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| roll to 15 degrees: settling | inside 5% of the step after 0.17 s | pass |
| roll to 15 degrees: overshoot | overshot by 3% of the step | pass |
| roll back from 15 degrees: settling | inside 5% of the step after 0.34 s | pass |
| roll back from 15 degrees: overshoot | overshot by 5% of the step | pass |
| pitch to 15 degrees: settling | inside 5% of the step after 0.35 s | pass |
| pitch to 15 degrees: overshoot | overshot by 6% of the step | pass |
| pitch back from 15 degrees: settling | inside 5% of the step after 0.18 s | pass |
| pitch back from 15 degrees: overshoot | overshot by 3% of the step | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>dead motor, C: fail</summary>

| Check | Found | Verdict |
|---|---|---|
| no fly-away | ended on the ground, 1 m from where it was then | pass |
| touchdown | came down at 25.0 m/s at the end, too fast for a controlled landing | fail |
| safety monitor | its free fall trigger would fire 0.51 s after the failure | pass |

</details>

<details>
<summary>endurance, C: fail</summary>

| Check | Found | Verdict |
|---|---|---|
| hover endurance | 29.4 min in the sim against the sizing model's 29.4, at 322 W | pass |
| cruise endurance | 29.6 min in the sim against the sizing model's 38.7, at 321 W | fail |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>failed sensor, C: fail</summary>

| Check | Found | Verdict |
|---|---|---|
| the landing | gps failed then landed | pass |
| no fly-away | ended on the ground, 32 m from where it was then | fail |
| touchdown | came down at 0.7 m/s at the end, a controlled landing | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>hover, C: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| hover drift | drifted 0.10 m sideways over 60.016 s | pass |
| hover height | held its height within 0.06 m | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>lost link, C: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the return | link cut then link lost then return then landed | pass |
| no fly-away | ended on the ground, 0 m from where it started | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>low battery, C: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the return | low battery then return then landed | pass |
| no fly-away | ended on the ground, 0 m from where it started | pass |
| charge at landing | landed with 29% left by my battery model, against the 20% reserve | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>payload grab, C: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| payload drift | stayed within 0.09 m after picking it up | pass |
| payload lifted | the rotors' thrust grew 12%, against 12% for 250 g | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>sagging pack, C: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the landing | pack sagged then low battery then landed | pass |
| sagged top speed | the motors topped out at 78% of their usual top speed | pass |
| no fly-away | ended on the ground, 0 m from where it was then | pass |
| touchdown | came down at 0.7 m/s at the end, a controlled landing | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>steps, C: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| roll to 15 degrees: settling | inside 5% of the step after 0.22 s | pass |
| roll to 15 degrees: overshoot | overshot by 2% of the step | pass |
| roll back from 15 degrees: settling | inside 5% of the step after 0.17 s | pass |
| roll back from 15 degrees: overshoot | overshot by 3% of the step | pass |
| pitch to 15 degrees: settling | inside 5% of the step after 0.22 s | pass |
| pitch to 15 degrees: overshoot | overshot by 3% of the step | pass |
| pitch back from 15 degrees: settling | inside 5% of the step after 0.19 s | pass |
| pitch back from 15 degrees: overshoot | overshot by 3% of the step | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>dead motor, max: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| no fly-away | ended on the ground, 1 m from where it was then | pass |
| chute order | the motors stopped 0.13 s before the canopy left | pass |
| chute height lost | lost 9.3 m before settling at 4.4 m/s | pass |
| safety monitor | its free fall trigger would fire 0.46 s after the failure | pass |

</details>

<details>
<summary>endurance, max: fail</summary>

| Check | Found | Verdict |
|---|---|---|
| hover endurance | 22.7 min in the sim against the sizing model's 22.6, at 414 W | pass |
| cruise endurance | 22.7 min in the sim against the sizing model's 28.5, at 413 W | fail |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>failed sensor, max: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the landing | gps failed then landed | pass |
| no fly-away | ended on the ground, 23 m from where it was then | pass |
| touchdown | came down at 0.7 m/s at the end, a controlled landing | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>hover, max: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| hover drift | drifted 0.06 m sideways over 60.008 s | pass |
| hover height | held its height within 0.12 m | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>lost link, max: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the return | link cut then link lost then return then landed | pass |
| no fly-away | ended on the ground, 0 m from where it started | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>low battery, max: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the return | low battery then return then landed | pass |
| no fly-away | ended on the ground, 0 m from where it started | pass |
| charge at landing | landed with 28% left by my battery model, against the 20% reserve | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>parachute drop, max: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| chute order | the motors stopped 0.12 s before the canopy left | pass |
| chute height lost | lost 4.8 m before settling at 4.4 m/s | pass |
| no fly-away | ended on the ground, 0 m from where it was then | pass |
| safety monitor | its free fall trigger would fire 0.46 s after the failure | pass |

</details>

<details>
<summary>payload grab, max: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| payload drift | stayed within 0.09 m after picking it up | pass |
| payload lifted | the rotors' thrust grew 11%, against 11% for 250 g | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>sagging pack, max: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the landing | pack sagged then low battery then landed | pass |
| sagged top speed | the motors topped out at 78% of their usual top speed | pass |
| no fly-away | ended on the ground, 0 m from where it was then | pass |
| touchdown | came down at 0.7 m/s at the end, a controlled landing | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>steps, max: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| roll to 15 degrees: settling | inside 5% of the step after 0.18 s | pass |
| roll to 15 degrees: overshoot | overshot by 2% of the step | pass |
| roll back from 15 degrees: settling | inside 5% of the step after 0.21 s | pass |
| roll back from 15 degrees: overshoot | overshot by 3% of the step | pass |
| pitch to 15 degrees: settling | inside 5% of the step after 0.31 s | pass |
| pitch to 15 degrees: overshoot | overshot by 6% of the step | pass |
| pitch back from 15 degrees: settling | inside 5% of the step after 0.35 s | pass |
| pitch back from 15 degrees: overshoot | overshot by 6% of the step | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>dead motor, mission: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| no fly-away | ended on the ground, 1 m from where it was then | pass |
| chute order | the motors stopped 0.12 s before the canopy left | pass |
| chute height lost | lost 9.3 m before settling at 4.3 m/s | pass |
| safety monitor | its free fall trigger would fire 0.51 s after the failure | pass |

</details>

<details>
<summary>endurance, mission: fail</summary>

| Check | Found | Verdict |
|---|---|---|
| hover endurance | 25.2 min in the sim against the sizing model's 25.2, at 375 W | pass |
| cruise endurance | 25.3 min in the sim against the sizing model's 32.2, at 374 W | fail |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>failed sensor, mission: fail</summary>

| Check | Found | Verdict |
|---|---|---|
| the landing | gps failed then landed | pass |
| no fly-away | ended on the ground, 36 m from where it was then | fail |
| touchdown | came down at 0.7 m/s at the end, a controlled landing | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>hover, mission: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| hover drift | drifted 0.08 m sideways over 60.008 s | pass |
| hover height | held its height within 0.09 m | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>lost link, mission: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the return | link cut then link lost then return then landed | pass |
| no fly-away | ended on the ground, 0 m from where it started | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>low battery, mission: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the return | low battery then return then landed | pass |
| no fly-away | ended on the ground, 0 m from where it started | pass |
| charge at landing | landed with 28% left by my battery model, against the 20% reserve | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>parachute drop, mission: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| chute order | the motors stopped 0.11 s before the canopy left | pass |
| chute height lost | lost 4.7 m before settling at 4.3 m/s | pass |
| no fly-away | ended on the ground, 0 m from where it was then | pass |
| safety monitor | its free fall trigger would fire 0.44 s after the failure | pass |

</details>

<details>
<summary>sagging pack, mission: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the landing | pack sagged then low battery then landed | pass |
| sagged top speed | the motors topped out at 78% of their usual top speed | pass |
| no fly-away | ended on the ground, 0 m from where it was then | pass |
| touchdown | came down at 0.7 m/s at the end, a controlled landing | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>steps, mission: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| roll to 15 degrees: settling | inside 5% of the step after 0.22 s | pass |
| roll to 15 degrees: overshoot | overshot by 2% of the step | pass |
| roll back from 15 degrees: settling | inside 5% of the step after 0.36 s | pass |
| roll back from 15 degrees: overshoot | overshot by 7% of the step | pass |
| pitch to 15 degrees: settling | inside 5% of the step after 0.37 s | pass |
| pitch to 15 degrees: overshoot | overshot by 8% of the step | pass |
| pitch back from 15 degrees: settling | inside 5% of the step after 0.34 s | pass |
| pitch back from 15 degrees: overshoot | overshot by 9% of the step | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>top speed, mission: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| top speed | held 88 km/h for 1 s, against 80 | pass |
| top speed, flat out | the busiest motor at 100% of its top speed, leaning up to 47 degrees | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>wind, mission: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| wind drift | drifted 0.14 m in the wind | pass |
| motor headroom | the busiest motor reached 62% of its top speed | pass |
| leaning into the wind | leaned 3.3 degrees into a 10 m/s wind | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>dead motor, P: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| no fly-away | ended on the ground, 1 m from where it was then | pass |
| chute order | the motors stopped 0.14 s before the canopy left | pass |
| chute height lost | lost 8.9 m before settling at 4.1 m/s | pass |
| safety monitor | its free fall trigger would fire 0.50 s after the failure | pass |

</details>

<details>
<summary>endurance, P: fail</summary>

| Check | Found | Verdict |
|---|---|---|
| hover endurance | 29.3 min in the sim against the sizing model's 29.2, at 324 W | pass |
| cruise endurance | 29.4 min in the sim against the sizing model's 38.8, at 322 W | fail |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>failed sensor, P: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the landing | gps failed then landed | pass |
| no fly-away | ended on the ground, 30 m from where it was then | pass |
| touchdown | came down at 0.7 m/s at the end, a controlled landing | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>hover, P: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| hover drift | drifted 0.06 m sideways over 60.004 s | pass |
| hover height | held its height within 0.11 m | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>lost link, P: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the return | link cut then link lost then return then landed | pass |
| no fly-away | ended on the ground, 0 m from where it started | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>low battery, P: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the return | low battery then return then landed | pass |
| no fly-away | ended on the ground, 0 m from where it started | pass |
| charge at landing | landed with 29% left by my battery model, against the 20% reserve | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>parachute drop, P: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| chute order | the motors stopped 0.14 s before the canopy left | pass |
| chute height lost | lost 4.7 m before settling at 4.1 m/s | pass |
| no fly-away | ended on the ground, 0 m from where it was then | pass |
| safety monitor | its free fall trigger would fire 0.42 s after the failure | pass |

</details>

<details>
<summary>sagging pack, P: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the landing | pack sagged then low battery then landed | pass |
| sagged top speed | the motors topped out at 78% of their usual top speed | pass |
| no fly-away | ended on the ground, 0 m from where it was then | pass |
| touchdown | came down at 0.7 m/s at the end, a controlled landing | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>steps, P: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| roll to 15 degrees: settling | inside 5% of the step after 0.20 s | pass |
| roll to 15 degrees: overshoot | overshot by 2% of the step | pass |
| roll back from 15 degrees: settling | inside 5% of the step after 0.17 s | pass |
| roll back from 15 degrees: overshoot | overshot by 3% of the step | pass |
| pitch to 15 degrees: settling | inside 5% of the step after 0.15 s | pass |
| pitch to 15 degrees: overshoot | overshot by 4% of the step | pass |
| pitch back from 15 degrees: settling | inside 5% of the step after 0.20 s | pass |
| pitch back from 15 degrees: overshoot | overshot by 4% of the step | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>top speed, P: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| top speed | held 88 km/h for 1 s, against 80 | pass |
| top speed, flat out | the busiest motor at 100% of its top speed, leaning up to 47 degrees | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>wind, P: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| wind drift | drifted 0.13 m in the wind | pass |
| motor headroom | the busiest motor reached 60% of its top speed | pass |
| leaning into the wind | leaned 2.6 degrees into a 10 m/s wind | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>dead motor, P+C: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| no fly-away | ended on the ground, 0 m from where it was then | pass |
| chute order | the motors stopped 0.14 s before the canopy left | pass |
| chute height lost | lost 9.1 m before settling at 4.3 m/s | pass |
| safety monitor | its free fall trigger would fire 0.48 s after the failure | pass |

</details>

<details>
<summary>endurance, P+C: fail</summary>

| Check | Found | Verdict |
|---|---|---|
| hover endurance | 26.0 min in the sim against the sizing model's 25.9, at 364 W | pass |
| cruise endurance | 26.1 min in the sim against the sizing model's 33.6, at 362 W | fail |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>failed sensor, P+C: fail</summary>

| Check | Found | Verdict |
|---|---|---|
| the landing | gps failed then landed | pass |
| no fly-away | ended on the ground, 31 m from where it was then | fail |
| touchdown | came down at 0.7 m/s at the end, a controlled landing | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>hover, P+C: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| hover drift | drifted 0.09 m sideways over 60 s | pass |
| hover height | held its height within 0.06 m | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>lost link, P+C: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the return | link cut then link lost then return then landed | pass |
| no fly-away | ended on the ground, 0 m from where it started | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>low battery, P+C: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the return | low battery then return then landed | pass |
| no fly-away | ended on the ground, 0 m from where it started | pass |
| charge at landing | landed with 28% left by my battery model, against the 20% reserve | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>parachute drop, P+C: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| chute order | the motors stopped 0.16 s before the canopy left | pass |
| chute height lost | lost 4.8 m before settling at 4.3 m/s | pass |
| no fly-away | ended on the ground, 0 m from where it was then | pass |
| safety monitor | its free fall trigger would fire 0.42 s after the failure | pass |

</details>

<details>
<summary>payload grab, P+C: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| payload drift | stayed within 0.10 m after picking it up | pass |
| payload lifted | the rotors' thrust grew 11%, against 11% for 250 g | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>sagging pack, P+C: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the landing | pack sagged then low battery then landed | pass |
| sagged top speed | the motors topped out at 78% of their usual top speed | pass |
| no fly-away | ended on the ground, 0 m from where it was then | pass |
| touchdown | came down at 0.7 m/s at the end, a controlled landing | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>steps, P+C: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| roll to 15 degrees: settling | inside 5% of the step after 0.17 s | pass |
| roll to 15 degrees: overshoot | overshot by 4% of the step | pass |
| roll back from 15 degrees: settling | inside 5% of the step after 0.15 s | pass |
| roll back from 15 degrees: overshoot | overshot by 5% of the step | pass |
| pitch to 15 degrees: settling | inside 5% of the step after 0.20 s | pass |
| pitch to 15 degrees: overshoot | overshot by 4% of the step | pass |
| pitch back from 15 degrees: settling | inside 5% of the step after 0.16 s | pass |
| pitch back from 15 degrees: overshoot | overshot by 4% of the step | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>dead motor, V: fail</summary>

| Check | Found | Verdict |
|---|---|---|
| no fly-away | ended on the ground, 2 m from where it was then | pass |
| touchdown | came down at 24.6 m/s at the end, too fast for a controlled landing | fail |
| safety monitor | its free fall trigger would fire 0.51 s after the failure | pass |

</details>

<details>
<summary>endurance, V: fail</summary>

| Check | Found | Verdict |
|---|---|---|
| hover endurance | 28.4 min in the sim against the sizing model's 28.4, at 333 W | pass |
| cruise endurance | 28.5 min in the sim against the sizing model's 36.8, at 332 W | fail |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>failed sensor, V: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the landing | gps failed then landed | pass |
| no fly-away | ended on the ground, 22 m from where it was then | pass |
| touchdown | came down at 0.7 m/s at the end, a controlled landing | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>hover, V: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| hover drift | drifted 0.09 m sideways over 60 s | pass |
| hover height | held its height within 0.07 m | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>lost link, V: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the return | link cut then link lost then return then landed | pass |
| no fly-away | ended on the ground, 0 m from where it started | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>low battery, V: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the return | low battery then return then landed | pass |
| no fly-away | ended on the ground, 0 m from where it started | pass |
| charge at landing | landed with 29% left by my battery model, against the 20% reserve | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>sagging pack, V: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the landing | pack sagged then low battery then landed | pass |
| sagged top speed | the motors topped out at 78% of their usual top speed | pass |
| no fly-away | ended on the ground, 0 m from where it was then | pass |
| touchdown | came down at 0.7 m/s at the end, a controlled landing | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>steps, V: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| roll to 15 degrees: settling | inside 5% of the step after 0.14 s | pass |
| roll to 15 degrees: overshoot | overshot by 4% of the step | pass |
| roll back from 15 degrees: settling | inside 5% of the step after 0.18 s | pass |
| roll back from 15 degrees: overshoot | overshot by 4% of the step | pass |
| pitch to 15 degrees: settling | inside 5% of the step after 0.36 s | pass |
| pitch to 15 degrees: overshoot | overshot by 5% of the step | pass |
| pitch back from 15 degrees: settling | inside 5% of the step after 0.16 s | pass |
| pitch back from 15 degrees: overshoot | overshot by 3% of the step | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>top speed, V: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| top speed | held 88 km/h for 1 s, against 80 | pass |
| top speed, flat out | the busiest motor at 100% of its top speed, leaning up to 47 degrees | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>wind, V: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| wind drift | drifted 0.15 m in the wind | pass |
| motor headroom | the busiest motor reached 60% of its top speed | pass |
| leaning into the wind | leaned 2.3 degrees into a 10 m/s wind | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>dead motor, V+C: fail</summary>

| Check | Found | Verdict |
|---|---|---|
| no fly-away | ended on the ground, 6 m from where it was then | pass |
| touchdown | came down at 24.1 m/s at the end, too fast for a controlled landing | fail |
| safety monitor | its free fall trigger would fire 0.50 s after the failure | pass |

</details>

<details>
<summary>endurance, V+C: fail</summary>

| Check | Found | Verdict |
|---|---|---|
| hover endurance | 25.3 min in the sim against the sizing model's 25.3, at 373 W | pass |
| cruise endurance | 25.4 min in the sim against the sizing model's 32.1, at 372 W | fail |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>failed sensor, V+C: fail</summary>

| Check | Found | Verdict |
|---|---|---|
| the landing | gps failed then landed | pass |
| no fly-away | ended on the ground, 32 m from where it was then | fail |
| touchdown | came down at 0.7 m/s at the end, a controlled landing | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>hover, V+C: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| hover drift | drifted 0.06 m sideways over 60.012 s | pass |
| hover height | held its height within 0.20 m | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>lost link, V+C: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the return | link cut then link lost then return then landed | pass |
| no fly-away | ended on the ground, 0 m from where it started | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>low battery, V+C: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the return | low battery then return then landed | pass |
| no fly-away | ended on the ground, 0 m from where it started | pass |
| charge at landing | landed with 28% left by my battery model, against the 20% reserve | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>payload grab, V+C: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| payload drift | stayed within 0.05 m after picking it up | pass |
| payload lifted | the rotors' thrust grew 11%, against 11% for 250 g | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>sagging pack, V+C: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| the landing | pack sagged then low battery then landed | pass |
| sagged top speed | the motors topped out at 78% of their usual top speed | pass |
| no fly-away | ended on the ground, 0 m from where it was then | pass |
| touchdown | came down at 0.7 m/s at the end, a controlled landing | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

<details>
<summary>steps, V+C: pass</summary>

| Check | Found | Verdict |
|---|---|---|
| roll to 16 degrees: settling | inside 5% of the step after 0.19 s | pass |
| roll to 16 degrees: overshoot | overshot by 4% of the step | pass |
| roll back from 16 degrees: settling | inside 5% of the step after 0.22 s | pass |
| roll back from 16 degrees: overshoot | overshot by 0% of the step | pass |
| pitch to 15 degrees: settling | inside 5% of the step after 0.40 s | pass |
| pitch to 15 degrees: overshoot | overshot by 9% of the step | pass |
| pitch back from 15 degrees: settling | inside 5% of the step after 0.18 s | pass |
| pitch back from 15 degrees: overshoot | overshot by 4% of the step | pass |
| false triggers | the safety monitor's triggers fired: none | pass |

</details>

## Why the misses miss

**dead motor, touchdown** (base, C, V, V+C). There's no chute without P, and a quad can't fly on three motors: PX4 drops the dead one from the mix and tries, but it tumbles and falls. Every combination without P loses the drone to a dead motor.

**endurance, cruise endurance** (base, C, max, mission, P, P+C, V, V+C). The sizing model says forward flight is cheaper than a hover, the way it is for a real prop moving through fresh air. Gazebo's rotors make the same thrust at any airspeed, so in the sim a cruise costs about what a hover does. The truth is somewhere between, and pinning it down takes the rotor's forward-flight data the aero side track will measure.

**failed sensor, no fly-away** (C, mission, P+C, V+C). Without GPS this drone has nothing to hold its position with: the TF-Luna only measures height, and there's no optical flow sensor. PX4 comes down blind, level by its own attitude estimate, and that estimate's small tilt error carries it off at up to a few m/s. In wind it would drift farther.

## Closing the loop

Flight times from the sim's logged rotors, through my battery model, against the sizing model's at the same weight (no growth margin, no payload).

| Setup | Hover, sim | Hover, sizing model | Cruise, sim | Cruise, sizing model |
|---|---|---|---|---|
| base | 33.7 min | 33.6 min | 33.8 min | 45.4 min |
| V | 28.4 min | 28.4 min | 28.5 min | 36.8 min |
| P | 29.3 min | 29.2 min | 29.4 min | 38.8 min |
| C | 29.4 min | 29.4 min | 29.6 min | 38.7 min |
| mission | 25.2 min | 25.2 min | 25.3 min | 32.2 min |
| V+C | 25.3 min | 25.3 min | 25.4 min | 32.1 min |
| P+C | 26.0 min | 25.9 min | 26.1 min | 33.6 min |
| max | 22.7 min | 22.6 min | 22.7 min | 28.5 min |

The safety monitor's triggers, replayed over the 66 runs where nothing fails on purpose: no false triggers.

And where something really fails:

- dead motor in base: its free fall trigger would fire 0.50 s after the failure
- dead motor in C: its free fall trigger would fire 0.51 s after the failure
- dead motor in max: its free fall trigger would fire 0.46 s after the failure
- parachute drop in max: its free fall trigger would fire 0.46 s after the failure
- dead motor in mission: its free fall trigger would fire 0.51 s after the failure
- parachute drop in mission: its free fall trigger would fire 0.44 s after the failure
- dead motor in P: its free fall trigger would fire 0.50 s after the failure
- parachute drop in P: its free fall trigger would fire 0.42 s after the failure
- dead motor in P+C: its free fall trigger would fire 0.48 s after the failure
- parachute drop in P+C: its free fall trigger would fire 0.42 s after the failure
- dead motor in V: its free fall trigger would fire 0.51 s after the failure
- dead motor in V+C: its free fall trigger would fire 0.50 s after the failure

## The models

Each combination's model, as generated. The weight is the CAD's, without the sizing model's growth margin; the top speed is where each motor makes the sizing model's full-throttle thrust, at the 20% reserve and the 90 A cap.

| Setup | Weight | Hover throttle | Top speed | Thrust constant | Torque per thrust | Drag area | Chute | Payload |
|---|---|---|---|---|---|---|---|---|
| base | 1860 g | 51% | 9046 rpm | 1.58e-05 N/(rad/s)² | 16.0 mm | 120 cm² |  |  |
| V | 2032 g | 54% | 9046 rpm | 1.58e-05 N/(rad/s)² | 16.0 mm | 177 cm² |  |  |
| P | 2036 g | 54% | 9046 rpm | 1.58e-05 N/(rad/s)² | 16.0 mm | 145 cm² | yes |  |
| C | 2022 g | 57% | 9046 rpm | 1.58e-05 N/(rad/s)² | 16.1 mm | 160 cm² |  | 250 g |
| mission | 2208 g | 57% | 9046 rpm | 1.58e-05 N/(rad/s)² | 16.0 mm | 202 cm² | yes |  |
| V+C | 2194 g | 60% | 9046 rpm | 1.58e-05 N/(rad/s)² | 16.2 mm | 217 cm² |  | 250 g |
| P+C | 2198 g | 60% | 9046 rpm | 1.58e-05 N/(rad/s)² | 16.2 mm | 185 cm² | yes | 250 g |
| max | 2370 g | 62% | 9046 rpm | 1.58e-05 N/(rad/s)² | 16.4 mm | 242 cm² | yes | 250 g |

## What it rests on

- The props' in-plane drag, their rolling moment and the motors' spin-up and spin-down times: PX4's x500 model (PX4-gazebo-models b6127f4, pinned by PX4 v1.17.0)
- fruity-chutes-harrier-40-42: ejection_s, opening_s. Fruity Chutes doesn't publish its timing. A spring launcher clears the tube in a fraction of a second, and a canopy this size takes about a second to fill at low speed; both are guesses for the flight sim, which reports the height lost while it opens
- The frame's drag area: Frontal area from the published size, times a drag coefficient of 1.0 for a blunt body: body 35 x 100 mm, arms 7 x 297 mm, four motors about 35 x 25 mm, and a 6S2P 21700 pack end-on about 42 x 70 mm, about 0.012 m2 in all. The battery is counted here. Replaced when the wind tunnel side track has real numbers
- The safety monitor's trigger thresholds are starting numbers, to be tuned against the false-trigger replays

## What it can't prove

- The parachute's descent rate. Its drag comes from Fruity Chutes' own rating, so the sim only repeats it; the drop checks the order of events and the height lost.
- The payload grab. Gazebo's attach joint stands in for the claws, which are a placeholder anyway.
- My firmware's current cap and the XT60's heat limit. This is PX4, which has neither, so the motors are held at their worst-case top speed instead.
- The props' in-plane drag, their rolling moment and the motors' spin-up times, which are PX4's x500 values.
- Body drag beyond a frontal-area estimate, until the wind tunnel side track has real tables.
- Vibration, and anything else a real IMU sees that clean Gaussian noise doesn't.

## Files

Generated on every run, not committed (they're build outputs):

- `stills/matrix.png`
- `stills/drop-portrait.png`
- `stills/drop-square.png`
- `stills/drop-vertical.png`
- `stills/drop-wide.png`
- `stills/steps.png`
- `flight-sim/models/pcs14_base/model.sdf`
- `flight-sim/models/pcs14_c/model.sdf`
- `flight-sim/models/pcs14_max/model.sdf`
- `flight-sim/models/pcs14_mission/model.sdf`
- `flight-sim/models/pcs14_p/model.sdf`
- `flight-sim/models/pcs14_p_c/model.sdf`
- `flight-sim/models/pcs14_payload/model.sdf`
- `flight-sim/models/pcs14_v/model.sdf`
- `flight-sim/models/pcs14_v_c/model.sdf`
- `flight-sim/worlds/pcs14-fine.sdf`
- `flight-sim/worlds/pcs14.sdf`
