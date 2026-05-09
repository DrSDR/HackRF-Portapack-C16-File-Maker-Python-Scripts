ok this is for folks with a hackrf portapack.

c16 and txt files can be copied to your sd card   (captures folder is good place)

then use replay to transmit the files.

the two files are:

one is an am signal at 1700khz,  to test this, i attached a 20dB pad to the rf out of the hackrf,  then connected it to a loop of wire.
place am radio near loop of wire and should hear am signal at 1700khz.

second file transmits on 7 of the frs channels at the same time.
tune your frs radio to ch 1 to 7 to hear the jamming signal.

three py files are attached to see how am and 7 frs and a wbfm signal where created in python and saves off the txt file and c16 file that are needed for the portapack sd card.

thanks for reading and enjoy.

dr. moonshine

