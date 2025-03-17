%chk=CALC_000022.chk
%mem=4GB
%NProcShared=1
#P SP HF/aug-cc-pVDZ gfinput fchk=all out=wfx

CALC_000022 helium HF aug-cc-pVDZ

0 1
He    0.0000   0.0000   0.0000

CALC_000022.wfx

