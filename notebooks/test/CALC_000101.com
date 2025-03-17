%chk=CALC_000101.chk
%mem=4GB
%NProcShared=1
#P SP CISD/aug-cc-pVQZ gfinput fchk=all density=rhoci iop(9/40=7) iop(9/28=-1) use=l916 out=wfx

CALC_000101 hydrogen_2eq CISD aug-cc-pVQZ

0 1
H    0.000000   0.000000  -0.750000
H    0.000000   0.000000   0.750000

CALC_000101.wfx

