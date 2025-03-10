%chk=CALC_000024.chk
%mem=4GB
%NProcShared=1
#P SP HF/cc-pVTZ gfinput fchk=all out=wfx

CALC_000024 helium HF cc-pVTZ

0 1
He    0.0000   0.0000   0.0000

CALC_000024.wfx

