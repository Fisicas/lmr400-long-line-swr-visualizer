# Apparent SWR of Long Open-Ended LMR-400 Coax

## Core observation

An antenna analyzer connected to a short, low-loss coaxial cable with the far end left open should report a very high SWR, because nearly all of the launched wave reflects from the open circuit and returns to the analyzer. A long real cable behaves differently. The open-circuit reflection still occurs at the far end, but the returning wave is attenuated by the cable on both the outward and return paths. The analyzer therefore sees a reduced reflection coefficient and may report a moderate or even deceptively low SWR.

This means a low SWR reading through a long feedline does not by itself prove that the antenna or load is well matched. It may simply indicate that the line loss has attenuated the reflected wave.

## Reflection coefficient and SWR

For a nominally matched transmission line, the load-end reflection coefficient is propagated back to the analyzer as

\[
\Gamma_\mathrm{in} = \Gamma_L e^{-2\gamma l}
\]

where

\[
\gamma = \alpha + j\beta
\]

is the propagation constant, \(l\) is cable length, \(\alpha\) is the attenuation constant, and \(\beta\) is the phase constant. For an open circuit,

\[
\Gamma_L = +1
\]

so the magnitude at the analyzer is approximately

\[
|\Gamma_\mathrm{in}| = e^{-2\alpha l}.
\]

If the one-way matched-line loss is expressed in dB, the open-circuit reflection coefficient magnitude at the analyzer can be written as

\[
|\Gamma_\mathrm{in}| \approx 10^{-L_\mathrm{one-way,dB}/10}.
\]

The apparent SWR is then

\[
\mathrm{SWR} = \frac{1 + |\Gamma_\mathrm{in}|}{1 - |\Gamma_\mathrm{in}|}.
\]

The factor of 10 in the exponent is important: the reflected voltage wave experiences the one-way loss twice, so the round-trip reflected-voltage attenuation is numerically equivalent to using the one-way dB loss divided by 10.

## Electrical-length behavior

The input impedance of an open or short transmission line rotates strongly with frequency because the cable electrical length changes as frequency changes. For an open circuit, half-wave intervals tend to reproduce the open condition at the analyzer, while odd quarter-wave intervals transform the open circuit toward a low impedance. The approximate spacing of these impedance rotations is

\[
\Delta f \approx \frac{v_p}{2l}
\]

where \(v_p\) is the phase velocity of the cable.

For LMR-400, \(v_p \approx 0.84c\). For a 21 m length,

\[
\Delta f \approx \frac{0.84c}{2(21\,\mathrm{m})} \approx 6.0\,\mathrm{MHz}.
\]

Thus the impedance and reflection phase can show rapid periodic structure. However, for an ideal open or short on a 50 Ω line measured by a 50 Ω analyzer, the magnitude of the reflection coefficient follows the attenuation envelope much more strongly than the phase rotation. Large periodic SWR swings generally indicate nonidealities such as frequency-dependent characteristic impedance, connector effects, imperfect opens/shorts, analyzer reference-plane behavior, or other parasitics.

## Practical LMR-400 estimate

Times Microwave lists LMR-400 as a 50 Ω cable with 84% velocity of propagation and typical attenuation values of 0.7 dB/100 ft at 30 MHz, 1.5 dB/100 ft at 150 MHz, 1.9 dB/100 ft at 220 MHz, 2.7 dB/100 ft at 450 MHz, 3.9 dB/100 ft at 900 MHz, 6.8 dB/100 ft at 2.5 GHz, and 10.8 dB/100 ft at 5.8 GHz.

For a 21 m run, these values give approximately:

| Frequency | One-way loss | Apparent open-circuit SWR |
|---:|---:|---:|
| 30 MHz | 0.48 dB | 18.0:1 |
| 150 MHz | 1.03 dB | 8.4:1 |
| 220 MHz | 1.31 dB | 6.7:1 |
| 450 MHz | 1.86 dB | 4.7:1 |
| 900 MHz | 2.69 dB | 3.3:1 |
| 2.5 GHz | 4.69 dB | 2.0:1 |
| 5.8 GHz | 7.44 dB | 1.44:1 |

So an observed reading near 6:1 on a long open-ended LMR-400 run is not anomalous in the upper-VHF/lower-UHF range. It is a normal consequence of reflected-wave attenuation in the feedline.

## Practical conclusion

The correct diagnostic interpretation is that a long lossy cable can hide a severe load mismatch. Measuring a good SWR at the transmitter end of a long feedline is not equivalent to measuring a good SWR at the antenna terminals. A dummy load at the far end should still read near 1:1, but an open-ended long cable can also appear less severe than expected because the reflected wave is reduced before it returns to the analyzer.
