# Introduction

This in-progress project aims to create an MPD-based internet radio player on Raspberry Pi 3, with functionalities similar to that of an actual radio. In its final state, the player will have an LCD display (HD44780U compatible) showing station information and remote control via infrared-red (IR) receiver.

We will implement three different clients, with each subsequent one increasing in level of complexity:

1. Client A - This is the most basic client which is controlled by logging in through SSH.
2. Client B - This client adds an LCD display which shows station information, but is otherwise mostly similar to Client A in terms of control.
3. Client C - This client will have both an LCD display and an IR receiver. Under normal circumstances, it should function without having to log in through SSH. Station change and the running of most functions will be done through an IR remote control.

Although Raspberry Pi 3 is used in the implemention of this project, the directions provided here should generally work for Pi 2 and 4, with slight modifications here and there. It is assumed that the reader has some working familiarity with Linux commands.

# Build Instructions

To be continued...
