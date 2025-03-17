%chk=CALC_000149.chk
%mem=4GB
%NProcShared=1
#P SP HF/aug-cc-pVDZ gfinput fchk=all out=wfx

CALC_000149 neon HF aug-cc-pVDZ

0 1
Ne 0.0 0.0 0.0

CALC_000149.wfx
