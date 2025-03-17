%chk=CALC_000116.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(2,2)/aug-cc-pVQZ gfinput fchk=all density=current iop(5/33=1) out=wfx

CALC_000116 hydrogen_5eq CASSCF(2,2) aug-cc-pVQZ

0 1
H    0.000000   0.000000  -1.850000
H    0.000000   0.000000   1.850000

CALC_000116.wfx

