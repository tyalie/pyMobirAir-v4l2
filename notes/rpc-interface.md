## The RPC? interface
It is currently not completely know if it actually is an RPC interface but it looks
and smells like one, at least partly.

### Commands
#### GetArmParam
When one sends `GetArmParam=<BYTES>` to the camera, it will return some data.
Interesting here is the `<BYTES>` section which seems to be structured as follows:
```c
struct {
  uint_16 address : 16,
  : 8  // currently unknown
  uint_16 offset : 8,
  uint_16 number_of_bytes : 16
}
```

My first guess was to assume that `address` mapped to the device memory, but I
quickly discovered I was wrong. During init by the SDK the module accesses `0xe801` 
and `0xe701`. These two are spaced 1B apart - assuming little endian - but return non
overlapping bytes.

So we are probably working here with actual parameters that are mapped internally. 
Interesting enough there are limits how many bytes can be returned until which the
camera either resets and closes the USB connection or doesn't return anything.

*EDIT*
Well as it turns it the first guess was correct and just needed a bit of adaptation.
The address parameter maps to the address `address * 0x800 + <unknown offset>` in the 
physical memory.

*EDIT 2*
There is also seemingly an `offset` parameter which moves the starting point by 256B.
So the formula for physical memory address is 
`address * 0x800 + offset * 0x100 + 0x0800_0000`.


##### `2c01`
- max length: 51201B (0xC801)
  - limit behavior: doesn't return anything

This seems to be some kind of calibration document?

- output can be parsed as 120x90 images as `uint_16` little endian
  - images are bright at the edges and dark in the middle
  - min: 7939 / max: 11665
  - small change between the two images
- there are 480B before each image filled with the word `0x0020`
- remaining 7041B also start with 480B of `0x0020`
  - seems to be part of an 120x90 image

All three images have a bright white dot in the upper left corner. I assume it's a
problem on the sensor or something? But especially the latter matches there so I
assume we're looking at a third but incomplete image.

##### `e801`
- default length: 2B
- max length: see below
  - limit behavior: read other memory areas / reset camera (after 0xC000 bytes)

My camera returns `03 00` for this command.

Interestingly even though the camera will reset if the default length is too far large,
we can still go far over the initial 2B. At 2048B we will actually find the value of
`e901` instead. The return becomes filled with `0xFF` after byte 8192.

Other interesting bits:
- byte  2048 (0x0800): return of `e901`
- byte  4096 (0x1000): `03 01 90 ee fe ff`
- byte  6144 (0x1800): `GHGN90405E008A017`
- after 8192 (0x2000): `0xFF`
- after 0xC000 bytes: crash camera


##### `e701`
- default length: 6B

Very similar to `e801`. Returns `74 03 2d 07 d0 0a`

As expected from `e801` can one find the value `03 00` at byte 2048 and so on.
Interestingly one can read up to 0xC800 bytes until a crash, which could mean that
this is the limit of the memory we are in.


#### Binary dump
In the previous section I was able to understand the format of the `GetArmParam`
method. So naturally I did a whole memory dump as can be found in `memory.bin`.

Some interesting bits are listed below

### SaveArmParam
```c
struct {
  uint_16 address : 16
  uint_16 length : 16
}
```

Where `length` < 0x800


#### All supported commands

These strings could be found in the memory dump
```
StartX     ShutterOff     SetParamDetect
StopX      ShutterStop    SetDetectIndex
Resume     ShutterOn      SaveArmParam
Reset      ResetFactory   GetParamLine
DoNUC      GetArmParam    ShutterStop
```

Known commands and their usage are:
```
ShutterOn=1
ShutterOff=1
StopX=1  # stop sending data
StartX=1  # start sending data
GetArmParam  # see above
```


### Getting into the bootloader

Yeaaahh. You know that command up there with `SaveArmParam`? I have no official
syntax for it so I tried giving it zeros until something happens. As it turns out I'm
not working on RAM here. The `GetArmParam` and `SaveArmParam` work on the internal
flash and are persistent. 

After I successfully wrote stuff to the first few bytes with
`SaveArmParam=\x00\x00\x00\x00` (or similar) I replugged the camera and was greeted
by a STM32 Bootloader in DFU mode - oops

What at first looked like a bricked camera turned out to be an STM32 chip that I can
reflash with the known image I downloaded previously using `GetArmParam` and get the
camera up running again. I'm still in disbelieve that I was lucky enough to have
__correctly__ retrieved a firmware dump through hacky ways __before__ that this
worked. That was really not planned.
