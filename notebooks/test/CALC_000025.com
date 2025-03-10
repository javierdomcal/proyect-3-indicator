%chk=CALC_000025.chk
%mem=4GB
%NProcShared=1
#P SP HF/aug-cc-pVTZ gfinput fchk=all out=wfx

CALC_000025 helium HF aug-cc-pVTZ

0 1
He    0.0000   0.0000   0.0000

CALC_000025.wfx

