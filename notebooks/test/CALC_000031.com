%chk=CALC_000031.chk
%mem=4GB
%NProcShared=1
#P SP HF/aug-cc-pVTZ gfinput fchk=all out=wfx

CALC_000031 berilium HF aug-cc-pVTZ

0 1
Be    0.0000   0.0000   0.0000

CALC_000031.wfx

