# Working on the hardware

So why would I need this you might ask? Well I successfully overwrote the first few
bytes in the flash that the MCU uses to configure it's boot. This worked out finee
when I was overwriting it with `0xff` because the bootloader would detect it as an
invalid firmware file and go into USB flashloader. But I needed to play with it and
with that I noticed that `0xcoffee` is a valid beginning of a firmware file - except
that it jumps into nothing.

So here I go recovering the bricked thermal camera. Opening it up revealed an ARM based
ST MCU, lots of really really tiny circuits and PCBs and a 5pin JST SUR connector
with 0.8mm line width (that is soo tiny it's unbelievable). Of course my eyes locked
on the 5pin connector because that connector looks suspiciously like an SWD header.
It took me a month or so to source this absurdly tiny connector in reasonable
quantities (I'm sorry aliexpress I don't wanna have 500 of those flying around).
Luckily one can order free samples at JST.

So here is the pinout of that connector assuming the tiny square on it marks pin one.

```
1 - -1.8V
2 - 0
3 - -1.8
4 - 0
5 - GND
```

