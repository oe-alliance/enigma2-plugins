ReconstructApSc-1.0
-------------------
2009-12-14
Anders Holst (aho@sics.se)


This plugin makes it possible to reconstruct missing or corrupt .ap
and .sc files of recorded movies. These files are used for precise
seeking and winding in the movie, and also for finding the cut
positions when using the plugin MovieCut to cut movies. 

Situations when this plugin may be useful include:
 * The .sc files are relatively new, so movies recorded with Enigma2
   from before the spring of 2009 doesn't have them.
 * The previous version of MovieCut did not know about .sc, and
   therefore produced no such file for the resulting cut movie.
 * If you have cut your movies on a PC, you may not get any .ap or .sc
   files. 
 * If a specific movie is impossible to seek correctly in, or just
   gets black or a frozen picture when trying to fast forward or
   rewind, then one may suspect that the coresponding .ap and .sc
   have got corrupt for some reason.
 * When downloading ts-files from internet, there may not be any
   provided .ap and .sc.
 * After a disk crash it may be possible to rescue the .ts files
   (because their specific structure) but perhaps not the others.

The plugin uses the C++ program "reconstruct_apsc" to scan through the
.ts file, and store the structural information into the .ap and .sc
files. You can either tell the program to reconstruct the files for a
specific movie, in which case any existing .ap and .sc for that movie
will be removed first. Or, you can tell it to reconstruct all files in
a specific directory, in which case it only reconstructs missing .ap
and .sc files. The typical situation is that you have a directory with
many older movies that don't have any .sc files. Note that
reconstructing .sc files for all movies in a directory may take
considerable time and disk activity. If the process should be
interupted for some reason, it should however be able to continue from
there next time you start it.

Disclaimer

I have tried to be careful, and to make it reasonably safe to use: It
should never change or overwrite the actual .ts file, but only the .ap
and .sc files; It checks for errors during the process and will abort
in a controlled way if it happens; It remembers which file it was
processing if it gets interupted so it can start from there next time,
not leaving any half-finished .ap or .sc.

However, all use will be on your own risk. I will not take
responsibility for any damage or loss of movies or other files due to
either bugs in the program or uncareful use. 

