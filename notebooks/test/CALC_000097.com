%chk=CALC_000097.chk
%mem=4GB
%NProcShared=1
#P SP CISD/aug-cc-pVTZ gfinput fchk=all density=rhoci iop(9/40=7) iop(9/28=-1) use=l916 out=wfx

CALC_000097 hydrogen_2eq CISD aug-cc-pVTZ

0 1
H    0.000000   0.000000  -0.750000
H    0.000000   0.000000   0.750000

CALC_000097.wfx

