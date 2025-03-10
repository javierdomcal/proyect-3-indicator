%chk=CALC_000151.chk
%mem=4GB
%NProcShared=1
#P SP HF/aug-cc-pVTZ gfinput fchk=all out=wfx

CALC_000151 neon HF aug-cc-pVTZ

0 1
Ne 0.0 0.0 0.0

CALC_000151.wfx
