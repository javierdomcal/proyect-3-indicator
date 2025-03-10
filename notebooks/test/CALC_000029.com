%chk=CALC_000029.chk
%mem=4GB
%NProcShared=1
#P SP HF/aug-cc-pVDZ gfinput fchk=all out=wfx

CALC_000029 berilium HF aug-cc-pVDZ

0 1
Be    0.0000   0.0000   0.0000

CALC_000029.wfx

