%chk=CALC_000041.chk
%mem=4GB
%NProcShared=1
#P SP HF/aug-cc-pVTZ gfinput fchk=all out=wfx

CALC_000041 neon HF aug-cc-pVTZ

0 1
Ne 0.0 0.0 0.0

CALC_000041.wfx

