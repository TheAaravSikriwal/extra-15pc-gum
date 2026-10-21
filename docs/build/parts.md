# The parts list

*Generated 2026-10-21 by `pcs14 package`, from the catalog, the build, the connection list and the CAD report. The same list is in [parts.csv](parts.csv). Prices are what the shop showed on the day each part was checked, in US dollars, and they drift. A ? is a price nobody's checked yet; it isn't counted as free.*

## What each combination costs

| Combination | Bought parts, wire and plugs | Not priced yet | Printed |
|---|---|---|---|
| base | $876.78 | 0 | 9 parts, 74 g |
| V | $1,321.67 | 1 | 13 parts, 128 g |
| P | $1,569.26 | 0 | 10 parts, 82 g |
| C | $1,034.93 | 1 | 9 parts, 74 g |
| mission | $2,014.15 | 1 | 14 parts, 136 g |
| V+C | $1,479.81 | 2 | 13 parts, 128 g |
| P+C | $1,727.40 | 1 | 10 parts, 82 g |
| max | $2,172.29 | 2 | 14 parts, 136 g |

Bought once, whatever's fitted (the transmitter, a charger, supplies, tools): $361.99, with 5 not priced yet.
Screws, nuts and spacers aren't priced: they're a few dollars from any hardware supplier.

## Base

### Parts

| Part | How many | Each | Total | Checked | If it's gone | Note |
|---|---|---|---|---|---|---|
| [Motor](https://shop.emax-usa.com/products/emax-e3-2814-brushless-motor)<br>Emax E3 2814 850KV | 4 | $37.99 | $151.96 | 2026-10-21 | [iFlight XING 2814 880KV](https://shop.iflight.com/xing-x2814-fpv-nextgen-motor-pro838): the same 19 x 19 mm mount and 5 mm shaft, 6 g heavier, and a lower peak; its thrust table is only an image, so the sizing model would need it read first | out of stock at EMAX USA on the day; EMAX's global shop had it at $58.50 |
| [Prop](https://www.getfpv.com/gemfan-1050-cl-cinelifter-3-blade-propeller-set-of-2-glass-fiber-nylon.html)<br>Gemfan 1050 3-blade | 4 | $6.00 | $24.00 | 2026-10-21 | [HQProp MacroQuad 10x5x3, 2 CW + 2 CCW](https://www.readymaderc.com/products/details/86878-hq-macroquad-prop-10x5x3-2ccw-2cw-black-glass-fiber-reinforced-nylon): the same size and hub, 6 g a prop heavier, and the motor's thrust table was measured on Gemfan, so recheck | two turn each way; sold in pairs at $11.99; back ordered at GetFPV on the day |
| [4-in-1 ESC](https://holybro.com/collections/fpv-esc/products/tekko32-f4-4in1-50a-esc)<br>Holybro Tekko32 F4 4in1 50A (AM32) | 1 | $62.99 | $62.99 | 2026-10-21 | [Lumenier ELITE PRO 60A 2-6S AM32 4-in-1, 30x30](https://www.getfpv.com/electronics/electronic-speed-controllers-esc/4-in-1-esc-s/lumenier-elite-pro-60a-2-6s-am32-4-in-1-esc-30x30.html): the same AM32 firmware and mount with more headroom, but 13 g heavier and 3 mm taller, against the frame's 19 mm stack height |  |
| [Frame](https://www.getfpv.com/iflight-nazgul-xl10-v6-10-frame-kit.html)<br>iFlight Nazgul XL10 V6 10-inch frame | 1 | $142.99 | $142.99 | 2026-10-21 | [GEPRC GEP-Mark4-10 frame kit](https://www.readymaderc.com/products/details/86588-geprc-mark4-10-multirotor-frame): the same stack and motor mounts and 75 g lighter, but a different plate layout, so the CAD needs a new frame | the catalog's $115.99 couldn't be found anywhere; iFlight's own shop doesn't list it |
| [Cell](https://liionwholesale.com/products/molicel-npe-inr-21700-p45b-50a-4500mah-flat-top-21700-battery-authorized-distributor)<br>Molicel INR-21700-P45B | 12 | $7.49 | $89.88 | 2026-10-21 | [Molicel INR-21700-P42A](https://imrbatteries.com/products/molicel-p42a-21700-4200mah-45a-battery): the same size and 45 A rating; the pack drops from 9.0 to 8.4 Ah, about 7% less flight time | for the 6S2P pack; out of stock at Liion Wholesale on the day; GetFPV had it at about $13 a cell, in stock |
| [ARK FPV flight controller](https://arkelectron.com/product/ark-fpv-flight-controller/)<br>ARK Electronics | 1 | $194.99 | $194.99 | 2026-10-21 | [Holybro Kakute H7 V1.5 (SKU 11091)](https://holybro.com/products/kakute-h7): the same STM32H743 and mount and runs PX4, but different sensors (my firmware's drivers are written for the ARK's), no compass and solder pads instead of JST-GH | in stock on the day; ARK lists its barometer as a BMP390, which my firmware's driver also accepts |
| [RP2 V2 ExpressLRS 2.4 GHz receiver](https://www.radiomasterrc.com/products/rp2-expresslrs-2-4ghz-nano-receiver)<br>RadioMaster | 1 | $18.99 | $18.99 | 2026-10-21 | [BETAFPV ELRS Nano Receiver 2.4GHz](https://racedayquads.com/products/betafpv-elrs-nano-2-4ghz-receiver): the same CRSF wiring, but a T antenna on U.FL to mount | order the FCC version |
| [TF-Luna lidar](https://www.robotshop.com/products/benewake-tf-luna-8m-lidar-distance-sensor)<br>Benewake | 1 | $20.96 | $20.96 | 2026-10-21 | [Benewake TFmini-S (SparkFun SEN-16977)](https://www.sparkfun.com/tfmini-s-micro-lidar-module.html): longer range (12 m) at the same weight, but a different body for the bracket and a tighter 5 V supply |  |
| [Teensy 4.1 (safety monitor)](https://www.sparkfun.com/teensy-4-1.html)<br>PJRC | 1 | $31.50 | $31.50 | 2026-10-21 | [PJRC (made by SparkFun) Teensy 4.0 (DEV-15583)](https://www.sparkfun.com/teensy-4-0.html): the same chip, but fewer pins, no microSD and a different size: the monitor's pin map and mount change | PJRC sends buyers to SparkFun, which makes Teensy now |
| [LSM6DSOX 6-DoF accelerometer and gyroscope breakout (product 4438)](https://www.adafruit.com/product/4438)<br>Adafruit (board), STMicroelectronics (chip) | 1 | $11.95 | $11.95 | 2026-10-21 | [Adafruit LSM6DSO32 breakout (4692)](https://www.adafruit.com/product/4692): the same family; its accelerometer has no +-2 g range, so the monitor's range setting changes |  |
| [TS3A5018 quad two-way analog switch on a CJMCU-5018 breakout](https://www.amazon.com/dp/B07PS18HST)<br>Texas Instruments (chip), various (board) | 1 | $6.99 | $6.99 | 2026-10-21 | [Texas Instruments and Adafruit TS3A5018DR on an Adafruit SOIC-16 breakout (1207)](https://www.mouser.com/en/ProductDetail/Texas-Instruments/TS3A5018DR?qs=0O%2FZFlpUpJXorOS44CKPgg%3D%3D): the same chip on a different board: the pin order and mount change, and its decoupling capacitor is mine to add | NOYITO on Amazon; Siqma sells it at $1.20 with a minimum of eight |
| [Six SN74LVC1G125 buffers on SparkFun SOT-23 adapters (BOB-00717)](https://www.mouser.com/ProductDetail/Texas-Instruments/74LVC1G125DBVRG4?qs=pajgIaoyDUi0MXq%2Fp1CdDQ%3D%3D)<br>Texas Instruments (chips), SparkFun (adapters) | 1 | $12.12 | $12.12 | 2026-10-21 | [Nexperia 74LVC1G125GV-Q100](https://www.mouser.com/en/ProductDetail/Nexperia/74LVC1G125GV-Q100?qs=vnbNJPHmPnMppZZ6gawcFw%3D%3D): the same buffer in the same size of package; check its pinout against TI's before wiring | six TI 74LVC1G125DBVRG4 at $0.77 and six SparkFun BOB-00717 adapters at $1.25 (https://www.sparkfun.com/sparkfun-sot23-to-dip-adapter.html); the plain SN74LVC1G125DBVR was out of stock until February 2027 |
| [BAT54C dual Schottky diode (common cathode) on a SOT-23 adapter](https://www.mouser.com/ProductDetail/onsemi/BAT54CLT3G?qs=CBDP9nzV7kkNgCKU97dzRw%3D%3D)<br>Diodes Incorporated (diode) | 1 | $1.38 | $1.38 | 2026-10-21 | [Diodes Incorporated BAT54C-7-F](https://www.mouser.com/ProductDetail/Diodes-Incorporated/BAT54C-7-F?qs=A%2FGeX6qn32NJhN9M%2F3GNcA%3D%3D): the catalog's own part, back ordered until April 2027 | onsemi's BAT54CLT3G ($0.13), the same dual Schottky, on a SparkFun BOB-00717 adapter ($1.25); check its pinout |
| [D36V6F3 3.3 V 600 mA step-down regulator (item 3791)](https://www.pololu.com/product/3791)<br>Pololu | 1 | $5.95 | $5.95 | 2026-10-21 | [Pololu D24V5F3 (item 2842)](https://www.pololu.com/product/2842): the same size and pins; 36 V in at most (fine on 6S) and 500 mA out |  |
| [R111 Remote ID broadcast module](https://www.amazon.com/Ruko-Aircraft-Tracker-Regulation-Compliant/dp/B0DG53V8JG)<br>Ruko | 1 | $39.99 | $39.99 | 2026-10-21 | [Holy Stone HSRID03](https://store.holystone.com/products/hsrid03): FAA-accepted with its own battery; its size and weight aren't published, so the mount and weight need checking | the R111S seems to have replaced the R111 (both FAA-accepted; the R111S is RID000001939); Ruko lists 13.5 g, so check it against the mount |
| [BEC12S-PRO 5 V 5 A supply for the Pi](https://www.racedayquads.com/products/matek-bec12s-pro-9-55v-to-5-8-12v-5a)<br>Matek | 1 | $22.99 | $22.99 | 2026-10-21 | [Pololu D36V50F5 (item 4091)](https://www.pololu.com/product/4091): 5.0 V at 5.5 A from up to 50 V; 2 g heavier and a different shape for its mount | its default output is 5.2 V, which the electrical report uses |
| Module sockets, three slots (an XT30U and an 8-pin JST-GH each)<br>Amass and JST | 1 | $9.85 | $9.85 | 2026-10-21 | Amass and JST the same halves from the XT30 and JST-GH fallbacks: see those two | an estimate from its pieces: three XT30U halves ($0.32), three 8-pin JST-GH plugs with leads (about $2.48), a 4-pin plug ($1.26) and two resistors |
| [Two MINI blade fuses, soldered inline under heat shrink](https://www.mouser.com/en/ProductDetail/Littelfuse/0297003.WXNV?qs=WtG364jHAdxHR7%2F%2F%252BiOsmQ%3D%3D)<br>Littelfuse (fuses) | 1 | $0.78 | $0.78 | 2026-10-21 | Eaton Bussmann BK/ATM-3 and ATM-2: the same size, five times the price | one 3 A (0297003) and one 2 A (0297002), $0.39 each at Mouser |

### Wire

| Part | How many | Each | Total | Checked | If it's gone | Note |
|---|---|---|---|---|---|---|
| [Thin PVC hookup lead for JST plugs, 26 AWG](https://www.adafruit.com/product/2517)<br>Various | 3.4 m | $0.65 | $2.21 | 2026-10-21 | [BNTECHGO 28 AWG silicone wire, red and black, 10 ft](https://www.amazon.com/dp/B01F8PO7UK): silicone in place of PVC, the same gauges | 2.56 m in the connection list, plus 30% |
| [Thin PVC hookup lead for JST plugs, 28 AWG](https://www.racedayquads.com/products/rdq-silicone-wire-6-roll-build-kit-28awg)<br>Various | 2.3 m | $0.30 | $0.69 | 2026-10-21 | [BNTECHGO 28 AWG silicone wire, red and black, 10 ft](https://www.amazon.com/dp/B01F8PO7UK): silicone in place of PVC, the same gauges | 1.75 m in the connection list, plus 30% |
| [Silicone hookup wire, UL style 3135, 12 AWG](https://www.racedayquads.com/products/silicone-wire-2-ft-red-and-black-pair)<br>Various (UL 3135) | 0.5 m | $4.08 | $2.04 | 2026-10-21 | [BNTECHGO silicone wire, red and black, 10 ft a color](https://www.amazon.com/dp/B01ABOPMEI): the same gauges, 200 C and 600 V, sold by the 10 ft | 0.34 m in the connection list, plus 30% |
| [Silicone hookup wire, UL style 3135, 18 AWG](https://www.racedayquads.com/products/silicone-wire-2-ft-red-and-black-pair)<br>Various (UL 3135) | 0.5 m | $4.08 | $2.04 | 2026-10-21 | [BNTECHGO silicone wire, red and black, 10 ft a color](https://www.amazon.com/dp/B01ABOPMEI): the same gauges, 200 C and 600 V, sold by the 10 ft | 0.31 m in the connection list, plus 30% |
| [Silicone hookup wire, UL style 3135, 20 AWG](https://www.racedayquads.com/products/silicone-wire-2-ft-red-and-black-pair)<br>Various (UL 3135) | 0.2 m | $4.08 | $0.82 | 2026-10-21 | [BNTECHGO silicone wire, red and black, 10 ft a color](https://www.amazon.com/dp/B01ABOPMEI): the same gauges, 200 C and 600 V, sold by the 10 ft | 0.11 m in the connection list, plus 30% |
| [Silicone hookup wire, UL style 3135, 22 AWG](https://www.racedayquads.com/products/silicone-wire-2-ft-red-and-black-pair)<br>Various (UL 3135) | 0.1 m | $4.08 | $0.41 | 2026-10-21 | [BNTECHGO silicone wire, red and black, 10 ft a color](https://www.amazon.com/dp/B01ABOPMEI): the same gauges, 200 C and 600 V, sold by the 10 ft | 0.06 m in the connection list, plus 30% |

### Plugs

| Part | How many | Each | Total | Checked | If it's gone | Note |
|---|---|---|---|---|---|---|
| [XT60 battery connector](https://www.getfpv.com/amass-xt60h-power-connectors-male-female-5-sets-10-pcs.html)<br>Amass | 1 | $0.90 | $0.90 | 2026-10-21 | [Amass XT60H, single halves](https://www.racedayquads.com/products/amass-xt60h-connector-1pc-choose-your-version): the same connector from another shop | the wire's half; sold as five pairs for $8.99 |
| [GH series wire-to-board connector, 1.25 mm pitch, 3-pin](https://www.mouser.com/en/ProductDetail/JST-Commercial/AGHGH28K305?qs=QpmGXVUTftHuHDeXhn0HhA%3D%3D)<br>JST | 1 | $1.90 | $1.90 | 2026-10-21 | [elechawk GH1.25 pre-crimped cable kit, 15 cm](https://www.amazon.com/dp/B07PBHN7TM): pre-crimped and cheaper per plug, but a clone, not genuine JST | the wire's half; genuine JST from Mouser: housings $0.10 (4-pin) to $0.16 (8-pin) and pre-crimped leads at $0.58, cut in half for two ends; $1.90 is a typical 6-pin plug with its leads |
| [GH series wire-to-board connector, 1.25 mm pitch, 4-pin](https://www.mouser.com/en/ProductDetail/JST-Commercial/AGHGH28K305?qs=QpmGXVUTftHuHDeXhn0HhA%3D%3D)<br>JST | 1 | $1.90 | $1.90 | 2026-10-21 | [elechawk GH1.25 pre-crimped cable kit, 15 cm](https://www.amazon.com/dp/B07PBHN7TM): pre-crimped and cheaper per plug, but a clone, not genuine JST | the wire's half; genuine JST from Mouser: housings $0.10 (4-pin) to $0.16 (8-pin) and pre-crimped leads at $0.58, cut in half for two ends; $1.90 is a typical 6-pin plug with its leads |
| [GH series wire-to-board connector, 1.25 mm pitch, 6-pin](https://www.mouser.com/en/ProductDetail/JST-Commercial/AGHGH28K305?qs=QpmGXVUTftHuHDeXhn0HhA%3D%3D)<br>JST | 4 | $1.90 | $7.60 | 2026-10-21 | [elechawk GH1.25 pre-crimped cable kit, 15 cm](https://www.amazon.com/dp/B07PBHN7TM): pre-crimped and cheaper per plug, but a clone, not genuine JST | the wire's half; genuine JST from Mouser: housings $0.10 (4-pin) to $0.16 (8-pin) and pre-crimped leads at $0.58, cut in half for two ends; $1.90 is a typical 6-pin plug with its leads |
| [GH series wire-to-board connector, 1.25 mm pitch, 8-pin](https://www.mouser.com/en/ProductDetail/JST-Commercial/AGHGH28K305?qs=QpmGXVUTftHuHDeXhn0HhA%3D%3D)<br>JST | 1 | $1.90 | $1.90 | 2026-10-21 | [elechawk GH1.25 pre-crimped cable kit, 15 cm](https://www.amazon.com/dp/B07PBHN7TM): pre-crimped and cheaper per plug, but a clone, not genuine JST | the wire's half; genuine JST from Mouser: housings $0.10 (4-pin) to $0.16 (8-pin) and pre-crimped leads at $0.58, cut in half for two ends; $1.90 is a typical 6-pin plug with its leads |
| [SH series wire-to-board connector, 1.0 mm pitch, 8-pin](https://www.mouser.com/en/ProductDetail/JST-Commercial/ASSHSSH28K152?qs=QpmGXVUTftEMSPTtBZfang%3D%3D)<br>JST | 2 | $2.06 | $4.12 | 2026-10-21 | [AIRBOT SH 1.0 silicone cable set](https://www.racedayquads.com/products/sh-1-0-silicone-cable-set): a clone kit with fixed lead lengths | the wire's half; genuine JST from Mouser: SHR housings $0.10 and pre-crimped leads at $0.49, cut in half; $2.06 is an 8-pin plug with its leads |

### Screws, nuts and spacers

| Part | How many |
|---|---|
| M2 nut, nylon | 2 |
| M2 x 6 screw, nylon | 2 |
| M3 lock nut, steel | 16 |
| M3 nut, nylon | 8 |
| M3 x 10 screw, nylon | 4 |
| M3 x 12 screw, steel | 8 |
| M3 x 30 screw, steel | 4 |
| M3 x 6 spacer, nylon | 4 |
| M3 x 8 screw, nylon | 4 |
| M3 x 8 screw, steel | 4 |
| grommet | 8 |
| insert | 3 |
| patch | 1 |

### Printed

| Part | Material | Note |
|---|---|---|
| leg front left | TPU | 6.6 g of TPU; outputs/cad/print/leg-front-left.3mf from pcs14 cad |
| leg front right | TPU | 6.6 g of TPU; outputs/cad/print/leg-front-right.3mf from pcs14 cad |
| leg back left | TPU | 6.6 g of TPU; outputs/cad/print/leg-back-left.3mf from pcs14 cad |
| leg back right | TPU | 6.6 g of TPU; outputs/cad/print/leg-back-right.3mf from pcs14 cad |
| battery tray | PETG-CF | 29.3 g of PETG_CF; outputs/cad/print/battery-tray.3mf from pcs14 cad |
| module rail | PETG-CF | 11.5 g of PETG_CF; outputs/cad/print/module-rail.3mf from pcs14 cad |
| lidar bracket | PETG-CF | 2.4 g of PETG_CF; outputs/cad/print/lidar-bracket.3mf from pcs14 cad |
| remote id mount | TPU | 1.4 g of TPU; outputs/cad/print/remote-id-mount.3mf from pcs14 cad |
| safety monitor carrier | PETG-CF | 2.8 g of PETG_CF; outputs/cad/print/safety-monitor-carrier.3mf from pcs14 cad |

## V: vision and nav

### Parts

| Part | How many | Each | Total | Checked | If it's gone | Note |
|---|---|---|---|---|---|---|
| [ARK GPS (DroneCAN, u-blox NEO-M9N, BMM150 compass, BMP388 barometer)](https://arkelectron.com/product/ark-gps/)<br>ARK Electronics | 1 | $225.00 | $225.00 | 2026-10-21 | [Holybro DroneCAN M9N GPS (SKU 12032)](https://holybro.com/products/dronecan-m9n-gps): the same M9N and DroneCAN, but 20 g heavier, a different shape for the cradle, and one CAN port |  |
| [Camera Module 3](https://www.pishop.us/product/raspberry-pi-camera-module-3/)<br>Raspberry Pi | 1 | $29.25 | $29.25 | 2026-10-21 | [Raspberry Pi Camera Module 3 Wide (Adafruit 5658)](https://www.adafruit.com/product/5658): the same sensor and board, but a 120 degree view: the mapping's scale and the detector's sizes change | its own cable doesn't fit the Pi 5; the Pi 5 cable is its own line |
| [Raspberry Pi 5 (4 GB) companion computer](https://www.pishop.us/product/raspberry-pi-5-4gb/)<br>Raspberry Pi | 1 | $110.00 | $110.00 | 2026-10-21 | [Raspberry Pi Raspberry Pi 5 8GB](https://www.pishop.us/product/raspberry-pi-5-8gb/): the same board with more memory | up from $60 at launch, after Raspberry Pi's 2026 price rises |
| [Active cooler for the Pi 5](https://www.pishop.us/product/raspberry-pi-active-cooler/)<br>Raspberry Pi | 1 | $10.95 | $10.95 | 2026-10-21 | [Argon 40 THRML 30mm Active Cooler](https://argon40.com/products/argon-thrml-30mm-active-cooler): the same fan header; its height isn't published, so its clearance under the HaLow HAT needs checking |  |
| [HT-HC01P Wi-Fi HaLow card with Pi HAT](https://heltec.org/project/ht-hc01p/)<br>Heltec | 1 | $18.80 | $18.80 | 2026-10-21 | [Heltec Automation HC01P V2 HaLow module, 902-928 MHz](https://heltec.org/project/hc01p-v2/): the same card, chip and HAT with a 27 dBm front end: more current from the Pi, and its own driver config | out of stock on the day: the module $12.90 and its Pi HAT $5.90 (https://heltec.org/project/ht-hc01p-hat/); Heltec lists Pi 1 to 4 only, and the Pi 5 swap is still open |
| [Camera cable, Standard-Mini, 200 mm](https://www.adafruit.com/product/5818)<br>Raspberry Pi | 1 | $2.70 | $2.70 | 2026-10-21 | [Raspberry Pi (via Adafruit) Pi 5 camera cable, 300 mm (5819)](https://www.adafruit.com/product/5819): the same cable, 100 mm longer to route | not the look-alike display cables, which don't work with cameras |
| [915 MHz dipole antenna with an IPEX pigtail (placeholder)](https://www.digikey.com/en/products/detail/taoglas-limited/FXP290-07-0100A/2332717)<br>Various | 1 | $11.07 | $11.07 | 2026-10-21 | [Molex 2111400100 ISM 868/915 MHz flexible antenna](https://www.digikey.com/en/products/detail/molex/2111400100/9953925): the same connector, cheaper, but dual-band and lower gain | the pick for the placeholder: Taoglas FXP290.07.0100A, a 75 x 45 mm flex antenna, 1.5 dBi, U.FL; DigiKey's price came from its search listing, and it needs a flat spot away from the carbon |
| Module plug (an XT30U and an 8-pin JST-GH)<br>Amass and JST | 1 | $2.80 | $2.80 | 2026-10-21 | Amass and JST the same halves from the XT30 and JST-GH fallbacks: see those two | an estimate from its pieces: an XT30U half ($0.32) and an 8-pin JST-GH plug with leads (about $2.48) |
| [microSD card for the Pi](https://www.pishop.us/product/raspberry-pi-sd-card-64gb/)<br>Raspberry Pi microSD card, 64 GB, A2 | 1 | $30.95 | $30.95 | 2026-10-21 | SanDisk Extreme 64GB microSDXC A2: the same class; its price couldn't be confirmed on the day | The Pi 5 boots from it; Raspberry Pi's own A2 card is the one specified for the Pi 5 |
| Carbon tube for the GPS mast<br>Any Carbon fiber tube, 8 mm outside, at least 100 mm long | 1 | ? | ? |  |  | The mast's tube, 8 mm across and 90 mm tall in the CAD (design/cad.yaml); the printed foot and cradle hold it |

### Wire

| Part | How many | Each | Total | Checked | If it's gone | Note |
|---|---|---|---|---|---|---|
| [Thin PVC hookup lead for JST plugs, 26 AWG](https://www.adafruit.com/product/2517)<br>Various | 1 m | $0.65 | $0.65 | 2026-10-21 | [BNTECHGO 28 AWG silicone wire, red and black, 10 ft](https://www.amazon.com/dp/B01F8PO7UK): silicone in place of PVC, the same gauges | 0.72 m in the connection list, plus 30% |
| [Silicone hookup wire, UL style 3135, 20 AWG](https://www.racedayquads.com/products/silicone-wire-2-ft-red-and-black-pair)<br>Various (UL 3135) | 0.2 m | $4.08 | $0.82 | 2026-10-21 | [BNTECHGO silicone wire, red and black, 10 ft a color](https://www.amazon.com/dp/B01ABOPMEI): the same gauges, 200 C and 600 V, sold by the 10 ft | 0.08 m in the connection list, plus 30% |

### Plugs

| Part | How many | Each | Total | Checked | If it's gone | Note |
|---|---|---|---|---|---|---|
| [GH series wire-to-board connector, 1.25 mm pitch, 4-pin](https://www.mouser.com/en/ProductDetail/JST-Commercial/AGHGH28K305?qs=QpmGXVUTftHuHDeXhn0HhA%3D%3D)<br>JST | 1 | $1.90 | $1.90 | 2026-10-21 | [elechawk GH1.25 pre-crimped cable kit, 15 cm](https://www.amazon.com/dp/B07PBHN7TM): pre-crimped and cheaper per plug, but a clone, not genuine JST | the wire's half; genuine JST from Mouser: housings $0.10 (4-pin) to $0.16 (8-pin) and pre-crimped leads at $0.58, cut in half for two ends; $1.90 is a typical 6-pin plug with its leads |

### Screws, nuts and spacers

| Part | How many |
|---|---|
| M2 nut, nylon | 4 |
| M2 x 8 screw, nylon | 4 |
| M2.5 x 11 standoff, nylon | 4 |
| M2.5 x 6 screw, nylon | 8 |
| M2.5 x 6 standoff, nylon | 4 |
| M3 nut, nylon | 2 |
| M3 x 10 screw, steel | 1 |
| M3 x 8 screw, nylon | 2 |
| tape | 4 |

### Printed

| Part | Material | Note |
|---|---|---|
| gps mast | TPU | 3.9 g of TPU; outputs/cad/print/gps-mast.3mf from pcs14 cad |
| gps cradle | TPU | 7.7 g of TPU; outputs/cad/print/gps-cradle.3mf from pcs14 cad |
| camera bracket | PETG-CF | 2.4 g of PETG_CF; outputs/cad/print/camera-bracket.3mf from pcs14 cad |
| v housing | PETG-CF | 39.9 g of PETG_CF; outputs/cad/print/v-housing.3mf from pcs14 cad |

## P: the parachute

### Parts

| Part | How many | Each | Total | Checked | If it's gone | Note |
|---|---|---|---|---|---|---|
| [Harrier 40-42 parachute bundle](https://shop.fruitychutes.com/products/harrier-40-42-drone-parachute-bundle-2-5kg-4-6m-s)<br>Fruity Chutes | 1 | $507.81 | $507.81 | 2026-10-21 | [Fruity Chutes Harrier 50-48 bundle, 3.2 kg at 4.6 m/s](https://shop.fruitychutes.com/products/harrier-50-48-drone-parachute-bundle-3-2kg-4-6m-s): the next size up: 81 g heavier, a longer tube for the mount, and it needs more height to open | sold out on the day, quote only; no servo, mount or trigger in the bundle, and Fruity Chutes doesn't publish the servo or the opening time |
| [ARK CANnode (DroneCAN node with 8 PWM outputs)](https://arkelectron.com/product/ark-cannode/)<br>ARK Electronics | 1 | $150.00 | $150.00 | 2026-10-21 | [Matek CAN-L4-PWM (AP_Periph)](https://www.getfpv.com/mateksys-ap-periph-dronecan-to-pwm-adapter-can-l4-pwm.html): a different node and firmware: no IMU, one CAN port, servo power on its own pads, so the harness changes; its price couldn't be confirmed |  |
| [74LVC1G157 two-input multiplexer on a SOT-23-6 adapter](https://www.mouser.com/ProductDetail/Nexperia/74LVC1G157GV125?qs=me8TqzrmIYVvTEwYoevmpg%3D%3D)<br>Nexperia (chip) | 1 | $1.43 | $1.43 | 2026-10-21 | [Texas Instruments SN74LVC1G97DBVR, wired as a 2-to-1 mux](https://www.mouser.com/en/ProductDetail/Texas-Instruments/SN74LVC1G97DBVR?qs=nqigI8dpoHK0Hd%2FJSa%2FqPA%3D%3D): in stock, the same footprint and supply pins, but its select works the other way round: the two data inputs swap in the connection list | the 74LVC1G157GV ($0.18) was back ordered until October 2027; with a SparkFun BOB-00717 adapter ($1.25) |
| [D36V6F3 3.3 V 600 mA step-down regulator (item 3791)](https://www.pololu.com/product/3791)<br>Pololu | 1 | $5.95 | $5.95 | 2026-10-21 | [Pololu D24V5F3 (item 2842)](https://www.pololu.com/product/2842): the same size and pins; 36 V in at most (fine on 6S) and 500 mA out |  |
| [LM66200 Ideal Dual Diodes Breakout](https://www.adafruit.com/product/5830)<br>Adafruit (board), Texas Instruments (chip) | 1 | $2.50 | $2.50 | 2026-10-21 | [Adafruit (via Mouser) the same board, Mouser 485-5830](https://www.mouser.com/en/ProductDetail/Adafruit/5830?qs=mELouGlnn3cI9zwLa2jyDA%3D%3D): the same board from a second shop |  |
| Module plug (an XT30U and an 8-pin JST-GH)<br>Amass and JST | 1 | $2.80 | $2.80 | 2026-10-21 | Amass and JST the same halves from the XT30 and JST-GH fallbacks: see those two | an estimate from its pieces: an XT30U half ($0.32) and an 8-pin JST-GH plug with leads (about $2.48) |
| [Release servo (stand-in)](https://hitecrcd.com/hs-55-economy-feather-servo/)<br>Hitec RCD HS-55 micro servo (31055S) | 1 | $16.99 | $16.99 | 2026-10-21 | [Hitec RCD HS-65MG (32065S)](https://hitecrcd.com/hs-65mg-metal-gear-analog-micro-servo/): metal gears and more torque, 4 g heavier; maybe the better release servo | The Harrier bundle has no servo. This is the design's stand-in until Fruity Chutes says which one theirs is |

### Wire

| Part | How many | Each | Total | Checked | If it's gone | Note |
|---|---|---|---|---|---|---|
| [Thin PVC hookup lead for JST plugs, 26 AWG](https://www.adafruit.com/product/2517)<br>Various | 0.4 m | $0.65 | $0.26 | 2026-10-21 | [BNTECHGO 28 AWG silicone wire, red and black, 10 ft](https://www.amazon.com/dp/B01F8PO7UK): silicone in place of PVC, the same gauges | 0.24 m in the connection list, plus 30% |
| [Thin PVC hookup lead for JST plugs, 28 AWG](https://www.racedayquads.com/products/rdq-silicone-wire-6-roll-build-kit-28awg)<br>Various | 0.4 m | $0.30 | $0.12 | 2026-10-21 | [BNTECHGO 28 AWG silicone wire, red and black, 10 ft](https://www.amazon.com/dp/B01F8PO7UK): silicone in place of PVC, the same gauges | 0.28 m in the connection list, plus 30% |
| [Silicone hookup wire, UL style 3135, 22 AWG](https://www.racedayquads.com/products/silicone-wire-2-ft-red-and-black-pair)<br>Various (UL 3135) | 0.2 m | $4.08 | $0.82 | 2026-10-21 | [BNTECHGO silicone wire, red and black, 10 ft a color](https://www.amazon.com/dp/B01ABOPMEI): the same gauges, 200 C and 600 V, sold by the 10 ft | 0.14 m in the connection list, plus 30% |

### Plugs

| Part | How many | Each | Total | Checked | If it's gone | Note |
|---|---|---|---|---|---|---|
| [GH series wire-to-board connector, 1.25 mm pitch, 4-pin](https://www.mouser.com/en/ProductDetail/JST-Commercial/AGHGH28K305?qs=QpmGXVUTftHuHDeXhn0HhA%3D%3D)<br>JST | 1 | $1.90 | $1.90 | 2026-10-21 | [elechawk GH1.25 pre-crimped cable kit, 15 cm](https://www.amazon.com/dp/B07PBHN7TM): pre-crimped and cheaper per plug, but a clone, not genuine JST | the wire's half; genuine JST from Mouser: housings $0.10 (4-pin) to $0.16 (8-pin) and pre-crimped leads at $0.58, cut in half for two ends; $1.90 is a typical 6-pin plug with its leads |
| [GH series wire-to-board connector, 1.25 mm pitch, 10-pin](https://www.mouser.com/en/ProductDetail/JST-Commercial/AGHGH28K305?qs=QpmGXVUTftHuHDeXhn0HhA%3D%3D)<br>JST | 1 | $1.90 | $1.90 | 2026-10-21 | [elechawk GH1.25 pre-crimped cable kit, 15 cm](https://www.amazon.com/dp/B07PBHN7TM): pre-crimped and cheaper per plug, but a clone, not genuine JST | the wire's half; genuine JST from Mouser: housings $0.10 (4-pin) to $0.16 (8-pin) and pre-crimped leads at $0.58, cut in half for two ends; $1.90 is a typical 6-pin plug with its leads |

### Screws, nuts and spacers

| Part | How many |
|---|---|
| 4-40 x 6.35 screw, steel | 3 |
| M3 x 12 screw, steel | 2 |

### Printed

| Part | Material | Note |
|---|---|---|
| p holder | PETG-CF | 8.4 g of PETG_CF; outputs/cad/print/p-holder.3mf from pcs14 cad |

## C: the claws

### Parts

| Part | How many | Each | Total | Checked | If it's gone | Note |
|---|---|---|---|---|---|---|
| Claws and servos (placeholder)<br>Various | 1 | ? | ? | 2026-10-21 | none: a placeholder until the claws are designed |  |
| [ARK CANnode (DroneCAN node with 8 PWM outputs)](https://arkelectron.com/product/ark-cannode/)<br>ARK Electronics | 1 | $150.00 | $150.00 | 2026-10-21 | [Matek CAN-L4-PWM (AP_Periph)](https://www.getfpv.com/mateksys-ap-periph-dronecan-to-pwm-adapter-can-l4-pwm.html): a different node and firmware: no IMU, one CAN port, servo power on its own pads, so the harness changes; its price couldn't be confirmed |  |
| Module plug (an XT30U and an 8-pin JST-GH)<br>Amass and JST | 1 | $2.80 | $2.80 | 2026-10-21 | Amass and JST the same halves from the XT30 and JST-GH fallbacks: see those two | an estimate from its pieces: an XT30U half ($0.32) and an 8-pin JST-GH plug with leads (about $2.48) |

### Wire

| Part | How many | Each | Total | Checked | If it's gone | Note |
|---|---|---|---|---|---|---|
| [Thin PVC hookup lead for JST plugs, 26 AWG](https://www.adafruit.com/product/2517)<br>Various | 0.4 m | $0.65 | $0.26 | 2026-10-21 | [BNTECHGO 28 AWG silicone wire, red and black, 10 ft](https://www.amazon.com/dp/B01F8PO7UK): silicone in place of PVC, the same gauges | 0.24 m in the connection list, plus 30% |
| [Thin PVC hookup lead for JST plugs, 28 AWG](https://www.racedayquads.com/products/rdq-silicone-wire-6-roll-build-kit-28awg)<br>Various | 0.2 m | $0.30 | $0.06 | 2026-10-21 | [BNTECHGO 28 AWG silicone wire, red and black, 10 ft](https://www.amazon.com/dp/B01F8PO7UK): silicone in place of PVC, the same gauges | 0.08 m in the connection list, plus 30% |
| [Silicone hookup wire, UL style 3135, 20 AWG](https://www.racedayquads.com/products/silicone-wire-2-ft-red-and-black-pair)<br>Various (UL 3135) | 0.3 m | $4.08 | $1.22 | 2026-10-21 | [BNTECHGO silicone wire, red and black, 10 ft a color](https://www.amazon.com/dp/B01ABOPMEI): the same gauges, 200 C and 600 V, sold by the 10 ft | 0.15 m in the connection list, plus 30% |

### Plugs

| Part | How many | Each | Total | Checked | If it's gone | Note |
|---|---|---|---|---|---|---|
| [GH series wire-to-board connector, 1.25 mm pitch, 4-pin](https://www.mouser.com/en/ProductDetail/JST-Commercial/AGHGH28K305?qs=QpmGXVUTftHuHDeXhn0HhA%3D%3D)<br>JST | 1 | $1.90 | $1.90 | 2026-10-21 | [elechawk GH1.25 pre-crimped cable kit, 15 cm](https://www.amazon.com/dp/B07PBHN7TM): pre-crimped and cheaper per plug, but a clone, not genuine JST | the wire's half; genuine JST from Mouser: housings $0.10 (4-pin) to $0.16 (8-pin) and pre-crimped leads at $0.58, cut in half for two ends; $1.90 is a typical 6-pin plug with its leads |
| [GH series wire-to-board connector, 1.25 mm pitch, 10-pin](https://www.mouser.com/en/ProductDetail/JST-Commercial/AGHGH28K305?qs=QpmGXVUTftHuHDeXhn0HhA%3D%3D)<br>JST | 1 | $1.90 | $1.90 | 2026-10-21 | [elechawk GH1.25 pre-crimped cable kit, 15 cm](https://www.amazon.com/dp/B07PBHN7TM): pre-crimped and cheaper per plug, but a clone, not genuine JST | the wire's half; genuine JST from Mouser: housings $0.10 (4-pin) to $0.16 (8-pin) and pre-crimped leads at $0.58, cut in half for two ends; $1.90 is a typical 6-pin plug with its leads |

### Screws, nuts and spacers

| Part | How many |
|---|---|
| M3 lock nut, steel | 2 |
| M3 x 10 screw, steel | 2 |

## Bought once

### On the ground

| Part | How many | Each | Total | Checked | If it's gone | Note |
|---|---|---|---|---|---|---|
| [Transmitter](https://radiomasterrc.com/products/pocket-radio-controller-m2)<br>RadioMaster Pocket (M2) ELRS, FCC version | 1 | $71.50 | $71.50 | 2026-10-21 | [RadioMaster Boxer EdgeTX ELRS](https://www.racedayquads.com/products/pre-order-radiomaster-boxer-edgetx-rc-transmitter-choose-version): full-size gimbals and up to 1 W, at two and a half times the price; the switch names change | The pilot's sticks and the kill switch, over 2.4 GHz ExpressLRS (the control link stays off 900 MHz). SA arms, SD is the kill switch, both two-position latching. Takes two 18650s, not included |
| [HaLow on the laptop's side](https://heltec.org/project/ht-h7608/)<br>Heltec Automation HT-H7608 V2 HaLow router, 902-928 MHz | 1 | $79.00 | $79.00 | 2026-10-21 | [Morse Micro (with GL.iNet) HaLowLink 2](https://www.gl-inet.com/en-us/products/halowlink2): Morse Micro's own router, about $130 (seen in search results), but a newer MM8108 chip: bench-test it against the drone's MM6108 first | The ground end of V's video and telemetry link, over Ethernet to the laptop. The same MM6108 chip as the drone's card. Which card the drone gets is still my call |
| [Balance charger](https://pyrodrone.com/collections/all/products/toolkitrc-m8ac-1-8s-ac-200w-dc-600w-20a-battery-charger-xt60)<br>ToolkitRC M8AC, AC 200 W / DC 600 W | 1 | $121.99 | $121.99 | 2026-10-21 | [HOTA D6 Pro dual channel](https://www.racedayquads.com/products/hota-d6-pro-dual-channel-325w-15a-ac-dc-battery-charger): the same 200 W AC limit, two channels, bulkier | Charges the 6S Li-ion pack through its balance lead. On AC it tops out around 6 to 7 A for this pack; a full 8 A needs a 24 V DC supply |

### Supplies

| Part | How many | Each | Total | Checked | If it's gone | Note |
|---|---|---|---|---|---|---|
| [Nickel-plated copper strip, 10 x 0.3 mm, 2 m](https://www.amazon.com/dp/B0G1KL5ZS9)<br>RIWETRA Nickel-plated copper strip, 10 mm x 0.3 mm, 2 m | 1 | $28.00 | $28.00 | 2026-10-21 | [Unbranded nickel-plated copper strip, 8 x 0.15 mm, 10 ft](https://www.amazon.com/dp/B0B789WW5D): thinner: two or three layers stacked for the same current, or the pack's limit rechecked | The pack's cell links: copper carries the 90 A cap at 15 A/mm2, where nickel strip would run at 37. Small spot welders struggle with 0.3 mm copper: check the welder |
| [Insulator rings for 21700 cells, 20](https://www.18650batterystore.com/products/21700-insulator-black)<br>18650 Battery Store 21700 battery terminal insulator rings, black, 20 pcs | 1 | $1.49 | $1.49 | 2026-10-21 |  | Insulates each cell's positive end from the strip |
| [Pack heat shrink](https://www.amazon.com/dp/B09SVFL33L)<br>JichuET PVC heat shrink, 200 mm flat, 3 m | 1 | $13.99 | $13.99 | 2026-10-21 |  | The pack's outer wrap; the flat width depends on the cell layout |
| [6S balance lead](https://www.getfpv.com/balance-lead-replacement-cable-6s-jst-xh.html)<br>GetFPV 6S JST-XH balance lead, 100 mm, 22 AWG silicone | 1 | $2.99 | $2.99 | 2026-10-21 |  | The seven wires from the pack's junctions to its JST-XH plug |
| Heat shrink assortment<br>Any Polyolefin heat shrink, 3 to 10 mm | 1 | ? | ? |  |  | Over every soldered end in the wiring guide, 3 mm to 10 mm |

### Tools

| Part | How many | Each | Total | Checked | If it's gone | Note |
|---|---|---|---|---|---|---|
| [Smoke stopper](https://www.racedayquads.com/products/vifly-short-saver-2-smoke-stopper-xt30-xt60)<br>ViFly Short Saver 2 (XT30 and XT60) | 1 | $17.49 | $17.49 | 2026-10-21 | [JHEMCU XT30 / XT60 Smoke Stopper](https://www.racedayquads.com/products/jhemcu-xt30-xt60-smoke-stopper): a resettable fuse with a 0.5 A hold: only good for the very first power-on | An electronic fuse in series for the first power-up, so a wiring mistake trips instead of burning. Use its 2 A setting so the ESC's capacitors don't trip it |
| Soldering iron, solder and flux<br>Any A temperature-controlled soldering station | 1 | ? | ? |  |  | A temperature-controlled iron that holds its heat on the ESC's 12 AWG pads, solder and flux |
| Multimeter<br>Any A digital multimeter with continuity and a low ohms range | 1 | ? | ? |  |  | Every check in the wiring guide and the test plans; one that reads continuity and low resistance |
| Spot welder<br>Any A battery spot welder that can weld 0.3 mm copper strip | 1 | ? | ? |  |  | The pack's strip goes on by spot welding; cells are never soldered. Not needed if the pack is bought built |
| Prop balancer<br>Any A magnetic prop balancer for 5 mm bores | 1 | ? | ? |  |  | The arms ring sideways close to what an unbalanced prop shakes them at in a hover (the structure report) |

### Spares

| Part | How many | Each | Total | Checked | If it's gone | Note |
|---|---|---|---|---|---|---|
| [Props, a spare set](https://www.getfpv.com/gemfan-1050-cl-cinelifter-3-blade-propeller-set-of-2-glass-fiber-nylon.html)<br>Gemfan 1050 tri-blade, a pair | 2 | $11.99 | $23.98 | 2026-10-21 |  | Props break; a set of four, two each way, like the build's (sold in pairs) |
| [MINI fuses, spares](https://www.mouser.com/en/ProductDetail/Littelfuse/0297003.WXNV?qs=WtG364jHAdxHR7%2F%2F%252BiOsmQ%3D%3D)<br>Littelfuse MINI blade fuses, 297 series, two 3 A and two 2 A | 4 | $0.39 | $1.56 | 2026-10-21 |  | The two branch fuses are soldered in; keep spares of both ratings |
