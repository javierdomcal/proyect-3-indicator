%chk=CALC_000107.chk
%mem=4GB
%NProcShared=1
#P SP CISD/cc-pVQZ gfinput fchk=all density=rhoci iop(9/40=7) iop(9/28=-1) use=l916 out=wfx

CALC_000107 hydrogen_5eq CISD cc-pVQZ

0 1
H    0.000000   0.000000  -1.850000
H    0.000000   0.000000   1.850000

CALC_000107.wfx

