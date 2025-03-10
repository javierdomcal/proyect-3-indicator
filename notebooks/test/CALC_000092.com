%chk=CALC_000092.chk
%mem=4GB
%NProcShared=1
#P SP CASSCF(2,2)/cc-pVQZ gfinput fchk=all density=current iop(5/33=1) out=wfx

CALC_000092 hydrogen_5eq CASSCF(2,2) cc-pVQZ

0 1
H    0.000000   0.000000  -1.850000
H    0.000000   0.000000   1.850000

CALC_000092.wfx

