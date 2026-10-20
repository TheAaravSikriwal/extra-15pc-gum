# 2026-10-20: My firmware's first flight

*PC, Windows and WSL2 Ubuntu. Step 5 starts: the spec, the plan, and tasks 1 to 5.*

Up to now the flight sim has flown PX4, which is a few hundred thousand lines of other people's very good code. Step 5 is my own flight code, and the bar is simple to say: it has to pass the same tests PX4 does.

## The shape of it

I wanted the same code to run in the sim, on the ARK FPV's STM32H743 and, for the safety monitor, on a Teensy 4.1, so it's C++17 everywhere. Everything that decides anything (the estimator, the controllers, the mixer, the modes, the failsafes) lives in one core library with no hardware in it. Around it sit thin layers: one that talks to Gazebo, one for the ARK FPV's chips later, one for the safety monitor.

The trick that makes "the same tests as PX4" literal: my firmware speaks PX4's language. It reports itself over MAVLink the way PX4 does and writes its log in PX4's format, ULog, with PX4's topic names. Then the flight sim's scenario scripts fly it without knowing the difference, and the same graders grade it. The [spec](../specs/2026-10-20-firmware.md) has the reasons and the [plan](../plans/2026-10-20-firmware.md) has the 13 tasks.

## Tasks 1 to 3: the pieces

The math is small: vectors and quaternions, in PX4's frames (forward-right-down on the body, north-east-down in the world) so the two logs read the same.

The attitude estimator is Mahony's complementary filter. The gyro carries the attitude from one sample to the next, and two slow corrections keep it honest: gravity, as the accelerometer feels it, pulls the tilt back, and the magnetometer pulls the heading. It only trusts the accelerometer near 1 g, since in a hard pull its direction says little about which way is down. The tests settle it from 20 degrees off, track a steady turn, and learn a made-up gyro bias within a minute.

The rate controller is a PID per axis that asks for an angular acceleration instead of a unitless effort. The mixer multiplies that by the drone's inertia to get a torque, so the gains mean something physical and the same ones suit every module combination. The derivative works on the measured rate, not the error, so a stick step doesn't kick it, and the integrator freezes while the motors are saturated.

The mixer turns the three torques and the total thrust into four motor speeds, with the same geometry PX4 uses. When the motors can't give everything, it gives up yaw first, then climbing, and only then roll and pitch, because a drone that can't hold its attitude can't do anything else.

Two things I got wrong first. My test said "the left rotors are 1 and 3", and they're 1 and 2 in PX4's order. And the rate gains I started with were too soft: a quick Python run of the same loop showed them creeping toward the setpoint for seconds.

## Task 4: flying it in Gazebo

The sim layer is a small Linux program that reads the model's own Gazebo sensors, the same ones PX4 reads, runs the loop once per IMU sample (250 Hz), and sends the four motor speeds back. The generator now writes an airframe file per combination, from the same numbers as the Gazebo model, with the props counted in the inertia. Gazebo carries them as separate parts, and they're about a sixth of the roll inertia.

Before Gazebo, the core flies a little rigid-body model on my PC. That test caught something real: with the weight 1 cm off center, rate mode tipped the drone 27 degrees before the integrator caught up. That's the physics of a PI loop (the tilt it picks up is the off-center pull over the integral gain), so I raised the roll and pitch integral gain from 40 to 100. A 3 mm offset, already more than the CAD's balance check lets through, now costs about 2.5 degrees by that arithmetic, and the test holds it under 5.

The first Gazebo flight went nowhere. My firmware armed and commanded hover speeds, and the model sat on the ground. Gazebo's motor plugins, with no namespace set, listen on `/<model>/command/motor_speed`, and I was publishing under `/model/`. One path segment.

The second one flew: rate mode, 3 s at 15% over the hover throttle, then 10 s at the hover throttle with the sticks centered. It never tilted more than 0.02 degrees. It also climbed to 47 m, which is correct and a little funny: in rate mode nothing holds the height, so it just kept the climb rate it had. Altitude hold is task 7.

## Task 5: the log

The ULog writer lays down PX4's format byte for byte: the header, the formats, the subscriptions, the samples. It writes the eight topics the graders read, including Gazebo's ground truth, under PX4's names. The test writes a sample flight, then pyulog (the library the graders use) reads every value back, and the graders' own reader turns it into the right events. The real Gazebo flight's log goes through the same reader too. One catch on the way: without a status sample from before the arm, the graders saw no arming at all.

## Next

Task 6, MAVLink. I read MAVSDK's source (v3.17.4, the version the flight sim pins) to see exactly what it needs from an autopilot before it calls it healthy: a GPS bit in SYS_STATUS, a HOME_POSITION, HIGHRES_IMU for the clock the runner keeps, and PX4's way of naming modes. It also sets the take-off height as a parameter rather than in the take-off command, so the parameter store has to be real from the start. The notes are in the plan.
