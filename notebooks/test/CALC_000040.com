%chk=CALC_000040.chk
%mem=4GB
%NProcShared=1
#P SP HF/cc-pVTZ gfinput fchk=all out=wfx

CALC_000040 neon HF cc-pVTZ

0 1
Ne 0.0 0.0 0.0

CALC_000040.wfx

